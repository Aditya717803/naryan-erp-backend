"""create manufacture tables

Revision ID: b4f4d0f9a5d1
Revises: 25d0fe1311a1
Create Date: 2026-08-30 18:54:26.998000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b4f4d0f9a5d1"
down_revision: Union[str, Sequence[str], None] = "25d0fe1311a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "manufacture_customers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("customer_code", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("gstin_uin", sa.String(length=20), nullable=True),
        sa.Column("contact_person", sa.String(length=150), nullable=True),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("state_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["state_id"], ["states.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("customer_code"),
        sa.UniqueConstraint("gstin_uin"),
    )

    op.create_table(
        "manufacture_products",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("product_code", sa.String(length=30), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("hsn_sac", sa.String(length=20), nullable=True),
        sa.Column("unit", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_code"),
    )

    op.create_table(
        "manufacture_invoices",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("invoice_number", sa.String(length=30), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("invoice_date", sa.Date(), nullable=False),
        sa.Column("eway_bill_number", sa.String(length=50), nullable=True),
        sa.Column("delivery_note", sa.String(length=100), nullable=True),
        sa.Column("payment_terms", sa.String(length=200), nullable=True),
        sa.Column("supplier_reference", sa.String(length=200), nullable=True),
        sa.Column("other_references", sa.String(length=200), nullable=True),
        sa.Column("buyer_order_number", sa.String(length=100), nullable=True),
        sa.Column("buyer_order_date", sa.Date(), nullable=True),
        sa.Column("dispatch_document_number", sa.String(length=100), nullable=True),
        sa.Column("delivery_note_date", sa.Date(), nullable=True),
        sa.Column("dispatched_through", sa.String(length=150), nullable=True),
        sa.Column("destination", sa.String(length=200), nullable=True),
        sa.Column("lr_rr_number", sa.String(length=100), nullable=True),
        sa.Column("vehicle_number", sa.String(length=50), nullable=True),
        sa.Column("terms_of_delivery", sa.String(length=500), nullable=True),
        sa.Column("subtotal", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("cgst_rate", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("cgst_amount", sa.Numeric(precision=14, scale=2), nullable=False, server_default="0"),
        sa.Column("sgst_rate", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("sgst_amount", sa.Numeric(precision=14, scale=2), nullable=False, server_default="0"),
        sa.Column("igst_rate", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("igst_amount", sa.Numeric(precision=14, scale=2), nullable=False, server_default="0"),
        sa.Column("round_off", sa.Numeric(precision=10, scale=2), nullable=False, server_default="0"),
        sa.Column("grand_total", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["manufacture_customers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("invoice_number"),
    )

    op.create_table(
        "manufacture_invoice_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("invoice_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column("hsn_sac", sa.String(length=20), nullable=True),
        sa.Column("quantity", sa.Numeric(precision=14, scale=3), nullable=False),
        sa.Column("unit", sa.String(length=30), nullable=False),
        sa.Column("rate", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("gst_rate", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("cgst_rate", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("cgst_amount", sa.Numeric(precision=14, scale=2), nullable=False, server_default="0"),
        sa.Column("sgst_rate", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("sgst_amount", sa.Numeric(precision=14, scale=2), nullable=False, server_default="0"),
        sa.Column("igst_rate", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("igst_amount", sa.Numeric(precision=14, scale=2), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["invoice_id"], ["manufacture_invoices.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["manufacture_products.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "manufacture_inventory",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["manufacture_products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_id"),
    )

    op.create_table(
        "manufacture_inventory_transactions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("transaction_type", sa.String(length=30), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["manufacture_products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("manufacture_invoice_items")
    op.drop_table("manufacture_inventory_transactions")
    op.drop_table("manufacture_invoices")
    op.drop_table("manufacture_inventory")
    op.drop_table("manufacture_products")
    op.drop_table("manufacture_customers")
