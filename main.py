import app.models

from fastapi import FastAPI
from sqlalchemy import text

from app.database import engine
from app.routes.customers import router as customer_router
from app.routes.states import router as state_router
from app.routes.products import router as products_router
from app.routes.invoices import router as invoices_router
from fastapi.middleware.cors import CORSMiddleware
from app.routes.inventory import router as inventory_router
from app.routes.notifications import router as notifications_router
from app.routes.auth import router as auth_router
from app.routes.dashboard import router as dashboard_router
from app.routes.manufacture_dashboard import router as manufacture_dashboard_router
from app.routes.manufacture_customers import router as manufacture_customer_router
from app.routes.manufacture_products import router as manufacture_products_router
from app.routes.manufacture_inventory import router as manufacture_inventory_router
from app.routes.manufacture_invoices import router as manufacture_invoice_router
from app.routes.archive import router as archive_router
from app.routes.expenses import router as expenses_router


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/db-test")
def database_test():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        return {
            "database": "connected",
            "result": result.scalar()
        }

app.include_router(customer_router)
app.include_router(state_router)
app.include_router(products_router)
app.include_router(invoices_router)
app.include_router(inventory_router)
app.include_router(notifications_router)
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(manufacture_dashboard_router)
app.include_router(manufacture_customer_router)
app.include_router(manufacture_products_router)
app.include_router(manufacture_inventory_router)
app.include_router(manufacture_invoice_router)
app.include_router(archive_router)
app.include_router(expenses_router)