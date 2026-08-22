from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    # Invoice identification
    invoice_number: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"),
        nullable=False,
    )

    invoice_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    # Invoice header information
    eway_bill_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    delivery_note: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    payment_terms: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    supplier_reference: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    other_references: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    buyer_order_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    buyer_order_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    dispatch_document_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    delivery_note_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    dispatched_through: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    destination: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    lr_rr_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    vehicle_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    terms_of_delivery: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # Financial information
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    cgst_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    cgst_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=0,
        nullable=False,
    )

    sgst_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    sgst_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=0,
        nullable=False,
    )

    igst_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    igst_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=0,
        nullable=False,
    )

    round_off: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=0,
        nullable=False,
    )

    grand_total: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Customer relationship
    customer: Mapped["Customer"] = relationship(
        back_populates="invoices",
    )

    items: Mapped[list["InvoiceItem"]] = relationship(
    back_populates="invoice",
    cascade="all, delete-orphan",
)