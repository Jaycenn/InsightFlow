from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Index, LargeBinary, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def now() -> datetime:
    return datetime.now(UTC)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
    businesses: Mapped[list["Business"]] = relationship(back_populates="owner", cascade="all, delete-orphan")


class Business(Base):
    __tablename__ = "businesses"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
    owner: Mapped[User] = relationship(back_populates="businesses")
    datasets: Mapped[list["Dataset"]] = relationship(back_populates="business", cascade="all, delete-orphan")
    products: Mapped[list["Product"]] = relationship(cascade="all, delete-orphan")
    customers: Mapped[list["Customer"]] = relationship(cascade="all, delete-orphan")


class Dataset(Base):
    __tablename__ = "datasets"
    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), index=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    file_type: Mapped[str] = mapped_column(String(8))
    file_data: Mapped[bytes] = mapped_column(LargeBinary)
    record_count: Mapped[int] = mapped_column(default=0)
    import_status: Mapped[str] = mapped_column(String(20), default="uploaded")
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    business: Mapped[Business] = relationship(back_populates="datasets")
    sales: Mapped[list["Sale"]] = relationship(back_populates="dataset", cascade="all, delete-orphan")


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (UniqueConstraint("business_id", "name", "category"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(180))
    category: Mapped[str] = mapped_column(String(120), default="Uncategorized")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = (UniqueConstraint("business_id", "name"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(180))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Sale(Base):
    __tablename__ = "sales"
    __table_args__ = (
        Index("ix_sales_business_date", "business_id", "sale_date"),
        Index("ix_sales_business_product", "business_id", "product_id"),
        Index("ix_sales_business_customer", "business_id", "customer_id"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), index=True)
    external_order_id: Mapped[str] = mapped_column(String(120))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"))
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id", ondelete="RESTRICT"))
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    cost: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    sale_date: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    dataset: Mapped[Dataset] = relationship(back_populates="sales")
    product: Mapped[Product] = relationship()
    customer: Mapped[Customer | None] = relationship()
