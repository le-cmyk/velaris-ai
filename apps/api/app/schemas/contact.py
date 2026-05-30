import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ContactCreate(BaseModel):
    customer_id: uuid.UUID | None = None
    name: str
    email: str | None = None
    phone: str | None = None
    role: str | None = None
    linkedin_url: str | None = None
    is_primary: bool = False
    last_contact_at: datetime | None = None
    notes: str | None = None


class ContactUpdate(BaseModel):
    customer_id: uuid.UUID | None = None
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    role: str | None = None
    linkedin_url: str | None = None
    is_primary: bool | None = None
    last_contact_at: datetime | None = None
    notes: str | None = None


class ContactSchema(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    customer_id: uuid.UUID | None
    name: str
    email: str | None
    phone: str | None
    role: str | None
    linkedin_url: str | None
    is_primary: bool
    last_contact_at: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ContactListResponse(BaseModel):
    items: list[ContactSchema]
    total: int
