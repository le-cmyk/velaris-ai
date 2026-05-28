import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user
from app.database import get_db
from app.models.audit_log import AuditLog
from app.models.client_data import ClientDataRecord
from app.models.user import User
from app.schemas.client_data import (
    ClientDataListResponse,
    ClientDataRecordCreate,
    ClientDataRecordSchema,
    ClientDataRecordUpdate,
)

router = APIRouter()


@router.get("", response_model=ClientDataListResponse)
async def list_client_data(
    type: str | None = Query(default=None, description="Filter by record type"),
    search: str | None = Query(default=None, description="Search in title"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ClientDataListResponse:
    base_q = select(ClientDataRecord).where(ClientDataRecord.workspace_id == current_user.workspace_id)
    if type:
        base_q = base_q.where(ClientDataRecord.type == type)
    if search:
        base_q = base_q.where(ClientDataRecord.title.ilike(f"%{search}%"))

    count_q = select(func.count()).select_from(base_q.subquery())
    total = await db.scalar(count_q) or 0

    result = await db.execute(
        base_q.order_by(ClientDataRecord.created_at.desc()).offset(skip).limit(limit)
    )
    records = result.scalars().all()
    return ClientDataListResponse(
        items=[ClientDataRecordSchema.model_validate(r) for r in records],
        total=total,
    )


@router.get("/{record_id}", response_model=ClientDataRecordSchema)
async def get_client_data(
    record_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ClientDataRecordSchema:
    result = await db.execute(
        select(ClientDataRecord).where(
            ClientDataRecord.id == record_id,
            ClientDataRecord.workspace_id == current_user.workspace_id,
        )
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    return ClientDataRecordSchema.model_validate(record)


@router.post("", response_model=ClientDataRecordSchema, status_code=status.HTTP_201_CREATED)
async def create_client_data(
    payload: ClientDataRecordCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ClientDataRecordSchema:
    record = ClientDataRecord(
        id=uuid.uuid4(),
        workspace_id=current_user.workspace_id,
        type=payload.type,
        title=payload.title,
        content=payload.content,
        metadata_=payload.metadata_,
    )
    db.add(record)
    await db.flush()
    db.add(
        AuditLog(
            workspace_id=current_user.workspace_id,
            user_id=current_user.id,
            action="client_data.create",
            resource_type="client_data_record",
            resource_id=str(record.id),
            details={"type": record.type, "title": record.title},
            ip_address=request.client.host if request.client else None,
        )
    )
    await db.commit()
    return ClientDataRecordSchema.model_validate(record)


@router.patch("/{record_id}", response_model=ClientDataRecordSchema)
async def update_client_data(
    record_id: uuid.UUID,
    payload: ClientDataRecordUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ClientDataRecordSchema:
    result = await db.execute(
        select(ClientDataRecord).where(
            ClientDataRecord.id == record_id,
            ClientDataRecord.workspace_id == current_user.workspace_id,
        )
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")

    if payload.type is not None:
        record.type = payload.type
    if payload.title is not None:
        record.title = payload.title
    if payload.content is not None:
        record.content = payload.content
    if payload.metadata_ is not None:
        record.metadata_ = payload.metadata_

    db.add(
        AuditLog(
            workspace_id=current_user.workspace_id,
            user_id=current_user.id,
            action="client_data.update",
            resource_type="client_data_record",
            resource_id=str(record.id),
            details={"type": record.type, "title": record.title},
            ip_address=request.client.host if request.client else None,
        )
    )
    await db.commit()
    return ClientDataRecordSchema.model_validate(record)


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client_data(
    record_id: uuid.UUID,
    request: Request,
    confirmed: bool = Query(default=False, description="Must be true to confirm deletion"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    if not confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deletion requires confirmed=true query parameter",
        )

    result = await db.execute(
        select(ClientDataRecord).where(
            ClientDataRecord.id == record_id,
            ClientDataRecord.workspace_id == current_user.workspace_id,
        )
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")

    db.add(
        AuditLog(
            workspace_id=current_user.workspace_id,
            user_id=current_user.id,
            action="client_data.delete",
            resource_type="client_data_record",
            resource_id=str(record_id),
            details={"type": record.type, "title": record.title},
            ip_address=request.client.host if request.client else None,
        )
    )
    await db.delete(record)
    await db.commit()
