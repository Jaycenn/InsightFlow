import io
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import AppError
from app.models import Customer, Dataset, Product, Sale

FIELDS = ("order_id", "date", "product", "category", "quantity", "unit_price", "cost", "customer")
REQUIRED = ("order_id", "date", "product", "quantity", "unit_price")
ALIASES = {
    "order_id": ("order id", "order", "transaction number", "transaction id", "invoice"),
    "date": ("date", "purchase date", "sale date", "order date"),
    "product": ("product", "item", "item name", "product name"),
    "category": ("category", "product category"),
    "quantity": ("quantity", "qty", "units"),
    "unit_price": ("unit price", "unit_price", "selling price", "price"),
    "cost": ("cost", "unit cost"),
    "customer": ("customer", "buyer", "customer name"),
}


def read_frame(dataset: Dataset) -> pd.DataFrame:
    try:
        stream = io.BytesIO(dataset.file_data)
        if dataset.file_type == "csv":
            frame = pd.read_csv(stream, dtype=str, keep_default_na=False, encoding="utf-8-sig", on_bad_lines="error")
        else:
            frame = pd.read_excel(stream, dtype=str, keep_default_na=False, engine="openpyxl")
    except Exception as exc:
        raise AppError("INVALID_DATASET", "The file could not be read as a valid CSV or XLSX file.") from exc
    frame.columns = [str(col).strip() for col in frame.columns]
    frame = frame.fillna("").astype(str)
    frame = frame[~frame.apply(lambda row: all(not str(value).strip() for value in row), axis=1)]
    if frame.empty or not any(frame.columns):
        raise AppError("INVALID_DATASET", "The dataset has no usable rows.")
    if len(frame.columns) != len(set(frame.columns)):
        raise AppError("INVALID_DATASET", "Column names must be unique.")
    return frame


def suggested_mapping(columns: list[str]) -> dict[str, str]:
    lower = {column.lower().replace("_", " ").strip(): column for column in columns}
    return {field: next((lower[name] for name in aliases if name in lower), "") for field, aliases in ALIASES.items()}


def preview(dataset: Dataset) -> dict:
    frame = read_frame(dataset)
    return {
        "columns": list(frame.columns),
        "rows": frame.head(8).to_dict(orient="records"),
        "total_rows": len(frame),
        "suggested_mapping": suggested_mapping(list(frame.columns)),
    }


def _number(value: str, label: str, row: int, errors: list[dict]) -> Decimal | None:
    try:
        number = Decimal(value.strip())
        if not number.is_finite() or number < 0:
            raise InvalidOperation
        return number
    except (InvalidOperation, AttributeError):
        errors.append({"row": row, "field": label, "message": f"{label} must be a valid non-negative number."})
        return None


def validate(dataset: Dataset, mapping: dict[str, str]) -> tuple[list[dict], list[dict], int]:
    frame = read_frame(dataset)
    errors: list[dict] = []
    missing = [field for field in REQUIRED if not mapping.get(field)]
    if missing:
        issues = [{"row": None, "field": field, "message": f"Map a column to {field}."} for field in missing]
        return [], issues, len(issues)
    selected = [source for field, source in mapping.items() if field in FIELDS and source]
    if len(selected) != len(set(selected)) or any(source not in frame.columns for source in selected):
        issues = [{"row": None, "field": "mapping", "message": "Choose distinct columns present in the uploaded file."}]
        return [], issues, len(issues)
    rows = []
    seen = set()
    for source_index, raw in frame.iterrows():
        index = int(source_index) + 2
        row = {field: str(raw.get(mapping.get(field, ""), "")).strip() for field in FIELDS}
        for field in REQUIRED:
            if not row[field]:
                errors.append({"row": index, "field": field, "message": f"{field} is required."})
        try:
            parsed_date = date.fromisoformat(row["date"])
        except ValueError:
            try:
                parsed_date = datetime.fromisoformat(row["date"]).date()
            except ValueError:
                parsed_date = None
                if row["date"]:
                    errors.append({"row": index, "field": "date", "message": "date must use YYYY-MM-DD."})
        quantity = _number(row["quantity"], "quantity", index, errors) if row["quantity"] else None
        price = _number(row["unit_price"], "unit_price", index, errors) if row["unit_price"] else None
        cost = _number(row["cost"], "cost", index, errors) if row["cost"] else None
        if quantity is not None and quantity == 0:
            errors.append({"row": index, "field": "quantity", "message": "quantity must be greater than zero."})
        fingerprint = (row["order_id"], row["date"], row["product"], row["quantity"], row["unit_price"])
        if fingerprint in seen:
            errors.append({"row": index, "field": "order_id", "message": "Duplicate transaction row in this file."})
        seen.add(fingerprint)
        rows.append({**row, "date": parsed_date, "quantity": quantity, "unit_price": price, "cost": cost})
    return rows, errors[:100], len(errors)


def import_rows(db: Session, dataset: Dataset, rows: list[dict]) -> int:
    products = {
        (p.name, p.category): p for p in db.scalars(select(Product).where(Product.business_id == dataset.business_id))
    }
    customers = {c.name: c for c in db.scalars(select(Customer).where(Customer.business_id == dataset.business_id))}
    for row in rows:
        key = (row["product"], row["category"] or "Uncategorized")
        if key not in products:
            products[key] = Product(business_id=dataset.business_id, name=key[0], category=key[1])
            db.add(products[key])
            db.flush()
        customer = None
        if row["customer"]:
            if row["customer"] not in customers:
                customers[row["customer"]] = Customer(business_id=dataset.business_id, name=row["customer"])
                db.add(customers[row["customer"]])
                db.flush()
            customer = customers[row["customer"]]
        db.add(
            Sale(
                business_id=dataset.business_id,
                dataset_id=dataset.id,
                external_order_id=row["order_id"],
                product_id=products[key].id,
                customer_id=customer.id if customer else None,
                quantity=row["quantity"],
                unit_price=row["unit_price"],
                cost=row["cost"],
                sale_date=row["date"],
            )
        )
    dataset.record_count = len(rows)
    dataset.import_status = "imported"
    db.commit()
    return len(rows)
