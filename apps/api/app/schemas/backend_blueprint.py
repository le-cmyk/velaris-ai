from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class RequestedRoute(BaseModel):
    method: Literal["GET", "POST", "PATCH", "PUT", "DELETE"]
    path: str
    purpose: str | None = None
    auth_required: bool = True


class RequestedEntity(BaseModel):
    name: str
    fields: list[str] = Field(default_factory=list)
    relationships: list[str] = Field(default_factory=list)


class BackendBlueprintRequest(BaseModel):
    description: str = Field(..., description="Natural language backend need from a client or agent")
    requested_routes: list[RequestedRoute] = Field(default_factory=list)
    data_entities: list[RequestedEntity] = Field(default_factory=list)
    infrastructure: list[str] = Field(default_factory=list)


class BlueprintRoute(BaseModel):
    method: str
    path: str
    purpose: str
    auth_required: bool
    workspace_scoped: bool
    status: Literal["available", "proposed"]
    handler: str | None = None


class BlueprintDataObject(BaseModel):
    name: str
    backing_table: str | None
    fields: list[str]
    relationships: list[str]
    status: Literal["available", "proposed"]


class BlueprintInfrastructureItem(BaseModel):
    name: str
    purpose: str
    status: Literal["available", "recommended"]


class BackendBlueprintResponse(BaseModel):
    summary: str
    routes: list[BlueprintRoute]
    data_objects: list[BlueprintDataObject]
    infrastructure: list[BlueprintInfrastructureItem]
    implementation_steps: list[str]
    open_questions: list[str]


class BackendCapability(BaseModel):
    name: str
    description: str
    entrypoints: list[str]


class BackendCapabilitiesResponse(BaseModel):
    capabilities: list[BackendCapability]

