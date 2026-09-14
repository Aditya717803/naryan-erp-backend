"""change store inventory quantities to decimal

Revision ID: be6bcb75db72
Revises: 8f2c1a9d4e7b
Create Date: 2026-09-14 15:08:57.760922

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'be6bcb75db72'
down_revision: Union[str, Sequence[str], None] = '8f2c1a9d4e7b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Change store inventory quantity from INTEGER to NUMERIC(14, 3)
    op.alter_column(
        "inventory",
        "quantity",
        existing_type=sa.Integer(),
        type_=sa.Numeric(14, 3),
        existing_nullable=False,
    )

    # Change inventory transaction quantity from INTEGER to NUMERIC(14, 3)
    op.alter_column(
        "inventory_transactions",
        "quantity",
        existing_type=sa.Integer(),
        type_=sa.Numeric(14, 3),
        existing_nullable=False,
    )


def downgrade() -> None:
    """Downgrade schema."""

    # WARNING: converting decimal values back to INTEGER can lose precision.
    op.alter_column(
        "inventory_transactions",
        "quantity",
        existing_type=sa.Numeric(14, 3),
        type_=sa.Integer(),
        existing_nullable=False,
    )

    op.alter_column(
        "inventory",
        "quantity",
        existing_type=sa.Numeric(14, 3),
        type_=sa.Integer(),
        existing_nullable=False,
    )