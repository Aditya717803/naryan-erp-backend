from datetime import datetime

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    user_id: str = Field(
        min_length=1,
        max_length=50,
    )

    password: str = Field(
        min_length=1,
        max_length=100,
    )


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    user_id: str
    name: str
    is_active: bool
    created_at: datetime

    model_config = {
        "from_attributes": True,
    }