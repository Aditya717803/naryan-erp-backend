from pydantic import BaseModel, Field


class CustomerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    gstin_uin: str | None = Field(default=None, max_length=20)
    contact_person: str | None = Field(default=None, max_length=150)
    address: str = Field(min_length=1)
    state_id: int

class CustomerResponse(BaseModel):
    id: int
    customer_code: str
    name: str
    gstin_uin: str | None
    contact_person: str | None
    address: str
    state_id: int

    model_config = {
        "from_attributes": True
    }