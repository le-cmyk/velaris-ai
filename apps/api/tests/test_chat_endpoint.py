"""Integration-style tests for the /chat endpoint using TestClient."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from main import app


class TestChatEndpointBehavior:
    """Tests for POST /chat endpoint behavior."""

    @pytest.fixture()
    def client(self) -> TestClient:
        return TestClient(app)

    def test_health_endpoint_returns_ok(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data

    def test_chat_requires_auth(self, client: TestClient) -> None:
        """POST /chat without a token should return 401."""
        response = client.post(
            "/chat",
            json={"message": "show me all customers", "workspace_id": str(uuid.uuid4())},
        )
        assert response.status_code == 401

    def test_approvals_requires_auth(self, client: TestClient) -> None:
        """GET /approvals without a token should return 401."""
        response = client.get("/approvals")
        assert response.status_code == 401

    def test_audit_logs_requires_auth(self, client: TestClient) -> None:
        """GET /audit-logs without a token should return 401."""
        response = client.get("/audit-logs")
        assert response.status_code == 401

    def test_workspace_requires_auth(self, client: TestClient) -> None:
        """GET /workspace without a token should return 401."""
        response = client.get("/workspace")
        assert response.status_code == 401

    def test_tools_requires_auth(self, client: TestClient) -> None:
        """GET /tools without a token should return 401."""
        response = client.get("/tools")
        assert response.status_code == 401

    def test_login_with_bad_credentials_returns_401(self, client: TestClient) -> None:
        """Attempting login with non-existent user returns 401."""
        # Build a mock session: scalar() returns a sentinel (demo user "exists"),
        # execute() returns a result whose scalar_one_or_none() is None (wrong user).
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        async def mock_execute(*_args, **_kwargs):
            return mock_result

        mock_session = AsyncMock()
        mock_session.scalar = AsyncMock(return_value="some-id")  # ensure_demo_user short-circuits
        mock_session.execute = mock_execute
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()

        async def override_get_db():
            yield mock_session

        from app.database import get_db
        app.dependency_overrides[get_db] = override_get_db
        try:
            response = client.post(
                "/auth/login",
                json={"email": "nobody@example.com", "password": "wrong"},
            )
        finally:
            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 401
