from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: EmailStr


class Login(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class BusinessInput(BaseModel):
    name: str = Field(min_length=2, max_length=120)


class BusinessRead(BusinessInput):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class DatasetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    business_id: int
    original_filename: str
    file_type: str
    record_count: int
    import_status: str
    uploaded_at: datetime


class MappingInput(BaseModel):
    mapping: dict[str, str]


class AnalyticsFilters(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    product: str | None = None
    category: str | None = None
    customer: str | None = None
