"""add invoice number counter

Revision ID: e4375a9d41f0
Revises: 1dd08041e9c7
Create Date: 2026-08-26 17:58:53.448908

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e4375a9d41f0"
down_revision: Union[str, Sequence[str], None] = "1dd08041e9c7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "invoice_number_counters",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "next_number",
            sa.Integer(),
            server_default=sa.text("1"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("invoice_number_counters")