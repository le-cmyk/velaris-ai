import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ConversationCreate(BaseModel):
    title: str = "New Conversation"
    agent_template_id: uuid.UUID | None = None


class ConversationUpdate(BaseModel):
    title: str | None = None
    agent_template_id: uuid.UUID | None = None


class ConversationSchema(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    user_id: uuid.UUID | None
    title: str
    agent_template_id: uuid.UUID | None
    message_count: int
    last_message_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationListResponse(BaseModel):
    items: list[ConversationSchema]
    total: int
