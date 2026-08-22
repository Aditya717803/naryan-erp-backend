from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductResponse
from app.routes.auth import get_current_user
from app.models.user import User


router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
):
    # 1. Check whether SKU already exists
    existing_product = db.scalar(
        select(Product).where(
            Product.product_code == product_data.product_code.strip().upper()
        )
    )

    if existing_product:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product code already exists",
        )

    # 2. Create product
    product = Product(
        product_code=product_data.product_code.strip().upper(),
        name=product_data.name.strip(),
        hsn_sac=(
            product_data.hsn_sac.strip()
            if product_data.hsn_sac
            else None
        ),
        unit=product_data.unit.strip(),
    )

    # 3. Save
    db.add(product)
    db.commit()
    db.refresh(product)

    return product


@router.get(
    "/",
    response_model=list[ProductResponse],
)
def get_products(
    search: str | None = None,
    db: Session = Depends(get_db),
):
    query = select(Product).order_by(Product.id.desc())

    if search:
        search_term = f"%{search.strip()}%"

        query = query.where(
            Product.name.ilike(search_term)
            | Product.product_code.ilike(search_term)
            | Product.hsn_sac.ilike(search_term)
        )

    products = db.scalars(query).all()

    return products


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    product = db.get(Product, product_id)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return product