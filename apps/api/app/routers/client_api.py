from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.backend.dynamic_endpoints import execute_client_endpoint, resolve_client_endpoint
from app.core.deps import get_current_active_user
from app.database import get_db
from app.models.user import User

router = APIRouter()


@router.api_route("/{path:path}", methods=["GET", "POST", "PATCH", "PUT", "DELETE"])
async def execute_dynamic_client_endpoint(
    path: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    endpoint = await resolve_client_endpoint(
        db,
        workspace_id=current_user.workspace_id,
        method=request.method,
        path=path,
    )
    return await execute_client_endpoint(
        db,
        endpoint=endpoint,
        current_user=current_user,
        request=request,
    )

