from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.product import Product
from app.schemas.invoice import InvoiceCreate, InvoiceResponse
from app.routes.auth import get_current_user
from app.models.invoice_number_counter import InvoiceNumberCounter
from app.models.inventory import Inventory
from app.models.inventory_transaction import InventoryTransaction


router = APIRouter(
    prefix="/invoices",
    tags=["Invoices"],
    dependencies=[Depends(get_current_user)],
)


TWO_PLACES = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return value.quantize(
        TWO_PLACES,
        rounding=ROUND_HALF_UP,
    )


@router.post(
    "/",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_invoice(
    invoice_data: InvoiceCreate,
    db: Session = Depends(get_db),
):
    # --------------------------------------------------
    # 1. Check customer
    # --------------------------------------------------

    customer = db.get(Customer, invoice_data.customer_id)

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    # --------------------------------------------------
    # 2. Validate products and inventory BEFORE
    #    creating the invoice
    # --------------------------------------------------

    products = {}

    for item_data in invoice_data.items:

        product = db.get(
            Product,
            item_data.product_id,
        )

        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"Product {item_data.product_id} not found"
                ),
            )

        products[item_data.product_id] = product

        # Lock inventory row
        inventory = db.scalar(
            select(Inventory)
            .where(
                Inventory.product_id
                == item_data.product_id
            )
            .with_for_update()
        )

        if inventory is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"Inventory not found for "
                    f"product {product.name}"
                ),
            )

        # Check available stock
        if inventory.quantity < item_data.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Insufficient stock for "
                    f"{product.name}. "
                    f"Available: {inventory.quantity}, "
                    f"Requested: {item_data.quantity}"
                ),
            )

    # --------------------------------------------------
    # 3. Get and lock invoice number counter
    # --------------------------------------------------

    counter = db.scalar(
        select(InvoiceNumberCounter)
        .where(
            InvoiceNumberCounter.id == 1
        )
        .with_for_update()
    )

    if counter is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invoice number counter is not initialized",
        )

    invoice_number = (
        f"INV-{counter.next_number:06d}"
    )

    counter.next_number += 1

    # --------------------------------------------------
    # 4. Create invoice
    # --------------------------------------------------

    invoice = Invoice(
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

        dispatch_document_number=(
            invoice_data.dispatch_document_number
        ),
        delivery_note_date=(
            invoice_data.delivery_note_date
        ),

        dispatched_through=(
            invoice_data.dispatched_through
        ),
        destination=invoice_data.destination,
        lr_rr_number=invoice_data.lr_rr_number,
        vehicle_number=invoice_data.vehicle_number,
        terms_of_delivery=(
            invoice_data.terms_of_delivery
        ),

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

    # --------------------------------------------------
    # 5. Create invoice items + deduct inventory
    # --------------------------------------------------

    for item_data in invoice_data.items:

        product = products[item_data.product_id]

        amount = money(
            item_data.quantity * item_data.rate
        )

        cgst_rate = Decimal("0")
        sgst_rate = Decimal("0")
        cgst_amount = Decimal("0")
        sgst_amount = Decimal("0")

        if item_data.gst_rate is not None:

            cgst_rate = (
                item_data.gst_rate
                / Decimal("2")
            )

            sgst_rate = (
                item_data.gst_rate
                / Decimal("2")
            )

            cgst_amount = money(
                amount
                * cgst_rate
                / Decimal("100")
            )

            sgst_amount = money(
                amount
                * sgst_rate
                / Decimal("100")
            )

        invoice_item = InvoiceItem(
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
                cgst_rate
                if item_data.gst_rate is not None
                else None
            ),
            cgst_amount=cgst_amount,

            sgst_rate=(
                sgst_rate
                if item_data.gst_rate is not None
                else None
            ),
            sgst_amount=sgst_amount,

            igst_rate=None,
            igst_amount=Decimal("0"),
        )

        db.add(invoice_item)

        # ----------------------------------------------
        # Deduct stock
        # ----------------------------------------------

        inventory = db.scalar(
            select(Inventory)
            .where(
                Inventory.product_id
                == product.id
            )
            .with_for_update()
        )

        inventory.quantity -= item_data.quantity

        # ----------------------------------------------
        # Record inventory transaction
        # ----------------------------------------------

        transaction = InventoryTransaction(
            product_id=product.id,
            transaction_type="SALE",
            quantity=-item_data.quantity,
            note=(
                f"Invoice {invoice_number}"
            ),
        )

        db.add(transaction)

        subtotal += amount
        total_cgst += cgst_amount
        total_sgst += sgst_amount

    # --------------------------------------------------
    # 6. Calculate totals
    # --------------------------------------------------

    subtotal = money(subtotal)
    total_cgst = money(total_cgst)
    total_sgst = money(total_sgst)

    total_before_rounding = (
        subtotal
        + total_cgst
        + total_sgst
    )

    grand_total = total_before_rounding.quantize(
        TWO_PLACES,
        rounding=ROUND_HALF_UP,
    )

    round_off = money(
        grand_total
        - total_before_rounding
    )

    invoice.subtotal = subtotal
    invoice.cgst_amount = total_cgst
    invoice.sgst_amount = total_sgst
    invoice.grand_total = grand_total
    invoice.round_off = round_off

    # --------------------------------------------------
    # 7. Commit invoice + stock + transactions
    # --------------------------------------------------

    db.commit()

    db.refresh(invoice)

    return invoice

@router.get(
    "/",
    response_model=list[InvoiceResponse],
)
def get_invoices(
    search: str | None = None,
    db: Session = Depends(get_db),
):
    query = select(Invoice).order_by(Invoice.id.desc())

    if search:
        search_term = f"%{search.strip()}%"

        query = query.where(
            Invoice.invoice_number.ilike(search_term)
        )

    invoices = db.scalars(query).all()

    return invoices


#=================================================================================
# Get Invoice Number
#===============================================================================

@router.get(
    "/next-number",
)
def get_next_invoice_number(
    db: Session = Depends(get_db),
):
    counter = db.scalar(
        select(InvoiceNumberCounter)
        .where(InvoiceNumberCounter.id == 1)
    )

    if counter is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invoice number counter is not initialized",
        )

    return {
        "invoice_number": f"INV-{counter.next_number:06d}"
    }





@router.get(
    "/{invoice_id}",
    response_model=InvoiceResponse,
)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
):
    invoice = db.get(Invoice, invoice_id)

    if invoice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )

    return invoice


