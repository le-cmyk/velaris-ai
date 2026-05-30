import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ScheduledJobCreate(BaseModel):
    name: str
    description: str | None = None
    agent_template_id: uuid.UUID | None = None
    message: str
    cron_expr: str | None = None
    interval_minutes: int | None = None
    is_active: bool = False


class ScheduledJobUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    agent_template_id: uuid.UUID | None = None
    message: str | None = None
    cron_expr: str | None = None
    interval_minutes: int | None = None
    is_active: bool | None = None
    next_run_at: datetime | None = None


class ScheduledJobSchema(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    description: str | None
    agent_template_id: uuid.UUID | None
    message: str
    cron_expr: str | None
    interval_minutes: int | None
    is_active: bool
    last_run_at: datetime | None
    last_run_status: str | None
    last_run_error: str | None
    next_run_at: datetime | None
    run_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScheduledJobListResponse(BaseModel):
    items: list[ScheduledJobSchema]
    total: int
