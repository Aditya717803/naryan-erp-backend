from datetime import datetime

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    notification_type: str
    product_id: int | None
    is_read: bool
    created_at: datetime

    model_config = {
        "from_attributes": True
    }