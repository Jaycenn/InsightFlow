"""Initial normalized business and sales schema.

Revision ID: 001_initial
Revises:
"""

import sqlalchemy as sa
from alembic import op

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table(
        "businesses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_businesses_owner_id", "businesses", ["owner_id"])
    op.create_table(
        "datasets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_id", sa.Integer(), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("file_type", sa.String(8), nullable=False),
        sa.Column("file_data", sa.LargeBinary(), nullable=False),
        sa.Column("record_count", sa.Integer(), nullable=False),
        sa.Column("import_status", sa.String(20), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_datasets_business_id", "datasets", ["business_id"])
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_id", sa.Integer(), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("category", sa.String(120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("business_id", "name", "category"),
    )
    op.create_index("ix_products_business_id", "products", ["business_id"])
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_id", sa.Integer(), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("business_id", "name"),
    )
    op.create_index("ix_customers_business_id", "customers", ["business_id"])
    op.create_table(
        "sales",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_id", sa.Integer(), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("dataset_id", sa.Integer(), sa.ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("external_order_id", sa.String(120), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id", ondelete="RESTRICT")),
        sa.Column("quantity", sa.Numeric(14, 3), nullable=False),
        sa.Column("unit_price", sa.Numeric(14, 2), nullable=False),
        sa.Column("cost", sa.Numeric(14, 2)),
        sa.Column("sale_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_sales_dataset_id", "sales", ["dataset_id"])
    op.create_index("ix_sales_business_date", "sales", ["business_id", "sale_date"])
    op.create_index("ix_sales_business_product", "sales", ["business_id", "product_id"])
    op.create_index("ix_sales_business_customer", "sales", ["business_id", "customer_id"])


def downgrade():
    for table in ("sales", "customers", "products", "datasets", "businesses", "users"):
        op.drop_table(table)
