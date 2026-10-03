from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.customer import Customer
from app.models.state import State
from app.schemas.customer import CustomerCreate, CustomerResponse, CustomerUpdate
from app.models.invoice import Invoice
from app.schemas.invoice import InvoiceResponse
from app.routes.auth import get_current_user



router = APIRouter(
    prefix="/customers",
    tags=["Customers"],
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
        select(State).where(State.id == customer_data.state_id)
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
            select(Customer).where(
                Customer.gstin_uin == gstin
            )
        )

        if existing_customer:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A customer with this GSTIN already exists",
            )


    # 3. Generate customer code
    last_customer = db.scalar(
        select(Customer)
        .order_by(Customer.id.desc())
        .limit(1)
    )

    if last_customer:
        next_number = last_customer.id + 1
    else:
        next_number = 1

    customer_code = f"CUS-{next_number:06d}"

    # 4. Create customer
    customer = Customer(
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

    
    # 5. Add to database
    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer


@router.put(
    "/{customer_id}",
    response_model=CustomerResponse,
)
def update_customer(
    customer_id: int,
    customer_data: CustomerUpdate,
    db: Session = Depends(get_db),
):
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    state = db.get(State, customer_data.state_id)
    if state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Selected state does not exist",
        )

    gstin = customer_data.gstin_uin.strip().upper() if customer_data.gstin_uin else None
    if gstin:
        if len(gstin) != 15:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GSTIN must contain exactly 15 characters",
            )
        if gstin[:2] != state.code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"GSTIN state code {gstin[:2]} does not match "
                    f"selected state code {state.code}"
                ),
            )
        duplicate = db.scalar(
            select(Customer).where(
                Customer.gstin_uin == gstin,
                Customer.id != customer_id,
            )
        )
        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A customer with this GSTIN already exists",
            )

    customer.name = customer_data.name.strip()
    customer.gstin_uin = gstin
    customer.contact_person = (
        customer_data.contact_person.strip()
        if customer_data.contact_person
        else None
    )
    customer.address = customer_data.address.strip()
    customer.state_id = customer_data.state_id

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
    print("🔥 GET_CUSTOMERS ENDPOINT REACHED")
    query = select(Customer).order_by(Customer.id.desc())

    if search:
        search_term = f"%{search.strip()}%"

        query = query.where(
            Customer.name.ilike(search_term)
            | Customer.customer_code.ilike(search_term)
            | Customer.gstin_uin.ilike(search_term)
        )

    customers = db.scalars(query).all()

    return customers

@router.get(
    "/{customer_id}/invoices",
    response_model=list[InvoiceResponse],
)
def get_customer_invoices(
    customer_id: int,
    db: Session = Depends(get_db),
):
    # 1. Check customer exists
    customer = db.get(Customer, customer_id)

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    # 2. Get customer's invoices
    query = (
        select(Invoice)
        .where(Invoice.customer_id == customer_id)
        .order_by(Invoice.invoice_date.desc(), Invoice.id.desc())
    )

    invoices = db.scalars(query).all()

    return invoices

@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
):
    customer = db.get(Customer, customer_id)

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    return customer