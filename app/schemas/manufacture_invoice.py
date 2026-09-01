from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class ManufactureInvoiceItemCreate(BaseModel):
    product_id: int
    quantity: Decimal = Field(gt=0)
    rate: Decimal = Field(gt=0)
    gst_rate: Decimal | None = Field(default=None, ge=0, le=100)


class ManufactureInvoiceCreate(BaseModel):
    customer_id: int
    invoice_date: date

    eway_bill_number: str | None = None
    delivery_note: str | None = None
    payment_terms: str | None = None
    supplier_reference: str | None = None
    other_references: str | None = None

    buyer_order_number: str | None = None
    buyer_order_date: date | None = None

    dispatch_document_number: str | None = None
    delivery_note_date: date | None = None

    dispatched_through: str | None = None
    destination: str | None = None
    lr_rr_number: str | None = None
    vehicle_number: str | None = None
    terms_of_delivery: str | None = None

    items: list[ManufactureInvoiceItemCreate] = Field(min_length=1)


class ManufactureInvoiceItemResponse(BaseModel):
    id: int
    product_id: int

    description: str
    hsn_sac: str | None
    quantity: Decimal
    unit: str
    rate: Decimal
    amount: Decimal

    gst_rate: Decimal | None
    cgst_rate: Decimal | None
    cgst_amount: Decimal
    sgst_rate: Decimal | None
    sgst_amount: Decimal
    igst_rate: Decimal | None
    igst_amount: Decimal

    model_config = {"from_attributes": True}


class ManufactureInvoiceResponse(BaseModel):
    id: int
    invoice_number: str
    customer_id: int
    invoice_date: date

    eway_bill_number: str | None
    delivery_note: str | None
    payment_terms: str | None
    supplier_reference: str | None
    other_references: str | None

    buyer_order_number: str | None
    buyer_order_date: date | None
    dispatch_document_number: str | None
    delivery_note_date: date | None

    dispatched_through: str | None
    destination: str | None
    lr_rr_number: str | None
    vehicle_number: str | None
    terms_of_delivery: str | None

    subtotal: Decimal
    cgst_rate: Decimal | None
    cgst_amount: Decimal
    sgst_rate: Decimal | None
    sgst_amount: Decimal
    igst_rate: Decimal | None
    igst_amount: Decimal
    round_off: Decimal
    grand_total: Decimal

    items: list[ManufactureInvoiceItemResponse]

    model_config = {"from_attributes": True}


InvoiceItemCreate = ManufactureInvoiceItemCreate
InvoiceCreate = ManufactureInvoiceCreate
InvoiceItemResponse = ManufactureInvoiceItemResponse
InvoiceResponse = ManufactureInvoiceResponse
