from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ManufactureInvoice(Base):
    __tablename__ = "manufacture_invoices"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    invoice_number: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("manufacture_customers.id"),
        nullable=False,
    )

    invoice_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    deduct_from_inventory: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

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

    customer: Mapped["ManufactureCustomer"] = relationship(
        back_populates="invoices",
    )

    items: Mapped[list["ManufactureInvoiceItem"]] = relationship(
        back_populates="invoice",
        cascade="all, delete-orphan",
    )
