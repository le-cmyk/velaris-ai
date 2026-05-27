from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.auth import LoginRequest, TokenResponse

router = APIRouter()


async def ensure_demo_user(db: AsyncSession) -> None:
    existing_user = await db.scalar(select(User.id).limit(1))
    if existing_user is not None:
        return

    workspace = Workspace(
        name="Demo Workspace",
        slug="demo-workspace",
        description="Seed workspace for local development",
    )
    db.add(workspace)
    await db.flush()

    demo_user = User(
        workspace_id=workspace.id,
        email="demo@velaris.ai",
        hashed_password=hash_password("demo123"),
        full_name="Velaris Demo User",
        is_active=True,
        is_superuser=True,
    )
    db.add(demo_user)
    await db.commit()


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    await ensure_demo_user(db)

    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    access_token = create_access_token(
        data={"sub": str(user.id), "workspace_id": str(user.workspace_id), "email": user.email},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )

    db.add(
        AuditLog(
            workspace_id=user.workspace_id,
            user_id=user.id,
            action="auth.login",
            resource_type="user",
            resource_id=str(user.id),
            details={"email": user.email},
            ip_address=request.client.host if request.client else None,
        )
    )
    await db.commit()

    return TokenResponse(
        access_token=access_token,
        user_id=user.id,
        workspace_id=user.workspace_id,
        email=user.email,
    )
