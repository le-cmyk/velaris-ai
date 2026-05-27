from __future__ import annotations

import re
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import client_config
from app.mcp.interface import MCPInterface
from app.mcp.tools.postgres_query import PostgresQueryTool
from app.models.approval import ApprovalRequest
from app.models.audit_log import AuditLog
from app.models.tool_call import ToolCall

SAFE_SQL_PATTERN = re.compile(r"^\s*SELECT\b", re.IGNORECASE)
RISKY_SQL_KEYWORDS = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE"]


class ToolGateway:
    def __init__(self, client_config: dict[str, Any], mcp_interface: MCPInterface):
        self.config = client_config
        self.mcp_interface = mcp_interface

    def is_sql_safe(self, query: str) -> bool:
        return bool(SAFE_SQL_PATTERN.match(query.strip()))

    def sql_requires_approval(self, query: str) -> bool:
        upper = query.upper()
        return any(keyword in upper for keyword in RISKY_SQL_KEYWORDS)

    def validate_tool_call(self, tool_name: str, arguments: dict[str, Any]) -> None:
        tool_config = self.config.get("tools", {}).get(tool_name)
        if tool_config is None:
            raise ValueError(f"Tool '{tool_name}' is not configured")
        if not tool_config.get("enabled", False):
            raise ValueError(f"Tool '{tool_name}' is disabled")
        if tool_name == "postgres_query" and not arguments.get("query"):
            raise ValueError("The postgres_query tool requires a SQL query")

    async def _add_audit_log(
        self,
        db: AsyncSession,
        *,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID | None,
        action: str,
        resource_type: str,
        resource_id: str | None,
        details: dict[str, Any] | None = None,
    ) -> None:
        db.add(
            AuditLog(
                workspace_id=workspace_id,
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
            )
        )
        await db.flush()

    async def list_tools(self) -> list[dict[str, Any]]:
        registered_tools = {tool["name"]: tool for tool in await self.mcp_interface.list_tools()}
        tools: list[dict[str, Any]] = []
        for name, config in self.config.get("tools", {}).items():
            info = registered_tools.get(name, {})
            tools.append(
                {
                    "name": name,
                    "description": config.get("description") or info.get("description", ""),
                    "requires_approval": config.get("requires_approval", info.get("requires_approval", False)),
                    "enabled": config.get("enabled", False),
                }
            )
        return tools

    async def execute(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        run_id: uuid.UUID,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
        db: AsyncSession,
    ) -> dict[str, Any]:
        self.validate_tool_call(tool_name, arguments)

        query = arguments.get("query", "")
        requires_approval = False
        tool_call = ToolCall(
            run_id=run_id,
            workspace_id=workspace_id,
            tool_name=tool_name,
            arguments=arguments,
            requires_approval=False,
            status="pending",
        )
        db.add(tool_call)
        await db.flush()
        await self._add_audit_log(
            db,
            workspace_id=workspace_id,
            user_id=user_id,
            action="tool_call.requested",
            resource_type="tool_call",
            resource_id=str(tool_call.id),
            details={"tool_name": tool_name, "arguments": arguments},
        )

        if tool_name == "postgres_query":
            if self.sql_requires_approval(query):
                requires_approval = True
                tool_call.requires_approval = True
                approval = ApprovalRequest(
                    workspace_id=workspace_id,
                    run_id=run_id,
                    tool_call_id=tool_call.id,
                    status="pending",
                    requested_action=query,
                    reason="SQL write operations require explicit approval",
                )
                db.add(approval)
                await db.flush()
                await self._add_audit_log(
                    db,
                    workspace_id=workspace_id,
                    user_id=user_id,
                    action="tool_call.pending_approval",
                    resource_type="approval_request",
                    resource_id=str(approval.id),
                    details={"tool_call_id": str(tool_call.id)},
                )
                await db.commit()
                return {
                    "status": "pending_approval",
                    "result": None,
                    "approval_id": str(approval.id),
                    "tool_call_id": str(tool_call.id),
                    "requires_approval": requires_approval,
                }
            if not self.is_sql_safe(query):
                tool_call.status = "blocked"
                tool_call.error = "Only SELECT queries are allowed without approval"
                await self._add_audit_log(
                    db,
                    workspace_id=workspace_id,
                    user_id=user_id,
                    action="tool_call.blocked",
                    resource_type="tool_call",
                    resource_id=str(tool_call.id),
                    details={"reason": tool_call.error},
                )
                await db.commit()
                return {
                    "status": "blocked",
                    "result": None,
                    "tool_call_id": str(tool_call.id),
                    "requires_approval": False,
                }

        try:
            result = await self.mcp_interface.call_tool(tool_name, arguments)
            tool_call.status = "executed"
            tool_call.result = result
            await self._add_audit_log(
                db,
                workspace_id=workspace_id,
                user_id=user_id,
                action="tool_call.executed",
                resource_type="tool_call",
                resource_id=str(tool_call.id),
                details={"tool_name": tool_name},
            )
            await db.commit()
            return {
                "status": "executed",
                "result": result,
                "tool_call_id": str(tool_call.id),
                "requires_approval": requires_approval,
            }
        except Exception as exc:
            tool_call.status = "failed"
            tool_call.error = str(exc)
            await self._add_audit_log(
                db,
                workspace_id=workspace_id,
                user_id=user_id,
                action="tool_call.failed",
                resource_type="tool_call",
                resource_id=str(tool_call.id),
                details={"error": str(exc)},
            )
            await db.commit()
            return {
                "status": "failed",
                "result": None,
                "tool_call_id": str(tool_call.id),
                "requires_approval": requires_approval,
            }

    async def execute_approved_tool_call(
        self,
        *,
        tool_call: ToolCall,
        approval: ApprovalRequest,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
        db: AsyncSession,
    ) -> dict[str, Any]:
        tool_call.status = "approved"
        await db.flush()
        try:
            result = await self.mcp_interface.call_tool(tool_call.tool_name, tool_call.arguments)
            tool_call.status = "executed"
            tool_call.result = result
            await self._add_audit_log(
                db,
                workspace_id=workspace_id,
                user_id=user_id,
                action="tool_call.executed_after_approval",
                resource_type="tool_call",
                resource_id=str(tool_call.id),
                details={"approval_id": str(approval.id)},
            )
            return {"status": "executed", "result": result}
        except Exception as exc:
            tool_call.status = "failed"
            tool_call.error = str(exc)
            await self._add_audit_log(
                db,
                workspace_id=workspace_id,
                user_id=user_id,
                action="tool_call.failed_after_approval",
                resource_type="tool_call",
                resource_id=str(tool_call.id),
                details={"approval_id": str(approval.id), "error": str(exc)},
            )
            return {"status": "failed", "result": None, "error": str(exc)}


mcp_interface = MCPInterface()
mcp_interface.register_tool("postgres_query", PostgresQueryTool())
tool_gateway = ToolGateway(client_config=client_config, mcp_interface=mcp_interface)
