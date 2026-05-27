from datetime import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user
from app.database import get_db
from app.gateway.tool_gateway import tool_gateway
from app.models.approval import ApprovalRequest
from app.models.audit_log import AuditLog
from app.models.tool_call import ToolCall
from app.models.user import User
from app.schemas.approval import ApprovalDecision, ApprovalRequestSchema

router = APIRouter()


@router.get("", response_model=list[ApprovalRequestSchema])
async def list_pending_approvals(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[ApprovalRequestSchema]:
    result = await db.execute(
        select(ApprovalRequest).where(
            ApprovalRequest.workspace_id == current_user.workspace_id,
            ApprovalRequest.status == "pending",
        )
    )
    approvals = result.scalars().all()
    return [ApprovalRequestSchema.model_validate(item) for item in approvals]


@router.post("/{approval_id}/approve")
async def approve_action(
    approval_id: uuid.UUID,
    decision: ApprovalDecision,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if decision.decision != "approve":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Decision must be 'approve'")

    result = await db.execute(
        select(ApprovalRequest).where(
            ApprovalRequest.id == approval_id,
            ApprovalRequest.workspace_id == current_user.workspace_id,
        )
    )
    approval = result.scalar_one_or_none()
    if approval is None or approval.status != "pending":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval request not found")

    tool_call = await db.get(ToolCall, approval.tool_call_id)
    if tool_call is None or tool_call.workspace_id != current_user.workspace_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool call not found")

    approval.status = "approved"
    approval.reason = decision.reason
    approval.decided_by = current_user.id
    approval.decided_at = datetime.utcnow()

    execution = await tool_gateway.execute_approved_tool_call(
        tool_call=tool_call,
        approval=approval,
        workspace_id=current_user.workspace_id,
        user_id=current_user.id,
        db=db,
    )

    db.add(
        AuditLog(
            workspace_id=current_user.workspace_id,
            user_id=current_user.id,
            action="approval.approved",
            resource_type="approval_request",
            resource_id=str(approval.id),
            details={"tool_call_id": str(tool_call.id), "result_status": execution.get("status")},
            ip_address=request.client.host if request.client else None,
        )
    )
    await db.commit()
    return {"approval_id": str(approval.id), "status": approval.status, "execution": execution}


@router.post("/{approval_id}/reject")
async def reject_action(
    approval_id: uuid.UUID,
    decision: ApprovalDecision,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if decision.decision != "reject":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Decision must be 'reject'")

    result = await db.execute(
        select(ApprovalRequest).where(
            ApprovalRequest.id == approval_id,
            ApprovalRequest.workspace_id == current_user.workspace_id,
        )
    )
    approval = result.scalar_one_or_none()
    if approval is None or approval.status != "pending":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval request not found")

    tool_call = await db.get(ToolCall, approval.tool_call_id)
    if tool_call is None or tool_call.workspace_id != current_user.workspace_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool call not found")

    approval.status = "rejected"
    approval.reason = decision.reason
    approval.decided_by = current_user.id
    approval.decided_at = datetime.utcnow()
    tool_call.status = "rejected"
    tool_call.error = decision.reason or "Rejected by approver"

    db.add(
        AuditLog(
            workspace_id=current_user.workspace_id,
            user_id=current_user.id,
            action="approval.rejected",
            resource_type="approval_request",
            resource_id=str(approval.id),
            details={"tool_call_id": str(tool_call.id), "reason": decision.reason},
            ip_address=request.client.host if request.client else None,
        )
    )
    await db.commit()
    return {"approval_id": str(approval.id), "status": approval.status}
