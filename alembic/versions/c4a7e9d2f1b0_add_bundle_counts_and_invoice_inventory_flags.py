"""add independent bundle counts and invoice inventory flags

Revision ID: c4a7e9d2f1b0
Revises: 9c6e2b4f1a7d
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4a7e9d2f1b0"
down_revision: Union[str, Sequence[str], None] = "9c6e2b4f1a7d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "inventory",
        sa.Column("bundle_count", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "manufacture_inventory",
        sa.Column("bundle_count", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "invoices",
        sa.Column(
            "deduct_from_inventory",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )
    op.add_column(
        "manufacture_invoices",
        sa.Column(
            "deduct_from_inventory",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("manufacture_invoices", "deduct_from_inventory")
    op.drop_column("invoices", "deduct_from_inventory")
    op.drop_column("manufacture_inventory", "bundle_count")
    op.drop_column("inventory", "bundle_count")
