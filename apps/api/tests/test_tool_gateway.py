"""Unit tests for Tool Gateway approval logic."""

import pytest

from app.gateway.tool_gateway import ToolGateway
from app.mcp.interface import MCPInterface


def make_gateway(readonly: bool = True) -> ToolGateway:
    config = {
        "security": {"readonly_by_default": readonly},
        "tools": {
            "postgres_query": {
                "enabled": True,
                "description": "Execute SQL",
                "requires_approval": True,
            },
            "disabled_tool": {
                "enabled": False,
                "description": "A disabled tool",
                "requires_approval": False,
            },
        },
    }
    return ToolGateway(client_config=config, mcp_interface=MCPInterface())


class TestToolGatewayApprovalLogic:
    """Tests for ToolGateway.validate_tool_call."""

    def setup_method(self) -> None:
        self.gateway = make_gateway()

    # --- validate_tool_call: happy paths ---

    def test_valid_postgres_query_accepted(self) -> None:
        """A configured, enabled tool with a valid query should not raise."""
        self.gateway.validate_tool_call("postgres_query", {"query": "SELECT 1"})

    # --- validate_tool_call: error paths ---

    def test_unknown_tool_raises(self) -> None:
        with pytest.raises(ValueError, match="not configured"):
            self.gateway.validate_tool_call("unknown_tool", {})

    def test_disabled_tool_raises(self) -> None:
        with pytest.raises(ValueError, match="disabled"):
            self.gateway.validate_tool_call("disabled_tool", {})

    def test_postgres_query_without_query_key_raises(self) -> None:
        with pytest.raises(ValueError, match="SQL query"):
            self.gateway.validate_tool_call("postgres_query", {})

    def test_postgres_query_with_empty_query_raises(self) -> None:
        with pytest.raises(ValueError, match="SQL query"):
            self.gateway.validate_tool_call("postgres_query", {"query": ""})

    # --- approval decision helpers ---

    def test_select_does_not_need_approval(self) -> None:
        assert self.gateway.sql_requires_approval("SELECT * FROM orders") is False

    def test_write_queries_need_approval(self) -> None:
        write_queries = [
            "INSERT INTO t VALUES (1)",
            "UPDATE t SET x=1",
            "DELETE FROM t",
            "DROP TABLE t",
            "ALTER TABLE t ADD COLUMN y INT",
            "TRUNCATE t",
        ]
        for q in write_queries:
            assert self.gateway.sql_requires_approval(q) is True, f"Expected approval for: {q}"

    def test_is_sql_safe_for_select(self) -> None:
        assert self.gateway.is_sql_safe("SELECT id FROM users LIMIT 10") is True

    def test_is_sql_safe_false_for_non_select(self) -> None:
        assert self.gateway.is_sql_safe("CALL some_procedure()") is False
