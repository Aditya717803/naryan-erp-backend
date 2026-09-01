from datetime import date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.manufacture_customer import ManufactureCustomer
from app.models.manufacture_inventory import ManufactureInventory
from app.models.manufacture_invoice import ManufactureInvoice
from app.models.manufacture_invoice_item import ManufactureInvoiceItem
from app.models.manufacture_product import ManufactureProduct


router = APIRouter(
    prefix="/manufacture/dashboard",
    tags=["Manufacture Dashboard"],
)


@router.get("/")
def get_manufacture_dashboard(
    db: Session = Depends(get_db),
):
    today = date.today()
    seven_days_ago = today - timedelta(days=6)

    total_products = db.scalar(
        select(func.count(ManufactureProduct.id))
    ) or 0

    total_customers = db.scalar(
        select(func.count(ManufactureCustomer.id))
    ) or 0

    total_stock = db.scalar(
        select(func.coalesce(func.sum(ManufactureInventory.quantity), 0))
    ) or 0

    low_stock_count = db.scalar(
        select(func.count(ManufactureInventory.id)).where(
            ManufactureInventory.quantity < 10,
            ManufactureInventory.quantity > 0,
        )
    ) or 0

    out_of_stock_count = db.scalar(
        select(func.count(ManufactureInventory.id)).where(
            ManufactureInventory.quantity <= 0,
        )
    ) or 0

    today_sales = db.scalar(
        select(
            func.coalesce(
                func.sum(ManufactureInvoice.grand_total),
                0,
            )
        ).where(
            ManufactureInvoice.invoice_date == today
        )
    ) or Decimal("0")

    today_invoice_count = db.scalar(
        select(func.count(ManufactureInvoice.id)).where(
            ManufactureInvoice.invoice_date == today
        )
    ) or 0

    recent_invoices = db.execute(
        select(
            ManufactureInvoice.id,
            ManufactureInvoice.invoice_number,
            ManufactureInvoice.invoice_date,
            ManufactureInvoice.grand_total,
            ManufactureCustomer.name.label("customer_name"),
        )
        .join(
            ManufactureCustomer,
            ManufactureCustomer.id == ManufactureInvoice.customer_id,
        )
        .order_by(
            ManufactureInvoice.id.desc()
        )
        .limit(5)
    ).all()

    low_stock_products = db.execute(
        select(
            ManufactureProduct.id,
            ManufactureProduct.product_code,
            ManufactureProduct.name,
            ManufactureProduct.unit,
            ManufactureInventory.quantity,
        )
        .join(
            ManufactureInventory,
            ManufactureInventory.product_id == ManufactureProduct.id,
        )
        .where(
            ManufactureInventory.quantity < 10,
        )
        .order_by(
            ManufactureInventory.quantity.asc()
        )
        .limit(10)
    ).all()

    sales_trend = db.execute(
        select(
            ManufactureInvoice.invoice_date,
            func.coalesce(
                func.sum(ManufactureInvoice.grand_total),
                0,
            ).label("sales"),
            func.count(ManufactureInvoice.id).label("invoice_count"),
        )
        .where(
            ManufactureInvoice.invoice_date >= seven_days_ago,
            ManufactureInvoice.invoice_date <= today,
        )
        .group_by(
            ManufactureInvoice.invoice_date
        )
        .order_by(
            ManufactureInvoice.invoice_date.asc()
        )
    ).all()

    top_products = db.execute(
        select(
            ManufactureProduct.id,
            ManufactureProduct.name,
            ManufactureProduct.product_code,
            func.sum(
                ManufactureInvoiceItem.quantity
            ).label("quantity_sold"),
        )
        .join(
            ManufactureInvoiceItem,
            ManufactureInvoiceItem.product_id == ManufactureProduct.id,
        )
        .group_by(
            ManufactureProduct.id,
            ManufactureProduct.name,
            ManufactureProduct.product_code,
        )
        .order_by(
            func.sum(
                ManufactureInvoiceItem.quantity
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
