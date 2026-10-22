import logging
from datetime import date
from pathlib import PurePath

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import create_token, current_user, password_hash, settings
from app.database import get_db
from app.errors import AppError
from app.models import Business, Dataset, User
from app.schemas import BusinessInput, BusinessRead, DatasetRead, Login, MappingInput, Token, UserCreate, UserRead
from app.services.analytics import analytics, filter_options
from app.services.importer import import_rows, preview, validate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")


def owned_business(db: Session, user: User, business_id: int) -> Business:
    business = db.get(Business, business_id)
    if not business or business.owner_id != user.id:
        raise AppError("BUSINESS_NOT_FOUND", "Business workspace not found.", 404)
    return business


def owned_dataset(db: Session, user: User, dataset_id: int) -> Dataset:
    dataset = db.get(Dataset, dataset_id)
    if not dataset:
        raise AppError("DATASET_NOT_FOUND", "Dataset not found.", 404)
    owned_business(db, user, dataset.business_id)
    return dataset


@router.post("/auth/register", response_model=Token, status_code=201)
def register(body: UserCreate, db: Session = Depends(get_db)):
    email = body.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise AppError("EMAIL_ALREADY_REGISTERED", "An account with this email already exists.", 409)
    user = User(name=body.name.strip(), email=email, password_hash=password_hash.hash(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"access_token": create_token(user.id), "user": user}


@router.post("/auth/login", response_model=Token)
def login(body: Login, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if not user or not password_hash.verify(body.password, user.password_hash):
        raise AppError("INVALID_CREDENTIALS", "Email or password is incorrect.", 401)
    return {"access_token": create_token(user.id), "user": user}


@router.get("/auth/me", response_model=UserRead)
def me(user: User = Depends(current_user)):
    return user


@router.get("/businesses", response_model=list[BusinessRead])
def businesses(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return db.scalars(select(Business).where(Business.owner_id == user.id).order_by(Business.created_at.desc())).all()


@router.post("/businesses", response_model=BusinessRead, status_code=201)
def create_business(body: BusinessInput, user: User = Depends(current_user), db: Session = Depends(get_db)):
    business = Business(owner_id=user.id, name=body.name.strip())
    db.add(business)
    db.commit()
    db.refresh(business)
    return business


@router.get("/businesses/{business_id}", response_model=BusinessRead)
def get_business(business_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return owned_business(db, user, business_id)


@router.patch("/businesses/{business_id}", response_model=BusinessRead)
def update_business(
    business_id: int, body: BusinessInput, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    business = owned_business(db, user, business_id)
    business.name = body.name.strip()
    db.commit()
    db.refresh(business)
    return business


@router.get("/businesses/{business_id}/datasets", response_model=list[DatasetRead])
def datasets(business_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    owned_business(db, user, business_id)
    return db.scalars(
        select(Dataset).where(Dataset.business_id == business_id).order_by(Dataset.uploaded_at.desc())
    ).all()


@router.post("/businesses/{business_id}/datasets/upload", response_model=DatasetRead, status_code=201)
async def upload(
    business_id: int, file: UploadFile = File(...), user: User = Depends(current_user), db: Session = Depends(get_db)
):
    owned_business(db, user, business_id)
    filename = PurePath((file.filename or "").replace("\\", "/")).name[:255]
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension not in {"csv", "xlsx"}:
        raise AppError("UNSUPPORTED_FILE", "Upload a CSV or XLSX file.", 415)
    content = await file.read(settings.max_upload_mb * 1024 * 1024 + 1)
    if not content:
        raise AppError("INVALID_DATASET", "The file is empty.")
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise AppError("FILE_TOO_LARGE", f"File exceeds the {settings.max_upload_mb} MB limit.", 413)
    dataset = Dataset(business_id=business_id, original_filename=filename, file_type=extension, file_data=content)
    result = preview(dataset)
    dataset.record_count = result["total_rows"]
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    logger.info("Dataset uploaded: id=%s business=%s rows=%s", dataset.id, business_id, dataset.record_count)
    return dataset


@router.get("/datasets/{dataset_id}", response_model=DatasetRead)
def get_dataset(dataset_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return owned_dataset(db, user, dataset_id)


@router.get("/datasets/{dataset_id}/preview")
def get_preview(dataset_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return preview(owned_dataset(db, user, dataset_id))


@router.post("/datasets/{dataset_id}/validate")
def validate_dataset(
    dataset_id: int, body: MappingInput, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    dataset = owned_dataset(db, user, dataset_id)
    rows, errors, error_count = validate(dataset, body.mapping)
    return {"valid": not errors, "total_rows": len(rows), "error_count": error_count, "errors": errors}


@router.post("/datasets/{dataset_id}/import", response_model=DatasetRead)
def import_dataset(
    dataset_id: int, body: MappingInput, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    dataset = owned_dataset(db, user, dataset_id)
    if dataset.import_status == "imported":
        raise AppError("ALREADY_IMPORTED", "This dataset has already been imported.", 409)
    rows, errors, error_count = validate(dataset, body.mapping)
    if errors:
        raise AppError("VALIDATION_FAILED", f"{error_count} issues need attention.", 422, errors)
    try:
        import_rows(db, dataset, rows)
    except Exception:
        db.rollback()
        logger.exception("Dataset import failed: id=%s", dataset.id)
        raise AppError("IMPORT_FAILED", "The import could not be completed.", 500) from None
    logger.info("Dataset imported: id=%s rows=%s", dataset.id, len(rows))
    return dataset


@router.delete("/datasets/{dataset_id}", status_code=204)
def delete_dataset(dataset_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    dataset = owned_dataset(db, user, dataset_id)
    db.delete(dataset)
    db.commit()


def analytics_args(
    start_date: date | None = None,
    end_date: date | None = None,
    product: str | None = None,
    category: str | None = None,
    customer: str | None = None,
):
    if start_date and end_date and start_date > end_date:
        raise AppError("INVALID_FILTER", "Start date must be before end date.")
    return {
        "start_date": start_date,
        "end_date": end_date,
        "product": product,
        "category": category,
        "customer": customer,
    }


@router.get("/businesses/{business_id}/analytics/options")
def options(business_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    owned_business(db, user, business_id)
    return filter_options(db, business_id)


@router.get("/businesses/{business_id}/analytics/{section}")
def get_analytics(
    section: str,
    business_id: int,
    filters: dict = Depends(analytics_args),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    owned_business(db, user, business_id)
    if section not in {"overview", "sales", "products", "customers"}:
        raise AppError("SECTION_NOT_FOUND", "Analytics section not found.", 404)
    return analytics(db, business_id, **filters)
