import re
import uuid
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
from app.schemas.auth import LoginRequest, SignupRequest, TokenResponse
from app.seeds.fake_data import seed_workspace_data as seed_fake_client_data

router = APIRouter()


def _slugify(text: str) -> str:
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = slug.strip("-")
    return slug or "workspace"


async def _unique_slug(base: str, db: AsyncSession) -> str:
    slug = base
    suffix = 0
    while True:
        existing = await db.scalar(select(Workspace.id).where(Workspace.slug == slug).limit(1))
        if existing is None:
            return slug
        suffix += 1
        slug = f"{base}-{suffix}"


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


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    payload: SignupRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    existing = await db.scalar(select(User.id).where(User.email == payload.email).limit(1))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    workspace_display = payload.workspace_name.strip() or payload.email.split("@")[0]
    base_slug = _slugify(workspace_display)
    slug = await _unique_slug(base_slug, db)

    workspace = Workspace(
        id=uuid.uuid4(),
        name=workspace_display,
        slug=slug,
        description=None,
    )
    db.add(workspace)
    await db.flush()

    user = User(
        id=uuid.uuid4(),
        workspace_id=workspace.id,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name.strip() or payload.email.split("@")[0],
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    await db.flush()

    await seed_fake_client_data(workspace.id, db)

    db.add(
        AuditLog(
            workspace_id=workspace.id,
            user_id=user.id,
            action="auth.signup",
            resource_type="user",
            resource_id=str(user.id),
            details={"email": user.email},
            ip_address=request.client.host if request.client else None,
        )
    )
    await db.commit()

    access_token = create_access_token(
        data={"sub": str(user.id), "workspace_id": str(workspace.id), "email": user.email},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )

    return TokenResponse(
        access_token=access_token,
        user_id=user.id,
        workspace_id=workspace.id,
        email=user.email,
    )
