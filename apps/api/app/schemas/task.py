import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    status: str = "todo"
    priority: str = "medium"
    due_date: date | None = None
    assignee: str | None = None
    parent_id: uuid.UUID | None = None
    linked_entity_type: str | None = None
    linked_entity_id: uuid.UUID | None = None
    tags: list[str] = []


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    due_date: date | None = None
    assignee: str | None = None
    parent_id: uuid.UUID | None = None
    linked_entity_type: str | None = None
    linked_entity_id: uuid.UUID | None = None
    tags: list[str] | None = None


class TaskSchema(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    title: str
    description: str | None
    status: str
    priority: str
    due_date: date | None
    assignee: str | None
    parent_id: uuid.UUID | None
    linked_entity_type: str | None
    linked_entity_id: uuid.UUID | None
    tags: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskListResponse(BaseModel):
    items: list[TaskSchema]
    total: int
