"""create invoice archives table

Revision ID: 9c6e2b4f1a7d
Revises: be6bcb75db72
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9c6e2b4f1a7d"
down_revision: Union[str, Sequence[str], None] = "be6bcb75db72"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "invoice_archives",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("invoice_count", sa.Integer(), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column(
            "google_drive_file_id", sa.String(length=255), nullable=False
        ),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("invoice_archives")
