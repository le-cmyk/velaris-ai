"""Unit tests for the SQL safety checker in the Tool Gateway."""

import pytest

from app.gateway.tool_gateway import RISKY_SQL_KEYWORDS, SAFE_SQL_PATTERN, ToolGateway
from app.mcp.interface import MCPInterface


def make_gateway() -> ToolGateway:
    """Create a ToolGateway with a minimal config for testing."""
    config = {
        "tools": {
            "postgres_query": {
                "enabled": True,
                "description": "Execute SQL",
                "requires_approval": True,
            }
        }
    }
    return ToolGateway(client_config=config, mcp_interface=MCPInterface())


class TestSqlSafetyChecker:
    """Tests for ToolGateway.is_sql_safe and sql_requires_approval."""

    def setup_method(self) -> None:
        self.gateway = make_gateway()

    # --- is_sql_safe ---

    def test_select_is_safe(self) -> None:
        assert self.gateway.is_sql_safe("SELECT id, name FROM users") is True

    def test_select_with_leading_whitespace(self) -> None:
        assert self.gateway.is_sql_safe("  SELECT * FROM customers") is True

    def test_select_case_insensitive(self) -> None:
        assert self.gateway.is_sql_safe("select * FROM orders") is True

    def test_insert_is_not_safe(self) -> None:
        assert self.gateway.is_sql_safe("INSERT INTO users (name) VALUES ('Alice')") is False

    def test_update_is_not_safe(self) -> None:
        assert self.gateway.is_sql_safe("UPDATE users SET name='Bob' WHERE id=1") is False

    def test_delete_is_not_safe(self) -> None:
        assert self.gateway.is_sql_safe("DELETE FROM users WHERE id=1") is False

    def test_drop_is_not_safe(self) -> None:
        assert self.gateway.is_sql_safe("DROP TABLE users") is False

    def test_empty_string_is_not_safe(self) -> None:
        assert self.gateway.is_sql_safe("") is False

    def test_arbitrary_text_is_not_safe(self) -> None:
        assert self.gateway.is_sql_safe("show tables") is False

    # --- sql_requires_approval ---

    def test_select_does_not_require_approval(self) -> None:
        assert self.gateway.sql_requires_approval("SELECT * FROM users") is False

    def test_insert_requires_approval(self) -> None:
        assert self.gateway.sql_requires_approval("INSERT INTO users VALUES (1, 'x')") is True

    def test_update_requires_approval(self) -> None:
        assert self.gateway.sql_requires_approval("UPDATE users SET name='y' WHERE id=1") is True

    def test_delete_requires_approval(self) -> None:
        assert self.gateway.sql_requires_approval("DELETE FROM users") is True

    def test_drop_requires_approval(self) -> None:
        assert self.gateway.sql_requires_approval("DROP TABLE users") is True

    def test_alter_requires_approval(self) -> None:
        assert self.gateway.sql_requires_approval("ALTER TABLE users ADD COLUMN age INT") is True

    def test_truncate_requires_approval(self) -> None:
        assert self.gateway.sql_requires_approval("TRUNCATE users") is True

    def test_case_insensitive_detection(self) -> None:
        assert self.gateway.sql_requires_approval("insert into users values (1)") is True
        assert self.gateway.sql_requires_approval("Delete from users where id=2") is True
