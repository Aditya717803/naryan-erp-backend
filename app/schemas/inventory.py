from datetime import datetime

from pydantic import BaseModel, Field


class InventoryAdjustment(BaseModel):
    quantity: int = Field(gt=0)
    note: str | None = Field(default=None, max_length=500)


class InventoryResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }


class InventoryTransactionResponse(BaseModel):
    id: int
    product_id: int
    transaction_type: str
    quantity: int
    note: str | None
    created_at: datetime

    model_config = {
        "from_attributes": True
    }