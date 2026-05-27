from __future__ import annotations

import uuid
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.database import get_db
from app.gateway.tool_gateway import ToolGateway
from app.mcp.interface import MCPInterface
from app.mcp.tools.postgres_query import PostgresQueryTool
from main import app


def _mock_result(items: list[object]):
    result = MagicMock()
    result.scalars.return_value.all.return_value = items
    return result


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def fake_user() -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        email="demo@velaris.ai",
        is_active=True,
    )


def _override_auth_user(user: SimpleNamespace) -> None:
    from app.core.deps import get_current_active_user

    async def _override():
        return user

    app.dependency_overrides[get_current_active_user] = _override


def _clear_overrides() -> None:
    app.dependency_overrides.clear()


class TestApiEndpointCoverage:
    def test_api_health_route_exists(self, client: TestClient) -> None:
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_login_success_returns_jwt(self, client: TestClient) -> None:
        workspace_id = uuid.uuid4()
        user_id = uuid.uuid4()
        mock_user = SimpleNamespace(
            id=user_id,
            workspace_id=workspace_id,
            email="demo@velaris.ai",
            hashed_password=hash_password("demo123"),
        )
        result = MagicMock()
        result.scalar_one_or_none.return_value = mock_user
        mock_session = AsyncMock()
        mock_session.scalar = AsyncMock(return_value=user_id)
        mock_session.execute = AsyncMock(return_value=result)
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()

        async def override_get_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_get_db
        try:
            response = client.post("/auth/login", json={"email": "demo@velaris.ai", "password": "demo123"})
        finally:
            _clear_overrides()

        assert response.status_code == 200
        payload = response.json()
        assert payload["token_type"] == "bearer"
        assert payload["access_token"]

    def test_chat_endpoint_success(self, client: TestClient, fake_user: SimpleNamespace) -> None:
        _override_auth_user(fake_user)
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()

        async def override_get_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_get_db
        with patch("app.routers.chat.run_agent", new=AsyncMock(return_value={
            "run_id": str(uuid.uuid4()),
            "message": "ok",
            "intent": "database_read",
            "execution_plan": {"steps": []},
            "tool_calls": [],
            "pending_approvals": [],
            "status": "completed",
        })):
            try:
                response = client.post(
                    "/chat",
                    json={"message": "show users", "workspace_id": str(fake_user.workspace_id)},
                )
            finally:
                _clear_overrides()

        assert response.status_code == 200
        assert response.json()["status"] == "completed"

    def test_chat_workspace_isolation(self, client: TestClient, fake_user: SimpleNamespace) -> None:
        _override_auth_user(fake_user)
        mock_session = AsyncMock()

        async def override_get_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_get_db
        try:
            response = client.post(
                "/chat",
                json={"message": "show users", "workspace_id": str(uuid.uuid4())},
            )
        finally:
            _clear_overrides()

        assert response.status_code == 403

    def test_get_run(self, client: TestClient, fake_user: SimpleNamespace) -> None:
        run_id = uuid.uuid4()
        run = SimpleNamespace(
            id=run_id,
            workspace_id=fake_user.workspace_id,
            user_id=fake_user.id,
            status="completed",
            intent="database_read",
            input_message="show users",
            output_message="done",
            execution_plan={"steps": []},
            created_at=datetime.utcnow(),
        )
        tool_call = SimpleNamespace(
            id=uuid.uuid4(),
            tool_name="postgres_query",
            arguments={"query": "SELECT 1"},
            status="executed",
            result={"row_count": 1},
            error=None,
            requires_approval=False,
            created_at=datetime.utcnow(),
        )
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=run)
        mock_session.execute = AsyncMock(return_value=_mock_result([tool_call]))
        _override_auth_user(fake_user)

        async def override_get_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_get_db
        try:
            response = client.get(f"/runs/{run_id}")
        finally:
            _clear_overrides()

        assert response.status_code == 200
        assert response.json()["id"] == str(run_id)

    def test_get_approvals(self, client: TestClient, fake_user: SimpleNamespace) -> None:
        approval = SimpleNamespace(
            id=uuid.uuid4(),
            run_id=uuid.uuid4(),
            tool_call_id=uuid.uuid4(),
            requested_action="DELETE FROM users",
            reason="approval required",
            status="pending",
            created_at=datetime.utcnow(),
            workspace_id=fake_user.workspace_id,
        )
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=_mock_result([approval]))
        _override_auth_user(fake_user)

        async def override_get_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_get_db
        try:
            response = client.get("/approvals")
        finally:
            _clear_overrides()

        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_approve_approval(self, client: TestClient, fake_user: SimpleNamespace) -> None:
        approval_id = uuid.uuid4()
        tool_call_id = uuid.uuid4()
        approval = SimpleNamespace(
            id=approval_id,
            workspace_id=fake_user.workspace_id,
            status="pending",
            tool_call_id=tool_call_id,
            reason=None,
            decided_by=None,
            decided_at=None,
        )
        tool_call = SimpleNamespace(id=tool_call_id, workspace_id=fake_user.workspace_id, status="pending", error=None)
        result = MagicMock()
        result.scalar_one_or_none.return_value = approval
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=result)
        mock_session.get = AsyncMock(return_value=tool_call)
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        _override_auth_user(fake_user)

        async def override_get_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_get_db
        with patch(
            "app.routers.approvals.tool_gateway.execute_approved_tool_call",
            new=AsyncMock(return_value={"status": "executed"}),
        ):
            try:
                response = client.post(
                    f"/approvals/{approval_id}/approve",
                    json={"decision": "approve", "reason": "safe"},
                )
            finally:
                _clear_overrides()

        assert response.status_code == 200
        assert response.json()["status"] == "approved"

    def test_reject_approval(self, client: TestClient, fake_user: SimpleNamespace) -> None:
        approval_id = uuid.uuid4()
        tool_call_id = uuid.uuid4()
        approval = SimpleNamespace(
            id=approval_id,
            workspace_id=fake_user.workspace_id,
            status="pending",
            tool_call_id=tool_call_id,
            reason=None,
            decided_by=None,
            decided_at=None,
        )
        tool_call = SimpleNamespace(id=tool_call_id, workspace_id=fake_user.workspace_id, status="pending", error=None)
        result = MagicMock()
        result.scalar_one_or_none.return_value = approval
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=result)
        mock_session.get = AsyncMock(return_value=tool_call)
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        _override_auth_user(fake_user)

        async def override_get_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_get_db
        try:
            response = client.post(
                f"/approvals/{approval_id}/reject",
                json={"decision": "reject", "reason": "blocked"},
            )
        finally:
            _clear_overrides()

        assert response.status_code == 200
        assert response.json()["status"] == "rejected"

    def test_audit_logs(self, client: TestClient, fake_user: SimpleNamespace) -> None:
        log = SimpleNamespace(
            id=uuid.uuid4(),
            action="tool_call.requested",
            resource_type="tool_call",
            resource_id="abc",
            details={"k": "v"},
            created_at=datetime.utcnow(),
        )
        mock_session = AsyncMock()
        mock_session.scalar = AsyncMock(return_value=1)
        mock_session.execute = AsyncMock(return_value=_mock_result([log]))
        _override_auth_user(fake_user)

        async def override_get_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_get_db
        try:
            response = client.get("/audit-logs")
        finally:
            _clear_overrides()

        assert response.status_code == 200
        assert response.json()["total"] == 1

    def test_tools(self, client: TestClient, fake_user: SimpleNamespace) -> None:
        _override_auth_user(fake_user)
        with patch(
            "app.routers.tools.tool_gateway.list_tools",
            new=AsyncMock(return_value=[{"name": "postgres_query", "description": "SQL", "requires_approval": True, "enabled": True}]),
        ):
            try:
                response = client.get("/tools")
            finally:
                _clear_overrides()

        assert response.status_code == 200
        assert response.json()["tools"][0]["name"] == "postgres_query"


