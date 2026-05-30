import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ApiKeyCreate(BaseModel):
    name: str
    scopes: list[str] = ["read"]
    expires_at: datetime | None = None


class ApiKeySchema(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    user_id: uuid.UUID | None
    name: str
    key_prefix: str
    scopes: list[str]
    is_active: bool
    last_used_at: datetime | None
    expires_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApiKeyWithSecret(ApiKeySchema):
    """Returned only at creation time — includes the plain-text key."""
    plain_key: str
