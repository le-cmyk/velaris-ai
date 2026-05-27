from pydantic import BaseModel


class ToolInfo(BaseModel):
    name: str
    description: str
    requires_approval: bool
    enabled: bool


class ToolListResponse(BaseModel):
    tools: list[ToolInfo]
