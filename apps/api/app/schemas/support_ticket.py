import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SupportTicketCreate(BaseModel):
    customer_id: uuid.UUID | None = None
    ticket_number: str
    subject: str
    body: str | None = None
    status: str = "open"
    priority: str = "medium"
    assignee: str | None = None
    tags: list[str] = []


class SupportTicketUpdate(BaseModel):
    customer_id: uuid.UUID | None = None
    ticket_number: str | None = None
    subject: str | None = None
    body: str | None = None
    status: str | None = None
    priority: str | None = None
    assignee: str | None = None
    tags: list[str] | None = None
    resolved_at: datetime | None = None
    satisfaction_score: int | None = None


class SupportTicketSchema(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    customer_id: uuid.UUID | None
    ticket_number: str
    subject: str
    body: str | None
    status: str
    priority: str
    assignee: str | None
    tags: list[str]
    resolved_at: datetime | None
    satisfaction_score: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SupportTicketListResponse(BaseModel):
    items: list[SupportTicketSchema]
    total: int
