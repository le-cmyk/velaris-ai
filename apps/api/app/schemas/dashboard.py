import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DashboardCreate(BaseModel):
    name: str
    description: str | None = None
    is_default: bool = False


class DashboardUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_default: bool | None = None


class DashboardSchema(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    description: str | None
    is_default: bool
    created_by_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DashboardListResponse(BaseModel):
    items: list[DashboardSchema]
    total: int


class DashboardWithWidgets(DashboardSchema):
    widgets: list[dict] = []  # DashboardWidgetSchema dicts, resolved at runtime
