import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.runtime import run_agent
from app.core.deps import get_current_active_user
from app.database import get_db
from app.models.agent_run import AgentRun
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()


@router.post("", response_model=ChatResponse)
async def create_chat_run(
    payload: ChatRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    if payload.workspace_id != current_user.workspace_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Workspace access denied")

    run = AgentRun(
        id=uuid.uuid4(),
        workspace_id=current_user.workspace_id,
        user_id=current_user.id,
        status="pending",
        input_message=payload.message,
    )
    db.add(run)
    await db.commit()

    response_payload = await run_agent(
        message=payload.message,
        run_id=run.id,
        workspace_id=current_user.workspace_id,
        user_id=current_user.id,
        db=db,
    )

    db.add(
        AuditLog(
            workspace_id=current_user.workspace_id,
            user_id=current_user.id,
            action="chat.run",
            resource_type="agent_run",
            resource_id=str(run.id),
            details={"intent": response_payload.get("intent"), "status": response_payload.get("status")},
            ip_address=request.client.host if request.client else None,
        )
    )
    await db.commit()

    return ChatResponse(**response_payload)
