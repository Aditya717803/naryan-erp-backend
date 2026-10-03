from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    product_code: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=200)
    hsn_sac: str | None = Field(default=None, max_length=20)
    unit: str = Field(min_length=1, max_length=30)


class ProductUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    hsn_sac: str | None = Field(default=None, max_length=20)
    unit: str = Field(min_length=1, max_length=30)


class ProductResponse(BaseModel):
    id: int
    product_code: str
    name: str
    hsn_sac: str | None
    unit: str

    model_config = {
        "from_attributes": True
    }