import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AgentTemplateCreate(BaseModel):
    name: str
    description: str | None = None
    icon: str = "🤖"
    category: str = "general"
    system_prompt: str
    allowed_tools: list[str] = []
    is_active: bool = True


class AgentTemplateUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    icon: str | None = None
    category: str | None = None
    system_prompt: str | None = None
    allowed_tools: list[str] | None = None
    is_active: bool | None = None


class AgentTemplateSchema(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    description: str | None
    icon: str
    category: str
    system_prompt: str
    allowed_tools: list[str]
    is_active: bool
    is_builtin: bool
    created_by_id: uuid.UUID | None
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentTemplateListResponse(BaseModel):
    items: list[AgentTemplateSchema]
    total: int
