from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.manufacture_inventory import ManufactureInventory
from app.models.manufacture_inventory_transaction import (
    ManufactureInventoryTransaction,
)
from app.models.manufacture_product import ManufactureProduct
from app.routes.auth import get_current_user
from app.schemas.manufacture_inventory import (
    ManufactureInventoryAdjustment,
    ManufactureInventoryResponse,
    ManufactureInventoryTransactionResponse,
)


router = APIRouter(
    prefix="/manufacture/inventory",
    tags=["Manufacture Inventory"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/", response_model=list[ManufactureInventoryResponse])
def get_inventory(db: Session = Depends(get_db)):
    return db.scalars(
        select(ManufactureInventory).order_by(ManufactureInventory.id.desc())
    ).all()


@router.get("/{product_id}", response_model=ManufactureInventoryResponse)
def get_product_inventory(
    product_id: int,
    db: Session = Depends(get_db),
):
    inventory = db.scalar(
        select(ManufactureInventory).where(
            ManufactureInventory.product_id == product_id
        )
    )
    if inventory is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory not found for this product",
        )
    return inventory


@router.post("/{product_id}/add", response_model=ManufactureInventoryResponse)
def add_stock(
    product_id: int,
    stock_data: ManufactureInventoryAdjustment,
    db: Session = Depends(get_db),
):
    try:
        product = db.get(ManufactureProduct, product_id)
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )

        inventory = db.scalar(
            select(ManufactureInventory)
            .where(ManufactureInventory.product_id == product_id)
            .with_for_update()
        )
        if inventory is None:
            inventory = ManufactureInventory(product_id=product_id, quantity=0)
            db.add(inventory)
            db.flush()

        inventory.quantity += stock_data.quantity
        db.add(
            ManufactureInventoryTransaction(
                product_id=product_id,
                transaction_type="ADJUSTMENT_IN",
                quantity=stock_data.quantity,
                note=stock_data.note,
            )
        )
        db.commit()
        db.refresh(inventory)
        return inventory
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to add manufacture stock",
        )


@router.post("/{product_id}/remove", response_model=ManufactureInventoryResponse)
def remove_stock(
    product_id: int,
    stock_data: ManufactureInventoryAdjustment,
    db: Session = Depends(get_db),
):
    try:
        product = db.get(ManufactureProduct, product_id)
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )

        inventory = db.scalar(
            select(ManufactureInventory)
            .where(ManufactureInventory.product_id == product_id)
            .with_for_update()
        )
        if inventory is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inventory not found for this product",
            )

        if inventory.quantity < stock_data.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Insufficient stock. "
                    f"Available stock: {inventory.quantity}"
                ),
            )

        inventory.quantity -= stock_data.quantity
        db.add(
            ManufactureInventoryTransaction(
                product_id=product_id,
                transaction_type="ADJUSTMENT_OUT",
                quantity=stock_data.quantity,
                note=stock_data.note,
            )
        )
        db.commit()
        db.refresh(inventory)
        return inventory
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to remove manufacture stock",
        )


@router.get(
    "/{product_id}/transactions",
    response_model=list[ManufactureInventoryTransactionResponse],
)
def get_inventory_transactions(
    product_id: int,
    db: Session = Depends(get_db),
):
    product = db.get(ManufactureProduct, product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return db.scalars(
        select(ManufactureInventoryTransaction)
        .where(ManufactureInventoryTransaction.product_id == product_id)
        .order_by(ManufactureInventoryTransaction.id.desc())
    ).all()
