from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ManufactureInventoryAdjustment(BaseModel):
    quantity: Decimal = Field(gt=0)
    note: str | None = Field(default=None, max_length=500)


class ManufactureBundleCountAdjustment(BaseModel):
    count: int = Field(gt=0)


class ManufactureInventoryResponse(BaseModel):
    id: int
    product_id: int
    quantity: Decimal
    bundle_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ManufactureInventoryTransactionResponse(BaseModel):
    id: int
    product_id: int
    transaction_type: str
    quantity: Decimal
    note: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
