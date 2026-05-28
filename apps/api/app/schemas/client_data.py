import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ClientDataRecordCreate(BaseModel):
    type: str
    title: str
    content: str | None = None
    metadata_: dict[str, Any] | None = None


class ClientDataRecordUpdate(BaseModel):
    type: str | None = None
    title: str | None = None
    content: str | None = None
    metadata_: dict[str, Any] | None = None


class ClientDataRecordSchema(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    type: str
    title: str
    content: str | None
    metadata_: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClientDataListResponse(BaseModel):
    items: list[ClientDataRecordSchema]
    total: int
