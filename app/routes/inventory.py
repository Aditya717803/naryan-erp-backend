from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.inventory import Inventory
from app.models.inventory_transaction import InventoryTransaction
from app.models.notification import Notification
from app.models.product import Product
from app.schemas.inventory import (
    BundleCountAdjustment,
    InventoryAdjustment,
    InventoryResponse,
    InventoryTransactionResponse,
)
from app.routes.auth import get_current_user


router = APIRouter(
    prefix="/inventory",
    tags=["Inventory"],
    dependencies=[Depends(get_current_user)],
)


LOW_STOCK_THRESHOLD = 10


@router.get(
    "/",
    response_model=list[InventoryResponse],
)
def get_inventory(
    db: Session = Depends(get_db),
):
    inventory = db.scalars(
        select(Inventory).order_by(Inventory.id.desc())
    ).all()

    return inventory


@router.get(
    "/{product_id}",
    response_model=InventoryResponse,
)
def get_product_inventory(
    product_id: int,
    db: Session = Depends(get_db),
):
    inventory = db.scalar(
        select(Inventory).where(
            Inventory.product_id == product_id
        )
    )

    if inventory is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory not found for this product",
        )

    return inventory


@router.post(
    "/{product_id}/add",
    response_model=InventoryResponse,
)
def add_stock(
    product_id: int,
    stock_data: InventoryAdjustment,
    db: Session = Depends(get_db),
):
    # Check product exists
    product = db.get(Product, product_id)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    # Get inventory
    inventory = db.scalar(
        select(Inventory).where(
            Inventory.product_id == product_id
        )
    )

    # Create inventory record if it doesn't exist
    if inventory is None:
        inventory = Inventory(
            product_id=product_id,
            quantity=0,
        )

        db.add(inventory)
        db.flush()

    # Store old quantity before changing stock
    old_quantity = inventory.quantity

    # Add stock
    inventory.quantity += stock_data.quantity

    new_quantity = inventory.quantity

    # Create transaction
    transaction = InventoryTransaction(
        product_id=product_id,
        transaction_type="ADJUSTMENT_IN",
        quantity=stock_data.quantity,
        note=stock_data.note,
    )

    db.add(transaction)

    # ---------------------------------------------------------
    # LOW STOCK NOTIFICATION
    # ---------------------------------------------------------
    #
    # We normally don't create a notification when adding stock.
    #
    # However, if stock was already below the threshold and the
    # product is being added back to a normal level, we simply
    # allow the existing low-stock condition to clear.
    #
    # No notification is required here.
    # ---------------------------------------------------------

    db.commit()
    db.refresh(inventory)

    return inventory


@router.post(
    "/{product_id}/remove",
    response_model=InventoryResponse,
)
def remove_stock(
    product_id: int,
    stock_data: InventoryAdjustment,
    db: Session = Depends(get_db),
):
    # Check product exists
    product = db.get(Product, product_id)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    # Get inventory
    inventory = db.scalar(
        select(Inventory).where(
            Inventory.product_id == product_id
        )
    )

    if inventory is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory not found for this product",
        )

    # Prevent negative stock
    if inventory.quantity < stock_data.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Insufficient stock. "
                f"Available stock: {inventory.quantity}"
            ),
        )

    # Store old quantity before changing stock
    old_quantity = inventory.quantity

    # Remove stock
    inventory.quantity -= stock_data.quantity

    new_quantity = inventory.quantity

    # Create transaction
    transaction = InventoryTransaction(
        product_id=product_id,
        transaction_type="ADJUSTMENT_OUT",
        quantity=stock_data.quantity,
        note=stock_data.note,
    )

    db.add(transaction)

    # ---------------------------------------------------------
    # LOW STOCK NOTIFICATION
    # ---------------------------------------------------------

    if (
        old_quantity > LOW_STOCK_THRESHOLD
        and new_quantity <= LOW_STOCK_THRESHOLD
        and new_quantity > 0
    ):
        notification = Notification(
            title="Low Stock",
            message=(
                f"{product.name} has only "
                f"{new_quantity} {product.unit} remaining."
            ),
            notification_type="LOW_STOCK",
            product_id=product.id,
            is_read=False,
        )

        db.add(notification)

    # ---------------------------------------------------------
    # OUT OF STOCK NOTIFICATION
    # ---------------------------------------------------------

    if (
        old_quantity > 0
        and new_quantity == 0
    ):
        notification = Notification(
            title="Out of Stock",
            message=(
                f"{product.name} is out of stock."
            ),
            notification_type="OUT_OF_STOCK",
            product_id=product.id,
            is_read=False,
        )

        db.add(notification)

    # Commit inventory + transaction + notification
    # together
    db.commit()

    db.refresh(inventory)

    return inventory


@router.post("/{product_id}/bundles/add", response_model=InventoryResponse)
def add_bundle_count(
    product_id: int,
    adjustment: BundleCountAdjustment,
    db: Session = Depends(get_db),
):
    if db.get(Product, product_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    inventory = db.scalar(
        select(Inventory).where(Inventory.product_id == product_id).with_for_update()
    )
    if inventory is None:
        inventory = Inventory(product_id=product_id, quantity=0, bundle_count=0)
        db.add(inventory)
        db.flush()
    inventory.bundle_count += adjustment.count
    db.commit()
    db.refresh(inventory)
    return inventory


@router.post("/{product_id}/bundles/remove", response_model=InventoryResponse)
def remove_bundle_count(
    product_id: int,
    adjustment: BundleCountAdjustment,
    db: Session = Depends(get_db),
):
    inventory = db.scalar(
        select(Inventory).where(Inventory.product_id == product_id).with_for_update()
    )
    if inventory is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory not found for this product")
    if inventory.bundle_count < adjustment.count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient bundles. Available: {inventory.bundle_count}",
        )
    inventory.bundle_count -= adjustment.count
    db.commit()
    db.refresh(inventory)
    return inventory


@router.get(
    "/{product_id}/transactions",
    response_model=list[InventoryTransactionResponse],
)
def get_inventory_transactions(
    product_id: int,
    db: Session = Depends(get_db),
):
    # Check product exists
    product = db.get(Product, product_id)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    transactions = db.scalars(
        select(InventoryTransaction)
        .where(
            InventoryTransaction.product_id == product_id
        )
        .order_by(
            InventoryTransaction.id.desc()
        )
    ).all()

    return transactions