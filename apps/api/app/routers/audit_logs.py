from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user
from app.database import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit_log import AuditLogEntry

router = APIRouter()


@router.get("")
async def list_audit_logs(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    total = await db.scalar(select(func.count(AuditLog.id)).where(AuditLog.workspace_id == current_user.workspace_id))
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.workspace_id == current_user.workspace_id)
        .order_by(AuditLog.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    items = [AuditLogEntry.model_validate(item) for item in result.scalars().all()]
    return {"items": items, "total": total or 0, "skip": skip, "limit": limit}
