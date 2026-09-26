import json
import logging
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models.invoice import Invoice
from app.models.invoice_archive import InvoiceArchive
from app.routes.auth import get_current_user
from app.services.google_drive import upload_json_file


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/archive",
    tags=["Archive"],
    dependencies=[Depends(get_current_user)],
)


def json_value(value):
    if isinstance(value, Decimal):
        return str(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def invoice_to_archive(invoice: Invoice) -> dict:
    invoice_fields = (
        "id", "invoice_number", "customer_id", "invoice_date",
        "eway_bill_number", "delivery_note", "payment_terms",
        "supplier_reference", "other_references", "buyer_order_number",
        "buyer_order_date", "dispatch_document_number", "delivery_note_date",
        "dispatched_through", "destination", "lr_rr_number", "vehicle_number",
        "terms_of_delivery", "subtotal", "cgst_rate", "cgst_amount",
        "sgst_rate", "sgst_amount", "igst_rate", "igst_amount", "round_off",
        "grand_total", "created_at", "updated_at",
    )
    item_fields = (
        "id", "invoice_id", "product_id", "description", "hsn_sac",
        "quantity", "unit", "rate", "amount", "gst_rate", "cgst_rate",
        "cgst_amount", "sgst_rate", "sgst_amount", "igst_rate",
        "igst_amount",
    )
    customer_fields = (
        "id", "customer_code", "name", "gstin_uin", "contact_person",
        "address", "state_id", "created_at", "updated_at",
    )

    return {
        **{
            field: json_value(getattr(invoice, field))
            for field in invoice_fields
        },
        "customer": {
            field: json_value(getattr(invoice.customer, field))
            for field in customer_fields
        },
        "items": [
            {
                field: json_value(getattr(item, field))
                for field in item_fields
            }
            for item in invoice.items
        ],
    }


@router.post("/invoices")
def archive_invoices(db: Session = Depends(get_db)):
    archived_at = datetime.now(timezone.utc)
    file_name = (
        f"invoice_archive_{archived_at.strftime('%Y-%m-%d_%H-%M-%S')}.json"
    )

    try:
        invoices = db.scalars(
            select(Invoice)
            .options(
                selectinload(Invoice.customer),
                selectinload(Invoice.items),
            )
            .order_by(Invoice.id)
        ).all()
        payload = {
            "archive_version": 1,
            "archived_at": archived_at.isoformat(),
            "invoice_count": len(invoices),
            "invoices": [
                invoice_to_archive(invoice) for invoice in invoices
            ],
        }
        content = json.dumps(
            payload, ensure_ascii=False, indent=2
        ).encode("utf-8")
    except (SQLAlchemyError, TypeError, ValueError) as error:
        logger.exception("Could not prepare invoice archive")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not prepare invoice archive",
        ) from error

    try:
        google_drive_file_id = upload_json_file(file_name, content)
    except RuntimeError as error:
        logger.error("Invoice archive upload failed: %s", error)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error

    try:
        db.add(
            InvoiceArchive(
                archived_at=archived_at,
                invoice_count=len(invoices),
                file_name=file_name,
                google_drive_file_id=google_drive_file_id,
                status="SUCCESS",
            )
        )
        db.commit()
    except SQLAlchemyError as error:
        db.rollback()
        logger.exception(
            "Google Drive archive uploaded but archive record failed"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Archive uploaded but could not record archive details",
        ) from error

    return {
        "status": "SUCCESS",
        "archived_at": archived_at.isoformat(),
        "invoice_count": len(invoices),
        "file_name": file_name,
        "google_drive_file_id": google_drive_file_id,
    }
