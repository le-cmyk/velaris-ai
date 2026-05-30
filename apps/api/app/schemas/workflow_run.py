import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class WorkflowRunSchema(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    workflow_id: uuid.UUID
    status: str
    triggered_by: str
    started_at: datetime
    completed_at: datetime | None
    results: dict[str, Any]
    error: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkflowRunListResponse(BaseModel):
    items: list[WorkflowRunSchema]
    total: int
