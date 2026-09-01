"""use decimal quantities for manufacture inventory

Revision ID: 8f2c1a9d4e7b
Revises: 3efd0c13c529
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8f2c1a9d4e7b"
down_revision: Union[str, Sequence[str], None] = "3efd0c13c529"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "manufacture_inventory",
        "quantity",
        existing_type=sa.Integer(),
        type_=sa.Numeric(14, 3),
        existing_nullable=False,
        existing_server_default=sa.text("0"),
    )
    op.alter_column(
        "manufacture_inventory_transactions",
        "quantity",
        existing_type=sa.Integer(),
        type_=sa.Numeric(14, 3),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "manufacture_inventory_transactions",
        "quantity",
        existing_type=sa.Numeric(14, 3),
        type_=sa.Integer(),
        existing_nullable=False,
    )
    op.alter_column(
        "manufacture_inventory",
        "quantity",
        existing_type=sa.Numeric(14, 3),
        type_=sa.Integer(),
        existing_nullable=False,
        existing_server_default=sa.text("0"),
    )
