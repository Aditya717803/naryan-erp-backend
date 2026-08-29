"""initialize invoice number counter

Revision ID: 25d0fe1311a1
Revises: e4375a9d41f0
Create Date: 2026-08-26 18:51:13.596719

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "25d0fe1311a1"
down_revision: Union[str, Sequence[str], None] = "e4375a9d41f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO invoice_number_counters (id, next_number)
        VALUES (1, 1)
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM invoice_number_counters
        WHERE id = 1
        """
    )