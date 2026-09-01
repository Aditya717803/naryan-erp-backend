from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.manufacture_customer import ManufactureCustomer
from app.models.state import State
from app.models.manufacture_invoice import ManufactureInvoice
from app.schemas.customer import CustomerCreate, CustomerResponse
from app.schemas.manufacture_invoice import ManufactureInvoiceResponse
from app.routes.auth import get_current_user


router = APIRouter(
    prefix="/manufacture/customers",
    tags=["Manufacture Customers"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "/",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_customer(
    customer_data: CustomerCreate,
    db: Session = Depends(get_db),
):
    # 1. Check that the selected state exists
    state = db.scalar(
        select(State).where(
            State.id == customer_data.state_id
        )
    )

    if state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Selected state does not exist",
        )

    # 2. Validate GSTIN state code
    if customer_data.gstin_uin:
        gstin = customer_data.gstin_uin.strip().upper()

        if len(gstin) != 15:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GSTIN must contain exactly 15 characters",
            )

        gst_state_code = gstin[:2]

        if gst_state_code != state.code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"GSTIN state code {gst_state_code} does not match "
                    f"selected state code {state.code}"
                ),
            )

        # 3. Check duplicate GSTIN
        existing_customer = db.scalar(
            select(ManufactureCustomer).where(
                ManufactureCustomer.gstin_uin == gstin
            )
        )

        if existing_customer:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A customer with this GSTIN already exists",
            )

    # 4. Generate customer code
    last_customer = db.scalar(
        select(ManufactureCustomer)
        .order_by(ManufactureCustomer.id.desc())
        .limit(1)
    )

    if last_customer:
        next_number = last_customer.id + 1
    else:
        next_number = 1

    customer_code = f"MCUS-{next_number:06d}"

    # 5. Create customer
    customer = ManufactureCustomer(
        customer_code=customer_code,
        name=customer_data.name.strip(),
        gstin_uin=(
            customer_data.gstin_uin.strip().upper()
            if customer_data.gstin_uin
            else None
        ),
        contact_person=(
            customer_data.contact_person.strip()
            if customer_data.contact_person
            else None
        ),
        address=customer_data.address.strip(),
        state_id=customer_data.state_id,
    )

    # 6. Add to database
    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer


@router.get(
    "/",
    response_model=list[CustomerResponse],
)
def get_customers(
    search: str | None = None,
    db: Session = Depends(get_db),
):
    query = (
        select(ManufactureCustomer)
        .order_by(ManufactureCustomer.id.desc())
    )

    if search:
        search_term = f"%{search.strip()}%"

        query = query.where(
            ManufactureCustomer.name.ilike(search_term)
            | ManufactureCustomer.customer_code.ilike(
                search_term
            )
            | ManufactureCustomer.gstin_uin.ilike(
                search_term
            )
        )

    customers = db.scalars(query).all()

    return customers


@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
):
    customer = db.get(
        ManufactureCustomer,
        customer_id,
    )

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    return customer


@router.get(
    "/{customer_id}/invoices",
    response_model=list[ManufactureInvoiceResponse],
)
def get_customer_invoices(
    customer_id: int,
    db: Session = Depends(get_db),
):
    # 1. Check customer exists
    customer = db.get(
        ManufactureCustomer,
        customer_id,
    )

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    # 2. Get customer's invoices
    query = (
        select(ManufactureInvoice)
        .where(
            ManufactureInvoice.customer_id == customer_id
        )
        .order_by(
            ManufactureInvoice.invoice_date.desc(),
            ManufactureInvoice.id.desc(),
        )
    )

    invoices = db.scalars(query).all()

    return invoices