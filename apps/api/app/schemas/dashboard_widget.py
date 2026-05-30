import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class DashboardWidgetCreate(BaseModel):
    dashboard_id: uuid.UUID
    title: str
    widget_type: str
    data_source: str = "query"
    query: str | None = None
    config: dict[str, Any] = {}
    position_x: int = 0
    position_y: int = 0
    width: int = 4
    height: int = 3
    refresh_seconds: int | None = None


class DashboardWidgetUpdate(BaseModel):
    title: str | None = None
    widget_type: str | None = None
    data_source: str | None = None
    query: str | None = None
    config: dict[str, Any] | None = None
    position_x: int | None = None
    position_y: int | None = None
    width: int | None = None
    height: int | None = None
    refresh_seconds: int | None = None
    last_data: dict[str, Any] | None = None
    last_refreshed_at: datetime | None = None


class DashboardWidgetSchema(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    dashboard_id: uuid.UUID
    title: str
    widget_type: str
    data_source: str
    query: str | None
    config: dict[str, Any]
    position_x: int
    position_y: int
    width: int
    height: int
    refresh_seconds: int | None
    last_data: dict[str, Any] | None
    last_refreshed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
