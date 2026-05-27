"""Unit tests for audit log model and ToolGateway audit log creation."""

from __future__ import annotations

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.gateway.tool_gateway import ToolGateway
from app.mcp.interface import MCPInterface
from app.mcp.tools.postgres_query import PostgresQueryTool


class TestAuditLogCreation:
    """Tests verifying that _add_audit_log writes the expected record."""

    def _make_gateway(self) -> ToolGateway:
        config = {
            "tools": {
                "postgres_query": {"enabled": True, "description": "SQL", "requires_approval": True}
            }
        }
        mcp = MCPInterface()
        mcp.register_tool("postgres_query", PostgresQueryTool())
        return ToolGateway(client_config=config, mcp_interface=mcp)

    @pytest.mark.asyncio
    async def test_audit_log_is_added_on_safe_query(self) -> None:
        """Executing a SELECT query should create at least two audit log entries
        (tool_call.requested and tool_call.executed)."""
        gateway = self._make_gateway()

        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.commit = AsyncMock()
        db.get = AsyncMock(return_value=None)

        workspace_id = uuid.uuid4()
        run_id = uuid.uuid4()
        user_id = uuid.uuid4()

        await gateway.execute(
            tool_name="postgres_query",
            arguments={"query": "SELECT id FROM users LIMIT 5"},
            run_id=run_id,
            workspace_id=workspace_id,
            user_id=user_id,
            db=db,
        )

        # db.add should have been called at least twice:
        # once for ToolCall and at least once for each AuditLog
        assert db.add.call_count >= 2

    @pytest.mark.asyncio
    async def test_audit_log_action_for_risky_query(self) -> None:
        """A risky SQL query should log tool_call.requested and tool_call.pending_approval."""
        from app.models.audit_log import AuditLog

        gateway = self._make_gateway()

        added_objects: list = []

        db = AsyncMock()
        db.add = MagicMock(side_effect=lambda obj: added_objects.append(obj))
        db.flush = AsyncMock()
        db.commit = AsyncMock()

        workspace_id = uuid.uuid4()
        run_id = uuid.uuid4()
        user_id = uuid.uuid4()

        result = await gateway.execute(
            tool_name="postgres_query",
            arguments={"query": "DELETE FROM users WHERE id=1"},
            run_id=run_id,
            workspace_id=workspace_id,
            user_id=user_id,
            db=db,
        )

        assert result["status"] == "pending_approval"

        audit_log_actions = [
            obj.action for obj in added_objects if isinstance(obj, AuditLog)
        ]
        assert "tool_call.requested" in audit_log_actions
        assert "tool_call.pending_approval" in audit_log_actions


class TestPostgresQueryToolMock:
    """Tests for the mock PostgreSQL tool."""

    @pytest.mark.asyncio
    async def test_customer_query_returns_rows(self) -> None:
        tool = PostgresQueryTool()
        result = await tool.execute({"query": "SELECT id FROM customers LIMIT 3"})
        assert "rows" in result
        assert result["row_count"] > 0

    @pytest.mark.asyncio
    async def test_orders_query_returns_rows(self) -> None:
        tool = PostgresQueryTool()
        result = await tool.execute({"query": "SELECT id, amount FROM orders"})
        assert "rows" in result
        assert "columns" in result

    @pytest.mark.asyncio
    async def test_generic_query_returns_success(self) -> None:
        tool = PostgresQueryTool()
        result = await tool.execute({"query": "SELECT 1"})
        assert result["row_count"] >= 1

    def test_tool_info_has_required_keys(self) -> None:
        tool = PostgresQueryTool()
        info = tool.get_info()
        assert "name" in info
        assert "description" in info
        assert "requires_approval" in info
        assert info["name"] == "postgres_query"
