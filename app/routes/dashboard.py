from datetime import date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.customer import Customer
from app.models.inventory import Inventory
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.product import Product
from app.routes.auth import get_current_user


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


def _period_dates(period: str) -> tuple[date, date]:
    today = date.today()
    if period == "day":
        return today, today
    if period == "week":
        return today - timedelta(days=today.weekday()), today
    if period == "month":
        return today.replace(day=1), today
    if period == "year":
        return today.replace(month=1, day=1), today
    raise HTTPException(status_code=400, detail="period must be day, week, month, or year")


@router.get("/")
def get_dashboard(
    db: Session = Depends(get_db),
):
    today = date.today()
    seven_days_ago = today - timedelta(days=6)

    # -------------------------
    # Basic counts
    # -------------------------

    total_products = db.scalar(
        select(func.count(Product.id))
    ) or 0

    total_customers = db.scalar(
        select(func.count(Customer.id))
    ) or 0

    total_stock = db.scalar(
        select(func.coalesce(func.sum(Inventory.quantity), 0))
    ) or 0

    low_stock_count = db.scalar(
        select(func.count(Inventory.id)).where(
            Inventory.quantity < 10,
            Inventory.quantity > 0,
        )
    ) or 0

    out_of_stock_count = db.scalar(
        select(func.count(Inventory.id)).where(
            Inventory.quantity <= 0,
        )
    ) or 0

    # -------------------------
    # Today's sales
    # -------------------------

    today_sales = db.scalar(
        select(
            func.coalesce(
                func.sum(Invoice.grand_total),
                0,
            )
        ).where(
            Invoice.invoice_date == today
        )
    ) or Decimal("0")

    today_invoice_count = db.scalar(
        select(func.count(Invoice.id)).where(
            Invoice.invoice_date == today
        )
    ) or 0

    # -------------------------
    # Recent invoices
    # -------------------------

    recent_invoices = db.execute(
        select(
            Invoice.id,
            Invoice.invoice_number,
            Invoice.invoice_date,
            Invoice.grand_total,
            Customer.name.label("customer_name"),
        )
        .join(
            Customer,
            Customer.id == Invoice.customer_id,
        )
        .order_by(
            Invoice.id.desc()
        )
        .limit(5)
    ).all()

    # -------------------------
    # Low-stock products
    # -------------------------

    low_stock_products = db.execute(
        select(
            Product.id,
            Product.product_code,
            Product.name,
            Product.unit,
            Inventory.quantity,
        )
        .join(
            Inventory,
            Inventory.product_id == Product.id,
        )
        .where(
            Inventory.quantity < 10
        )
        .order_by(
            Inventory.quantity.asc()
        )
        .limit(10)
    ).all()

    # -------------------------
    # Sales trend - last 7 days
    # -------------------------

    sales_trend = db.execute(
        select(
            Invoice.invoice_date,
            func.coalesce(
                func.sum(Invoice.grand_total),
                0,
            ).label("sales"),
            func.count(Invoice.id).label("invoice_count"),
        )
        .where(
            Invoice.invoice_date >= seven_days_ago,
            Invoice.invoice_date <= today,
        )
        .group_by(
            Invoice.invoice_date
        )
        .order_by(
            Invoice.invoice_date.asc()
        )
    ).all()

    # -------------------------
    # Top-selling products
    # -------------------------

    top_products = db.execute(
        select(
            Product.id,
            Product.name,
            Product.product_code,
            func.sum(
                InvoiceItem.quantity
            ).label("quantity_sold"),
        )
        .join(
            InvoiceItem,
            InvoiceItem.product_id == Product.id,
        )
        .group_by(
            Product.id,
            Product.name,
            Product.product_code,
        )
        .order_by(
            func.sum(
                InvoiceItem.quantity
            ).desc()
        )
        .limit(5)
    ).all()

    return {
        "summary": {
            "today_sales": float(today_sales),
            "today_invoice_count": today_invoice_count,
            "total_customers": total_customers,
            "total_products": total_products,
            "total_stock": int(total_stock),
            "low_stock_count": low_stock_count,
            "out_of_stock_count": out_of_stock_count,
        },

        "recent_invoices": [
            {
                "id": row.id,
                "invoice_number": row.invoice_number,
                "invoice_date": row.invoice_date,
                "grand_total": float(row.grand_total),
                "customer_name": row.customer_name,
            }

            for row in recent_invoices
        ],

        "low_stock_products": [
            {
                "id": row.id,
                "product_code": row.product_code,
                "name": row.name,
                "unit": row.unit,
                "quantity": row.quantity,
            }
            for row in low_stock_products
        ],

        "sales_trend": [
            {
                "date": row.invoice_date,
                "sales": float(row.sales),
                "invoice_count": row.invoice_count,
            }
            for row in sales_trend
        ],

        "top_products": [
            {
                "id": row.id,
                "product_code": row.product_code,
                "name": row.name,
                "quantity_sold": float(row.quantity_sold),
            }
            for row in top_products
        ],
    }


@router.get("/top-products")
def get_top_products(
    period: str = "day",
    db: Session = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    start_date, end_date = _period_dates(period)
    rows = db.execute(
        select(
            Product.id, Product.product_code, Product.name, InvoiceItem.unit,
            func.sum(InvoiceItem.quantity).label("quantity_sold"),
        )
        .join(InvoiceItem, InvoiceItem.product_id == Product.id)
        .join(Invoice, Invoice.id == InvoiceItem.invoice_id)
        .where(Invoice.invoice_date >= start_date, Invoice.invoice_date <= end_date)
        .group_by(Product.id, Product.product_code, Product.name, InvoiceItem.unit)
        .order_by(func.sum(InvoiceItem.quantity).desc())
        .limit(5)
    ).all()
    return [
        {
            "id": row.id,
            "product_code": row.product_code,
            "name": row.name,
            "quantity_sold": float(row.quantity_sold),
            "unit": row.unit,
            "units": row.unit,
        }
        for row in rows
    ]