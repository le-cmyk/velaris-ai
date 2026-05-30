from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.backend.blueprints import create_backend_blueprint, get_backend_capabilities
from app.core.deps import get_current_active_user
from app.database import get_db
from app.models.audit_log import AuditLog
from app.models.client_endpoint import ClientEndpoint
from app.models.user import User
from app.schemas.backend_blueprint import (
    BackendBlueprintRequest,
    BackendBlueprintResponse,
    BackendCapabilitiesResponse,
)
from app.schemas.client_endpoint import (
    ClientEndpointCreate,
    ClientEndpointListResponse,
    ClientEndpointSchema,
    ClientEndpointUpdate,
)

router = APIRouter()


@router.get("/capabilities", response_model=BackendCapabilitiesResponse)
async def backend_capabilities(
    current_user: User = Depends(get_current_active_user),
) -> BackendCapabilitiesResponse:
    return get_backend_capabilities()


@router.post("/blueprints", response_model=BackendBlueprintResponse)
async def create_blueprint(
    payload: BackendBlueprintRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> BackendBlueprintResponse:
    blueprint = create_backend_blueprint(payload)
    db.add(
        AuditLog(
            workspace_id=current_user.workspace_id,
            user_id=current_user.id,
            action="backend.blueprint.create",
            resource_type="backend_blueprint",
            details={
                "requested_routes": [route.model_dump() for route in payload.requested_routes],
                "data_entities": [entity.model_dump() for entity in payload.data_entities],
                "infrastructure": payload.infrastructure,
            },
            ip_address=request.client.host if request.client else None,
        )
    )
    await db.commit()
    return blueprint


@router.get("/endpoints", response_model=ClientEndpointListResponse)
async def list_client_endpoints(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ClientEndpointListResponse:
    base_q = select(ClientEndpoint).where(ClientEndpoint.workspace_id == current_user.workspace_id)
    total = await db.scalar(select(func.count()).select_from(base_q.subquery())) or 0
    result = await db.execute(base_q.order_by(ClientEndpoint.created_at.desc()))
    endpoints = result.scalars().all()
    return ClientEndpointListResponse(
        items=[ClientEndpointSchema.model_validate(endpoint) for endpoint in endpoints],
        total=total,
    )


@router.post("/endpoints", response_model=ClientEndpointSchema, status_code=201)
async def create_client_endpoint(
    payload: ClientEndpointCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ClientEndpointSchema:
    endpoint = ClientEndpoint(
        workspace_id=current_user.workspace_id,
        created_by_id=current_user.id,
        name=payload.name,
        method=payload.method,
        path=payload.path,
        mode=payload.mode,
        description=payload.description,
        config=payload.config,
        is_active=payload.is_active,
    )
    db.add(endpoint)
    await db.flush()
    db.add(
        AuditLog(
            workspace_id=current_user.workspace_id,
            user_id=current_user.id,
            action="client_endpoint.create",
            resource_type="client_endpoint",
            resource_id=str(endpoint.id),
            details={
                "method": endpoint.method,
                "path": endpoint.path,
                "mode": endpoint.mode,
                "config": endpoint.config,
            },
            ip_address=request.client.host if request.client else None,
        )
    )
    await db.commit()
    return ClientEndpointSchema.model_validate(endpoint)


@router.patch("/endpoints/{endpoint_id}", response_model=ClientEndpointSchema)
async def update_client_endpoint(
    endpoint_id: uuid.UUID,
    payload: ClientEndpointUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ClientEndpointSchema:
    result = await db.execute(
        select(ClientEndpoint).where(
            ClientEndpoint.id == endpoint_id,
            ClientEndpoint.workspace_id == current_user.workspace_id,
        )
    )
    endpoint = result.scalar_one_or_none()
    if endpoint is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Client endpoint not found")

    if payload.name is not None:
        endpoint.name = payload.name
    if payload.description is not None:
        endpoint.description = payload.description
    if payload.config is not None:
        endpoint.config = payload.config
    if payload.is_active is not None:
        endpoint.is_active = payload.is_active

    db.add(
        AuditLog(
            workspace_id=current_user.workspace_id,
            user_id=current_user.id,
            action="client_endpoint.update",
            resource_type="client_endpoint",
            resource_id=str(endpoint.id),
            details={"method": endpoint.method, "path": endpoint.path, "is_active": endpoint.is_active},
            ip_address=request.client.host if request.client else None,
        )
    )
    await db.commit()
    return ClientEndpointSchema.model_validate(endpoint)
