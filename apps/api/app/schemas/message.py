import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class MessageCreate(BaseModel):
    conversation_id: uuid.UUID
    role: str
    content: str
    agent_run_id: uuid.UUID | None = None
    metadata_: dict[str, Any] | None = None


class MessageSchema(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: str
    agent_run_id: uuid.UUID | None
    metadata_: dict[str, Any] | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageListResponse(BaseModel):
    items: list[MessageSchema]
    total: int
