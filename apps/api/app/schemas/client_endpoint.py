from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


EndpointMethod = Literal["GET", "POST", "PATCH", "PUT", "DELETE"]
EndpointMode = Literal["agent_task", "data_query", "client_data_create"]


class ClientEndpointCreate(BaseModel):
    name: str
    method: EndpointMethod
    path: str
    mode: EndpointMode
    description: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        normalized = "/" + value.strip().strip("/")
        if normalized == "/":
            raise ValueError("Endpoint path cannot be root")
        if normalized.startswith(("/backend", "/auth", "/data", "/client-data", "/client-api")):
            raise ValueError("Endpoint path cannot use a reserved Velaris prefix")
        return normalized


class ClientEndpointUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    config: dict[str, Any] | None = None
    is_active: bool | None = None


class ClientEndpointSchema(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    created_by_id: uuid.UUID | None
    name: str
    method: str
    path: str
    mode: str
    description: str | None
    config: dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClientEndpointListResponse(BaseModel):
    items: list[ClientEndpointSchema]
    total: int
