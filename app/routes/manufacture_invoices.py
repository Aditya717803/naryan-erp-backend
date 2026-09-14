from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.manufacture_customer import ManufactureCustomer
from app.models.manufacture_invoice import ManufactureInvoice
from app.models.manufacture_invoice_item import ManufactureInvoiceItem
from app.models.manufacture_invoice_number_counter import (
    ManufactureInvoiceNumberCounter,
)
from app.models.manufacture_inventory import ManufactureInventory
from app.models.manufacture_inventory_transaction import (
    ManufactureInventoryTransaction,
)
from app.models.manufacture_product import ManufactureProduct
from app.routes.auth import get_current_user
from app.schemas.manufacture_invoice import (
    ManufactureInvoiceCreate,
    ManufactureInvoiceResponse,
)


router = APIRouter(
    prefix="/manufacture/invoices",
    tags=["Manufacture Invoices"],
    dependencies=[Depends(get_current_user)],
)

TWO_PLACES = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def validate_quantity_for_unit(
    quantity: Decimal,
    unit: str,
) -> None:
    if unit.strip().lower() == "kg":
        return

    if quantity != quantity.to_integral_value():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Quantity for {unit} must be a whole number. "
                f"Received: {quantity}"
            ),
        )


@router.post(
    "/",
    response_model=ManufactureInvoiceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_invoice(
    invoice_data: ManufactureInvoiceCreate,
    db: Session = Depends(get_db),
):
    try:
        customer = db.get(ManufactureCustomer, invoice_data.customer_id)
        if customer is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found",
            )

        products: dict[int, ManufactureProduct] = {}
        inventories: dict[int, ManufactureInventory] = {}
        requested_quantities: dict[int, Decimal] = {}

        # Lock every inventory row before validating stock. This keeps the
        # validation and subsequent deductions in one transaction.
        for item_data in invoice_data.items:
            product = products.get(item_data.product_id)
            if product is None:
                product = db.get(ManufactureProduct, item_data.product_id)
                if product is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Product {item_data.product_id} not found",
                    )
                products[item_data.product_id] = product

            validate_quantity_for_unit(
                item_data.quantity,
                product.unit,
            )

            requested_quantities[item_data.product_id] = (
                requested_quantities.get(item_data.product_id, Decimal("0"))
                + item_data.quantity
            )

            if item_data.product_id not in inventories:
                inventory = db.scalar(
                    select(ManufactureInventory)
                    .where(
                        ManufactureInventory.product_id == item_data.product_id
                    )
                    .with_for_update()
                )
                if inventory is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=(
                            f"Inventory not found for product "
                            f"{product.name}"
                        ),
                    )
                inventories[item_data.product_id] = inventory

        for product_id, requested in requested_quantities.items():
            inventory = inventories[product_id]
            product = products[product_id]
            if inventory.quantity < requested:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Insufficient stock for {product.name}. "
                        f"Available: {inventory.quantity}, "
                        f"Requested: {requested}"
                    ),
                )

        counter = db.scalar(
            select(ManufactureInvoiceNumberCounter)
            .where(ManufactureInvoiceNumberCounter.id == 1)
            .with_for_update()
        )
        if counter is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    "Manufacture invoice number counter "
                    "is not initialized"
                ),
            )

        invoice_number = f"MINV-{counter.next_number:06d}"
        counter.next_number += 1

        invoice = ManufactureInvoice(
            invoice_number=invoice_number,
            customer_id=invoice_data.customer_id,
            invoice_date=invoice_data.invoice_date,
            eway_bill_number=invoice_data.eway_bill_number,
            delivery_note=invoice_data.delivery_note,
            payment_terms=invoice_data.payment_terms,
            supplier_reference=invoice_data.supplier_reference,
            other_references=invoice_data.other_references,
            buyer_order_number=invoice_data.buyer_order_number,
            buyer_order_date=invoice_data.buyer_order_date,
            dispatch_document_number=invoice_data.dispatch_document_number,
            delivery_note_date=invoice_data.delivery_note_date,
            dispatched_through=invoice_data.dispatched_through,
            destination=invoice_data.destination,
            lr_rr_number=invoice_data.lr_rr_number,
            vehicle_number=invoice_data.vehicle_number,
            terms_of_delivery=invoice_data.terms_of_delivery,
            subtotal=Decimal("0"),
            cgst_amount=Decimal("0"),
            sgst_amount=Decimal("0"),
            igst_amount=Decimal("0"),
            round_off=Decimal("0"),
            grand_total=Decimal("0"),
        )
        db.add(invoice)

        subtotal = Decimal("0")
        total_cgst = Decimal("0")
        total_sgst = Decimal("0")

        for item_data in invoice_data.items:
            product = products[item_data.product_id]
            amount = money(item_data.quantity * item_data.rate)

            cgst_rate = Decimal("0")
            sgst_rate = Decimal("0")
            cgst_amount = Decimal("0")
            sgst_amount = Decimal("0")
            if item_data.gst_rate is not None:
                cgst_rate = item_data.gst_rate / Decimal("2")
                sgst_rate = item_data.gst_rate / Decimal("2")
                cgst_amount = money(
                    amount * cgst_rate / Decimal("100")
                )
                sgst_amount = money(
                    amount * sgst_rate / Decimal("100")
                )

            db.add(
                ManufactureInvoiceItem(
                    invoice=invoice,
                    product_id=product.id,
                    description=product.name,
                    hsn_sac=product.hsn_sac,
                    unit=product.unit,
                    quantity=item_data.quantity,
                    rate=item_data.rate,
                    amount=amount,
                    gst_rate=item_data.gst_rate,
                    cgst_rate=(
                        cgst_rate if item_data.gst_rate is not None else None
                    ),
                    cgst_amount=cgst_amount,
                    sgst_rate=(
                        sgst_rate if item_data.gst_rate is not None else None
                    ),
                    sgst_amount=sgst_amount,
                    igst_rate=None,
                    igst_amount=Decimal("0"),
                )
            )

            inventories[item_data.product_id].quantity -= item_data.quantity
            db.add(
                ManufactureInventoryTransaction(
                    product_id=product.id,
                    transaction_type="SALE",
                    quantity=-item_data.quantity,
                    note=f"Invoice {invoice_number}",
                )
            )

            subtotal += amount
            total_cgst += cgst_amount
            total_sgst += sgst_amount

        subtotal = money(subtotal)
        total_cgst = money(total_cgst)
        total_sgst = money(total_sgst)
        total_before_rounding = subtotal + total_cgst + total_sgst
        grand_total = money(total_before_rounding)
        round_off = money(grand_total - total_before_rounding)

        invoice.subtotal = subtotal
        invoice.cgst_amount = total_cgst
        invoice.sgst_amount = total_sgst
        invoice.grand_total = grand_total
        invoice.round_off = round_off

        db.commit()
        db.refresh(invoice)
        return invoice
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create manufacture invoice",
        )


@router.get(
    "/",
    response_model=list[ManufactureInvoiceResponse],
)
def get_invoices(
    search: str | None = None,
    db: Session = Depends(get_db),
):
    query = select(ManufactureInvoice).order_by(ManufactureInvoice.id.desc())
    if search:
        query = query.where(
            ManufactureInvoice.invoice_number.ilike(f"%{search.strip()}%")
        )
    return db.scalars(query).all()


@router.get("/next-number")
def get_next_invoice_number(db: Session = Depends(get_db)):
    counter = db.scalar(
        select(ManufactureInvoiceNumberCounter).where(
            ManufactureInvoiceNumberCounter.id == 1
        )
    )
    if counter is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Manufacture invoice number counter "
                "is not initialized"
            ),
        )
    return {"invoice_number": f"MINV-{counter.next_number:06d}"}


@router.get(
    "/{invoice_id}",
    response_model=ManufactureInvoiceResponse,
)
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    invoice = db.get(ManufactureInvoice, invoice_id)
    if invoice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )
    return invoice
