from decimal import Decimal

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
    ManufactureBundleCountAdjustment,
    ManufactureInventoryAdjustment,
    ManufactureInventoryResponse,
    ManufactureInventoryTransactionResponse,
)


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

        validate_quantity_for_unit(
            stock_data.quantity,
            product.unit,
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

        validate_quantity_for_unit(
            stock_data.quantity,
            product.unit,
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


@router.post("/{product_id}/bundles/add", response_model=ManufactureInventoryResponse)
def add_bundle_count(
    product_id: int,
    adjustment: ManufactureBundleCountAdjustment,
    db: Session = Depends(get_db),
):
    if db.get(ManufactureProduct, product_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    inventory = db.scalar(
        select(ManufactureInventory)
        .where(ManufactureInventory.product_id == product_id)
        .with_for_update()
    )
    if inventory is None:
        inventory = ManufactureInventory(product_id=product_id, quantity=0, bundle_count=0)
        db.add(inventory)
        db.flush()
    inventory.bundle_count += adjustment.count
    db.add(
        ManufactureInventoryTransaction(
            product_id=product_id,
            transaction_type="BUNDLE_ADJUSTMENT_IN",
            quantity=adjustment.count,
            note=adjustment.note,
        )
    )
    db.commit()
    db.refresh(inventory)
    return inventory


@router.post("/{product_id}/bundles/remove", response_model=ManufactureInventoryResponse)
def remove_bundle_count(
    product_id: int,
    adjustment: ManufactureBundleCountAdjustment,
    db: Session = Depends(get_db),
):
    inventory = db.scalar(
        select(ManufactureInventory)
        .where(ManufactureInventory.product_id == product_id)
        .with_for_update()
    )
    if inventory is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory not found for this product")
    if inventory.bundle_count < adjustment.count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient bundles. Available: {inventory.bundle_count}",
        )
    inventory.bundle_count -= adjustment.count
    db.add(
        ManufactureInventoryTransaction(
            product_id=product_id,
            transaction_type="BUNDLE_ADJUSTMENT_OUT",
            quantity=adjustment.count,
            note=adjustment.note,
        )
    )
    db.commit()
    db.refresh(inventory)
    return inventory


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
