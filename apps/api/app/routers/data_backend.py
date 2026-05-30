from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user
from app.data.catalog import build_data_catalog, execute_data_query
from app.database import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.data_backend import DataCatalogResponse, DataQueryRequest, DataQueryResponse

router = APIRouter()


@router.get("/catalog", response_model=DataCatalogResponse)
async def get_data_catalog(
    include_counts: bool = Query(default=False),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DataCatalogResponse:
    return await build_data_catalog(
        db,
        workspace_id=current_user.workspace_id,
        include_counts=include_counts,
    )


@router.get("/relationships", response_model=DataCatalogResponse)
async def get_data_relationships(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DataCatalogResponse:
    catalog = await build_data_catalog(db, workspace_id=current_user.workspace_id)
    return DataCatalogResponse(tables=[], relationships=catalog.relationships)


@router.post("/query", response_model=DataQueryResponse)
async def query_data(
    payload: DataQueryRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DataQueryResponse:
    result = await execute_data_query(db, workspace_id=current_user.workspace_id, request=payload)
    db.add(
        AuditLog(
            workspace_id=current_user.workspace_id,
            user_id=current_user.id,
            action="data.query",
            resource_type=payload.table,
            details={
                "table": payload.table,
                "filters": [filter_.model_dump() for filter_ in payload.filters],
                "selected_columns": payload.select,
                "row_count": result.row_count,
            },
            ip_address=request.client.host if request.client else None,
        )
    )
    await db.commit()
    return result
