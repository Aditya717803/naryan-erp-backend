from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class InvoiceNumberCounter(Base):
    __tablename__ = "invoice_number_counters"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    next_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )