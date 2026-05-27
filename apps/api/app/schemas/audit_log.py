import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditLogEntry(BaseModel):
    id: uuid.UUID
    action: str
    resource_type: str
    resource_id: str | None = None
    details: dict[str, Any] | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
