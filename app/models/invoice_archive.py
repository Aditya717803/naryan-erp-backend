from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class InvoiceArchive(Base):
    __tablename__ = "invoice_archives"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    archived_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    invoice_count: Mapped[int] = mapped_column(Integer, nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    google_drive_file_id: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
