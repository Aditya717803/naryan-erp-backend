from pydantic import BaseModel


class StateResponse(BaseModel):
    id: int
    name: str
    code: str

    model_config = {
        "from_attributes": True
    }