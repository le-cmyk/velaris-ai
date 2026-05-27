import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user
from app.database import get_db
from app.models.agent_run import AgentRun
from app.models.tool_call import ToolCall
from app.models.user import User

router = APIRouter()


@router.get("/{run_id}")
async def get_run(
    run_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get details of a specific agent run, including its tool calls."""
    run = await db.get(AgentRun, run_id)
    if run is None or run.workspace_id != current_user.workspace_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")

    tool_calls_result = await db.execute(
        select(ToolCall).where(ToolCall.run_id == run_id).order_by(ToolCall.created_at)
    )
    tool_calls = tool_calls_result.scalars().all()

    return {
        "id": str(run.id),
        "workspace_id": str(run.workspace_id),
        "user_id": str(run.user_id),
        "status": run.status,
        "intent": run.intent,
        "input_message": run.input_message,
        "output_message": run.output_message,
        "execution_plan": run.execution_plan,
        "created_at": run.created_at.isoformat(),
        "tool_calls": [
            {
                "id": str(tc.id),
                "tool_name": tc.tool_name,
                "arguments": tc.arguments,
                "status": tc.status,
                "result": tc.result,
                "error": tc.error,
                "requires_approval": tc.requires_approval,
                "created_at": tc.created_at.isoformat(),
            }
            for tc in tool_calls
        ],
    }
