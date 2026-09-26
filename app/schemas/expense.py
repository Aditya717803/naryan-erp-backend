from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class ExpenseFields(BaseModel):
    date: date
    description: str = Field(min_length=1, max_length=500)
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Description is required")
        return value


class ExpenseCreate(ExpenseFields):
    pass


class ExpenseUpdate(ExpenseFields):
    pass


class ExpenseResponse(BaseModel):
    id: int
    date: date
    description: str
    amount: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
