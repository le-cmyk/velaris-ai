import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class ApprovalRequestSchema(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    tool_call_id: uuid.UUID
    requested_action: str
    reason: str | None = None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApprovalDecision(BaseModel):
    decision: Literal["approve", "reject"]
    reason: str | None = None
