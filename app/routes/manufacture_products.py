from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.manufacture_product import ManufactureProduct
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.routes.auth import get_current_user


router = APIRouter(
    prefix="/manufacture/products",
    tags=["Manufacture Products"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "/",
    response_model = ProductResponse,
    status_code = status.HTTP_201_CREATED,

)
def create_product(
    product_data : ProductCreate,
    db: Session = Depends(get_db),
):
    existing_product = db.scalar(
        select(ManufactureProduct).where(
            ManufactureProduct.product_code == product_data.product_code.strip().upper()
        )
    )

    if existing_product:
        raise HTTPException(
            status_code= status.HTTP_409_CONFLICT,
            detail = "Product code already exists"
        )

    product  = ManufactureProduct(
        product_code =  product_data.product_code.strip().upper(),
        name = product_data.name.strip(),
        hsn_sac = (
            product_data.hsn_sac.strip()
            if product_data.hsn_sac
            else None
        ),
        unit = product_data.unit.strip(),
    )


    db.add(product)
    db.commit()
    db.refresh(product)


    return product

@router.get(
    "/",
    response_model = list[ProductResponse],
)

def get_products(
    search : str | None = None,
    db: Session = Depends(get_db),
):
    query = select(ManufactureProduct).order_by(ManufactureProduct.id.desc())

    if search:
        search_term = f"%{search.strip()}%"

        query = query.where(
            ManufactureProduct.name.ilike(search_term)
            | ManufactureProduct.product_code.ilike(search_term)
            | ManufactureProduct.hsn_sac.ilike(search_term)

        )

    products = db.scalars(query).all()

    return products


@router.get(
    "/{product_id}",
    response_model = ProductResponse,
)

def get_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    product = db.get(ManufactureProduct , product_id)

    if product is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Product not found"
        )

    return product


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
)
def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
):
    product = db.get(ManufactureProduct, product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    product.name = product_data.name.strip()
    product.hsn_sac = (
        product_data.hsn_sac.strip()
        if product_data.hsn_sac
        else None
    )
    product.unit = product_data.unit.strip()

    db.commit()
    db.refresh(product)
    return product
