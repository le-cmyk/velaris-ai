from __future__ import annotations

import uuid
from typing import Any

from fastapi import HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.runtime import run_agent
from app.data.catalog import execute_data_query
from app.models.agent_run import AgentRun
from app.models.audit_log import AuditLog
from app.models.client_data import ClientDataRecord
from app.models.client_endpoint import ClientEndpoint
from app.models.user import User
from app.schemas.data_backend import DataFilter, DataQueryRequest, DataSort


def normalize_client_endpoint_path(path: str) -> str:
    normalized = "/" + path.strip().strip("/")
    if normalized == "/":
        raise HTTPException(status_code=400, detail="Endpoint path cannot be root")
    return normalized


async def resolve_client_endpoint(
    db: AsyncSession,
    *,
    workspace_id: uuid.UUID,
    method: str,
    path: str,
) -> ClientEndpoint:
    result = await db.execute(
        select(ClientEndpoint).where(
            ClientEndpoint.workspace_id == workspace_id,
            ClientEndpoint.method == method.upper(),
            ClientEndpoint.path == normalize_client_endpoint_path(path),
            ClientEndpoint.is_active.is_(True),
        )
    )
    endpoint = result.scalar_one_or_none()
    if endpoint is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client endpoint not found")
    return endpoint


def _query_filters_from_request(endpoint: ClientEndpoint, request: Request) -> list[DataFilter]:
    allowed_fields = set(endpoint.config.get("allowed_filter_fields", []))
    filters = [
        DataFilter.model_validate(filter_)
        for filter_ in endpoint.config.get("filters", [])
    ]
    for field, value in request.query_params.multi_items():
        if field in {"limit", "offset", "sort", "direction"}:
            continue
        if allowed_fields and field not in allowed_fields:
            raise HTTPException(status_code=400, detail=f"Filtering by '{field}' is not allowed")
        filters.append(DataFilter(field=field, op="eq", value=value))
    return filters


async def _execute_data_query_endpoint(
    db: AsyncSession,
    *,
    endpoint: ClientEndpoint,
    workspace_id: uuid.UUID,
    request: Request,
) -> dict[str, Any]:
    table = endpoint.config.get("table")
    if not table:
        raise HTTPException(status_code=400, detail="data_query endpoint is missing config.table")

    limit = int(request.query_params.get("limit", endpoint.config.get("limit", 50)))
    offset = int(request.query_params.get("offset", endpoint.config.get("offset", 0)))
    sort_field = request.query_params.get("sort", endpoint.config.get("sort", {}).get("field"))
    sort_direction = request.query_params.get("direction", endpoint.config.get("sort", {}).get("direction", "desc"))

    query = DataQueryRequest(
        table=table,
        select=endpoint.config.get("select"),
        filters=_query_filters_from_request(endpoint, request),
        sort=DataSort(field=sort_field, direction=sort_direction) if sort_field else None,
        limit=limit,
        offset=offset,
    )
    result = await execute_data_query(db, workspace_id=workspace_id, request=query)
    return result.model_dump(mode="json")


async def _execute_client_data_create_endpoint(
    db: AsyncSession,
    *,
    endpoint: ClientEndpoint,
    current_user: User,
    request: Request,
) -> dict[str, Any]:
    payload = await request.json()
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Request body must be a JSON object")

    record_type = endpoint.config.get("type") or payload.get("type")
    title_field = endpoint.config.get("title_field", "title")
    content_field = endpoint.config.get("content_field", "content")
    metadata_field = endpoint.config.get("metadata_field", "metadata")

    title = payload.get(title_field)
    if not record_type or not title:
        raise HTTPException(status_code=400, detail="Client data create endpoint requires type and title")

    record = ClientDataRecord(
        id=uuid.uuid4(),
        workspace_id=current_user.workspace_id,
        type=str(record_type),
        title=str(title),
        content=payload.get(content_field),
        metadata_=payload.get(metadata_field, payload),
    )
    db.add(record)
    await db.flush()
    return {
        "id": str(record.id),
        "type": record.type,
        "title": record.title,
        "content": record.content,
        "metadata": record.metadata_,
    }


async def _request_body(request: Request) -> Any:
    if request.method.upper() in {"GET", "DELETE"}:
        return None
    try:
        return await request.json()
    except Exception:
        return None


async def _execute_agent_task_endpoint(
    db: AsyncSession,
    *,
    endpoint: ClientEndpoint,
    current_user: User,
    request: Request,
) -> dict[str, Any]:
    body = await _request_body(request)
    instruction = endpoint.config.get(
        "instruction",
        "Handle this client API request using the correct Velaris data, tools, and backend functions.",
    )
    allowed_tools = endpoint.config.get("allowed_tools", ["data_query"])
    expected_response = endpoint.config.get("response", "Return the API response payload the client needs.")
    message = (
        f"You are serving a dynamic Velaris client API endpoint.\n"
        f"Endpoint: {endpoint.method} {endpoint.path}\n"
        f"Endpoint name: {endpoint.name}\n"
        f"Instruction: {instruction}\n"
        f"Allowed tools/functions: {allowed_tools}\n"
        f"Expected response: {expected_response}\n"
        f"Query params: {dict(request.query_params)}\n"
        f"Request body: {body}\n\n"
        "Use the authenticated workspace only. Choose the correct data/system/function, perform the work, "
        "and return a concise API-ready result."
    )

    run = AgentRun(
        id=uuid.uuid4(),
        workspace_id=current_user.workspace_id,
        user_id=current_user.id,
        status="pending",
        input_message=message,
    )
    db.add(run)
    await db.commit()

    result = await run_agent(
        message=message,
        run_id=run.id,
        workspace_id=current_user.workspace_id,
        user_id=current_user.id,
        db=db,
    )
    return {
        "agent_run_id": str(run.id),
        "status": result.get("status"),
        "message": result.get("message"),
        "intent": result.get("intent"),
        "tool_calls": result.get("tool_calls", []),
        "pending_approvals": result.get("pending_approvals", []),
    }


async def execute_client_endpoint(
    db: AsyncSession,
    *,
    endpoint: ClientEndpoint,
    current_user: User,
    request: Request,
) -> dict[str, Any]:
    if endpoint.mode == "data_query":
        result = await _execute_data_query_endpoint(
            db,
            endpoint=endpoint,
            workspace_id=current_user.workspace_id,
            request=request,
        )
    elif endpoint.mode == "agent_task":
        result = await _execute_agent_task_endpoint(
            db,
            endpoint=endpoint,
            current_user=current_user,
            request=request,
        )
    elif endpoint.mode == "client_data_create":
        result = await _execute_client_data_create_endpoint(
            db,
            endpoint=endpoint,
            current_user=current_user,
            request=request,
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported endpoint mode '{endpoint.mode}'")

    db.add(
        AuditLog(
            workspace_id=current_user.workspace_id,
            user_id=current_user.id,
            action="client_endpoint.execute",
            resource_type="client_endpoint",
            resource_id=str(endpoint.id),
            details={"method": endpoint.method, "path": endpoint.path, "mode": endpoint.mode},
            ip_address=request.client.host if request.client else None,
        )
    )
    await db.commit()
    return result