class TestGatewayExecutionBehavior:
    @pytest.mark.asyncio
    async def test_database_read_query_executes_without_approval(self) -> None:
        gateway = ToolGateway(
            client_config={"tools": {"postgres_query": {"enabled": True, "description": "SQL", "requires_approval": True}}},
            mcp_interface=MCPInterface(),
        )
        gateway.mcp_interface.register_tool("postgres_query", PostgresQueryTool())
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.commit = AsyncMock()
        result = await gateway.execute(
            tool_name="postgres_query",
            arguments={"query": "SELECT id FROM users LIMIT 1"},
            run_id=uuid.uuid4(),
            workspace_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            db=db,
        )
        assert result["status"] == "executed"

    @pytest.mark.asyncio
    async def test_database_write_query_requires_approval(self) -> None:
        gateway = ToolGateway(
            client_config={"tools": {"postgres_query": {"enabled": True, "description": "SQL", "requires_approval": True}}},
            mcp_interface=MCPInterface(),
        )
        gateway.mcp_interface.register_tool("postgres_query", PostgresQueryTool())
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.commit = AsyncMock()
        result = await gateway.execute(
            tool_name="postgres_query",
            arguments={"query": "UPDATE users SET full_name='x'"},
            run_id=uuid.uuid4(),
            workspace_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            db=db,
        )
        assert result["status"] == "pending_approval"

    @pytest.mark.asyncio
    async def test_unknown_tool_is_blocked(self) -> None:
        gateway = ToolGateway(client_config={"tools": {}}, mcp_interface=MCPInterface())
        db = AsyncMock()
        with pytest.raises(ValueError, match="not configured"):
            await gateway.execute(
                tool_name="unknown_tool",
                arguments={},
                run_id=uuid.uuid4(),
                workspace_id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                db=db,
            )
