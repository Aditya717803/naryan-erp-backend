"""create expenses table

Revision ID: d29c7416e5ab
Revises: c4a7e9d2f1b0
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d29c7416e5ab"
down_revision: Union[str, Sequence[str], None] = "c4a7e9d2f1b0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "expenses",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("expenses")
