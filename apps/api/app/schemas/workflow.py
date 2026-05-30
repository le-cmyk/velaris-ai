import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class WorkflowCreate(BaseModel):
    name: str
    description: str | None = None
    trigger_type: str = "manual"
    steps: list[dict[str, Any]] = []
    is_active: bool = False


class WorkflowUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    trigger_type: str | None = None
    steps: list[dict[str, Any]] | None = None
    is_active: bool | None = None


class WorkflowSchema(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    description: str | None
    trigger_type: str
    steps: list[dict[str, Any]]
    is_active: bool
    version: int
    run_count: int
    last_run_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkflowListResponse(BaseModel):
    items: list[WorkflowSchema]
    total: int
