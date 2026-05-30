import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationSchema(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    user_id: uuid.UUID | None
    type: str
    title: str
    body: str | None
    is_read: bool
    linked_entity_type: str | None
    linked_entity_id: uuid.UUID | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    items: list[NotificationSchema]
    total: int
