from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.backend.dynamic_endpoints import execute_client_endpoint, resolve_client_endpoint
from app.models.client_endpoint import ClientEndpoint


def _mock_scalar_one(item: object | None):
    result = MagicMock()
    result.scalar_one_or_none.return_value = item
    return result


@pytest.mark.asyncio
async def test_resolve_client_endpoint_is_workspace_method_and_path_scoped() -> None:
    workspace_id = uuid.uuid4()
    endpoint = ClientEndpoint(
        id=uuid.uuid4(),
        workspace_id=workspace_id,
        created_by_id=uuid.uuid4(),
        name="Customers API",
        method="GET",
        path="/customers",
        mode="data_query",
        config={"table": "customers"},
        is_active=True,
    )
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_mock_scalar_one(endpoint))

    resolved = await resolve_client_endpoint(
        db,
        workspace_id=workspace_id,
        method="GET",
        path="customers",
    )

    assert resolved is endpoint
    executed_query = str(db.execute.call_args.args[0])
    assert "client_endpoints.workspace_id" in executed_query
    assert "client_endpoints.method" in executed_query
    assert "client_endpoints.path" in executed_query


@pytest.mark.asyncio
async def test_resolve_client_endpoint_returns_404_for_unknown_endpoint() -> None:
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_mock_scalar_one(None))

    with pytest.raises(HTTPException, match="Client endpoint not found"):
        await resolve_client_endpoint(
            db,
            workspace_id=uuid.uuid4(),
            method="GET",
            path="/missing",
        )


@pytest.mark.asyncio
async def test_execute_data_query_endpoint_uses_endpoint_config_and_query_params() -> None:
    endpoint = ClientEndpoint(
        id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        name="Active customers",
        method="GET",
        path="/customers",
        mode="data_query",
        config={
            "table": "customers",
            "select": ["id", "name", "status"],
            "filters": [{"field": "status", "op": "eq", "value": "active"}],
            "allowed_filter_fields": ["country"],
            "limit": 25,
        },
        is_active=True,
    )
    user = SimpleNamespace(id=uuid.uuid4(), workspace_id=endpoint.workspace_id)
    request = MagicMock()
    request.query_params.get.side_effect = lambda key, default=None: {"country": None}.get(key, default)
    request.query_params.multi_items.return_value = [("country", "US")]
    request.client.host = "127.0.0.1"
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()

    with patch(
        "app.backend.dynamic_endpoints.execute_data_query",
        new=AsyncMock(return_value=SimpleNamespace(model_dump=lambda mode: {"rows": [], "row_count": 0})),
    ) as execute_data_query:
        result = await execute_client_endpoint(db, endpoint=endpoint, current_user=user, request=request)

    assert result == {"rows": [], "row_count": 0}
    data_request = execute_data_query.call_args.kwargs["request"]
    assert data_request.table == "customers"
    assert [filter_.field for filter_ in data_request.filters] == ["status", "country"]
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_execute_client_data_create_endpoint_creates_record() -> None:
    endpoint = ClientEndpoint(
        id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        name="Create leads",
        method="POST",
        path="/leads",
        mode="client_data_create",
        config={"type": "lead", "title_field": "company"},
        is_active=True,
    )
    user = SimpleNamespace(id=uuid.uuid4(), workspace_id=endpoint.workspace_id)
    request = MagicMock()
    request.json = AsyncMock(return_value={"company": "Acme", "source": "website"})
    request.client.host = "127.0.0.1"
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()

    result = await execute_client_endpoint(db, endpoint=endpoint, current_user=user, request=request)

    assert result["type"] == "lead"
    assert result["title"] == "Acme"
    assert result["metadata"] == {"company": "Acme", "source": "website"}
    db.flush.assert_awaited_once()
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_execute_agent_task_endpoint_dispatches_request_to_agent() -> None:
    endpoint = ClientEndpoint(
        id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        name="Smart Support API",
        method="POST",
        path="/support/triage",
        mode="agent_task",
        config={
            "instruction": "Triage support requests and create the right records.",
            "allowed_tools": ["data_query", "client_data_create"],
        },
        is_active=True,
    )
    user = SimpleNamespace(id=uuid.uuid4(), workspace_id=endpoint.workspace_id)
    request = MagicMock()
    request.method = "POST"
    request.query_params = {"priority": "high"}
    request.json = AsyncMock(return_value={"subject": "Login broken"})
    request.client.host = "127.0.0.1"
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()

    with patch(
        "app.backend.dynamic_endpoints.run_agent",
        new=AsyncMock(return_value={
            "status": "completed",
            "message": {"ticket_id": "t_123"},
            "intent": "database_write_request",
            "tool_calls": [],
            "pending_approvals": [],
        }),
    ) as run_agent:
        result = await execute_client_endpoint(db, endpoint=endpoint, current_user=user, request=request)

    assert result["status"] == "completed"
    assert result["message"] == {"ticket_id": "t_123"}
    agent_message = run_agent.call_args.kwargs["message"]
    assert "Endpoint: POST /support/triage" in agent_message
    assert "Login broken" in agent_message
    assert "Triage support requests" in agent_message
