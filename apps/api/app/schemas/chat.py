import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    message: str
    workspace_id: uuid.UUID


class ToolCallResult(BaseModel):
    tool_name: str
    arguments: dict[str, Any]
    status: str
    result: dict[str, Any] | None = None
    requires_approval: bool = False


class ChatResponse(BaseModel):
    run_id: uuid.UUID
    message: str
    intent: str | None = None
    execution_plan: dict[str, Any] | None = None
    tool_calls: list[ToolCallResult] = Field(default_factory=list)
    pending_approvals: list[dict[str, Any]] = Field(default_factory=list)
    status: str

    model_config = ConfigDict(from_attributes=True)
