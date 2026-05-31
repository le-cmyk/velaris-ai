from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.intents import Intent
from app.gateway.tool_gateway import tool_gateway
from app.llm.openrouter import OpenRouterError, chat_completion
from app.models.agent_run import AgentRun
from app.models.audit_log import AuditLog
from app.models.client_data import ClientDataRecord
from app.models.client_endpoint import ClientEndpoint

logger = logging.getLogger(__name__)

READ_KEYWORDS = ("select", "show", "list", "get", "fetch", "find")
WRITE_KEYWORDS = ("insert", "update", "delete", "write", "create", "remove", "drop", "alter", "truncate")
ROUTE_REQUEST_KEYWORDS = ("route", "endpoint", "api")
ROUTE_ACTION_KEYWORDS = ("add", "build", "create", "make", "register")
SUMMARY_KEYWORDS = ("summarize", "summary", "report")

_SYSTEM_PROMPT = """You are the Velaris AI operations assistant. You help users manage and query their business data.

You have access to the user's workspace records. Each record has: id, type, title, content, metadata.

You can also help users create API routes for their workspace. When a user says things like
"create an endpoint", "make a route", "I need a GET route", "add an API for leads", or
"let my app call /client-api/...", treat it as a route creation request.

ALLOWED ACTIONS (respond with JSON when you want to perform an action):
- list_records: {"action": "list_records", "type": "<optional type filter>"}
- search_records: {"action": "search_records", "query": "<search term>", "type": "<optional>"}
- summarize_records: {"action": "summarize_records", "type": "<optional type filter>"}
- create_record: {"action": "create_record", "type": "<type>", "title": "<title>", "content": "<content>"}
- update_record: {"action": "update_record", "id": "<uuid>", "title": "<optional>", "content": "<optional>"}
- delete_record: {"action": "delete_record", "id": "<uuid>", "confirm": true}
- create_client_endpoint: {"action": "create_client_endpoint", "name": "<route name>", "method": "GET|POST|PATCH|PUT|DELETE", "path": "/your/path", "mode": "agent_task|data_query|client_data_create", "description": "<what the route does>", "config": {...}}

IMPORTANT:
- For delete_record you MUST include "confirm": true only if the user explicitly confirmed deletion.
- If the user asks to delete but hasn't confirmed, respond with a natural language message asking for confirmation instead of JSON.
- Prefer create_client_endpoint with mode="agent_task" when the user wants a smart API route where the agent decides the right backend work.
- Prefer mode="data_query" for deterministic read endpoints and include config.table, optional config.select, config.filters, config.allowed_filter_fields, and config.limit.
- Prefer mode="client_data_create" for simple write endpoints into flexible client records and include config.type plus title/content field mappings.
- Created routes are called under /client-api{path}. They require the same Bearer token as the Velaris API.
- For normal questions or analysis, respond with plain text.
- When returning JSON actions, respond with ONLY the JSON object, nothing else.
- Record types include: customer, invoice, support_ticket, task, contract, company_note, product_usage.
"""

_MAX_CONTEXT_RECORDS = 30


def classify_intent(message: str) -> Intent:
    lowered = message.lower()
    if any(keyword in lowered for keyword in SUMMARY_KEYWORDS):
        return Intent.SUMMARIZE_DATA
    if any(keyword in lowered for keyword in ROUTE_REQUEST_KEYWORDS) and any(
        keyword in lowered for keyword in ROUTE_ACTION_KEYWORDS
    ):
        return Intent.DATABASE_WRITE_REQUEST
    if any(keyword in lowered for keyword in WRITE_KEYWORDS):
        return Intent.DATABASE_WRITE_REQUEST
    if any(keyword in lowered for keyword in READ_KEYWORDS):
        return Intent.DATABASE_READ
    return Intent.UNKNOWN


def build_execution_plan(intent: Intent, query: str | None = None) -> dict[str, Any]:
    steps = ["Classify intent", "Build execution plan"]
    requires_approval = intent == Intent.DATABASE_WRITE_REQUEST
    if intent in {Intent.DATABASE_READ, Intent.DATABASE_WRITE_REQUEST, Intent.SUMMARIZE_DATA}:
        steps.append("Load workspace client data")
        steps.append("Call OpenRouter LLM with context")
        steps.append("Parse LLM response / execute action")
    else:
        steps.append("Call OpenRouter LLM")
    return {
        "intent": intent.value,
        "steps": steps,
        "query": query,
        "requires_approval": requires_approval,
    }


async def _load_context_records(workspace_id: uuid.UUID, db: AsyncSession) -> list[dict[str, Any]]:
    result = await db.execute(
        select(ClientDataRecord)
        .where(ClientDataRecord.workspace_id == workspace_id)
        .order_by(ClientDataRecord.updated_at.desc())
        .limit(_MAX_CONTEXT_RECORDS)
    )
    records = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "type": r.type,
            "title": r.title,
            "content": r.content,
            "metadata": r.metadata_,
        }
        for r in records
    ]


def _records_to_context_text(records: list[dict[str, Any]]) -> str:
    if not records:
        return "No records found in workspace."
    lines = []
    for r in records:
        line = f"[{r['type']}] {r['title']} (id: {r['id']})"
        if r.get("content"):
            line += f"\n  {r['content'][:200]}"
        if r.get("metadata"):
            line += f"\n  metadata: {json.dumps(r['metadata'])}"
        lines.append(line)
    return "\n\n".join(lines)


async def _execute_action(
    action_data: dict[str, Any],
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
    run_id: uuid.UUID,
) -> tuple[str, bool]:
    """Execute a structured action from the LLM. Returns (response_message, requires_approval)."""
    action = action_data.get("action")

    if action == "list_records":
        type_filter = action_data.get("type")
        q = select(ClientDataRecord).where(ClientDataRecord.workspace_id == workspace_id)
        if type_filter:
            q = q.where(ClientDataRecord.type == type_filter)
        result = await db.execute(q.order_by(ClientDataRecord.created_at.desc()).limit(50))
        records = result.scalars().all()
        db.add(AuditLog(
            workspace_id=workspace_id, user_id=user_id,
            action="agent.list_records", resource_type="client_data_record",
            details={"type_filter": type_filter, "count": len(records)},
        ))
        await db.flush()
        if not records:
            return "No records found.", False
        lines = [f"- [{r.type}] **{r.title}** (id: {r.id})" for r in records]
        type_label = f" of type '{type_filter}'" if type_filter else ""
        return f"Found {len(records)} record(s){type_label}:\n" + "\n".join(lines), False

    if action == "search_records":
        query_text = action_data.get("query", "")
        type_filter = action_data.get("type")
        q = select(ClientDataRecord).where(
            ClientDataRecord.workspace_id == workspace_id,
            ClientDataRecord.title.ilike(f"%{query_text}%"),
        )
        if type_filter:
            q = q.where(ClientDataRecord.type == type_filter)
        result = await db.execute(q.limit(20))
        records = result.scalars().all()
        db.add(AuditLog(
            workspace_id=workspace_id, user_id=user_id,
            action="agent.search_records", resource_type="client_data_record",
            details={"query": query_text, "count": len(records)},
        ))
        await db.flush()
        if not records:
            return f"No records found matching '{query_text}'.", False
        lines = [f"- [{r.type}] **{r.title}** (id: {r.id})" for r in records]
        return f"Found {len(records)} result(s) for '{query_text}':\n" + "\n".join(lines), False

    if action == "summarize_records":
        type_filter = action_data.get("type")
        q = select(ClientDataRecord).where(ClientDataRecord.workspace_id == workspace_id)
        if type_filter:
            q = q.where(ClientDataRecord.type == type_filter)
        result = await db.execute(q)
        records = result.scalars().all()
        db.add(AuditLog(
            workspace_id=workspace_id, user_id=user_id,
            action="agent.summarize_records", resource_type="client_data_record",
            details={"type_filter": type_filter, "count": len(records)},
        ))
        await db.flush()
        from collections import Counter
        type_counts = Counter(r.type for r in records)
        summary = f"Workspace has {len(records)} total record(s).\n"
        for rtype, count in sorted(type_counts.items()):
            summary += f"  - {rtype}: {count}\n"
        return summary.strip(), False

    if action == "create_record":
        record = ClientDataRecord(
            id=uuid.uuid4(),
            workspace_id=workspace_id,
            type=action_data.get("type", "note"),
            title=action_data.get("title", "Untitled"),
            content=action_data.get("content"),
            metadata_=action_data.get("metadata"),
        )
        db.add(record)
        db.add(AuditLog(
            workspace_id=workspace_id, user_id=user_id,
            action="agent.create_record", resource_type="client_data_record",
            resource_id=str(record.id),
            details={"type": record.type, "title": record.title},
        ))
        await db.flush()
        return f"Created new {record.type} record: **{record.title}** (id: {record.id})", False

    if action == "update_record":
        record_id_str = action_data.get("id")
        if not record_id_str:
            return "update_record requires an 'id' field.", False
        try:
            record_id = uuid.UUID(record_id_str)
        except ValueError:
            return f"Invalid record id: {record_id_str}", False
        result = await db.execute(
            select(ClientDataRecord).where(
                ClientDataRecord.id == record_id,
                ClientDataRecord.workspace_id == workspace_id,
            )
        )
        record = result.scalar_one_or_none()
        if record is None:
            return f"Record {record_id_str} not found.", False
        if action_data.get("title"):
            record.title = action_data["title"]
        if action_data.get("content"):
            record.content = action_data["content"]
        if action_data.get("metadata"):
            record.metadata_ = action_data["metadata"]
        db.add(AuditLog(
            workspace_id=workspace_id, user_id=user_id,
            action="agent.update_record", resource_type="client_data_record",
            resource_id=str(record.id),
            details={"title": record.title},
        ))
        await db.flush()
        return f"Updated record: **{record.title}** (id: {record.id})", False

    if action == "delete_record":
        if not action_data.get("confirm"):
            return "Delete requires explicit confirmation. Please confirm you want to delete this record.", True
        record_id_str = action_data.get("id")
        if not record_id_str:
            return "delete_record requires an 'id' field.", False
        try:
            record_id = uuid.UUID(record_id_str)
        except ValueError:
            return f"Invalid record id: {record_id_str}", False
        result = await db.execute(
            select(ClientDataRecord).where(
                ClientDataRecord.id == record_id,
                ClientDataRecord.workspace_id == workspace_id,
            )
        )
        record = result.scalar_one_or_none()
        if record is None:
            return f"Record {record_id_str} not found.", False
        title = record.title
        db.add(AuditLog(
            workspace_id=workspace_id, user_id=user_id,
            action="agent.delete_record", resource_type="client_data_record",
            resource_id=str(record_id),
            details={"title": title},
        ))
        await db.delete(record)
        await db.flush()
        return f"Deleted record: **{title}** (id: {record_id})", False

    if action == "create_client_endpoint":
        method = str(action_data.get("method", "GET")).upper()
        path = "/" + str(action_data.get("path", "")).strip().strip("/")
        mode = str(action_data.get("mode", "agent_task"))
        if method not in {"GET", "POST", "PATCH", "PUT", "DELETE"}:
            return f"Unsupported endpoint method: {method}", False
        if path == "/":
            return "create_client_endpoint requires a non-root path.", False
        if path.startswith(("/backend", "/auth", "/data", "/client-data", "/client-api")):
            return "Endpoint path uses a reserved Velaris prefix. Choose a client-specific path like /support/triage.", False
        if mode not in {"agent_task", "data_query", "client_data_create"}:
            return f"Unsupported endpoint mode: {mode}", False

        endpoint = ClientEndpoint(
            id=uuid.uuid4(),
            workspace_id=workspace_id,
            created_by_id=user_id,
            name=action_data.get("name") or f"{method} {path}",
            method=method,
            path=path,
            mode=mode,
            description=action_data.get("description"),
            config=action_data.get("config") or {},
            is_active=True,
        )
        db.add(endpoint)
        await db.flush()
        db.add(AuditLog(
            workspace_id=workspace_id,
            user_id=user_id,
            action="agent.create_client_endpoint",
            resource_type="client_endpoint",
            resource_id=str(endpoint.id),
            details={"method": method, "path": path, "mode": mode, "config": endpoint.config},
        ))
        await db.flush()
        return (
            f"Created client API route **{method} /client-api{path}** using `{mode}` mode. "
            "Use the workspace Bearer token in the Authorization header to call it."
        ), False

    return f"Unknown action: {action}", False


async def run_agent(
    message: str,
    run_id: uuid.UUID,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> dict[str, Any]:
    run = await db.get(AgentRun, run_id)
    intent = classify_intent(message)
    execution_plan = build_execution_plan(intent)

    if run is not None:
        run.status = "running"
        run.intent = intent.value
        run.execution_plan = execution_plan
        await db.commit()

    tool_calls: list[dict[str, Any]] = []
    pending_approvals: list[dict[str, Any]] = []
    response_message = "I could not process your request."
    response_status = "completed"

    try:
        context_records = await _load_context_records(workspace_id, db)
        context_text = _records_to_context_text(context_records)

        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "system",
                "content": f"Current workspace records:\n\n{context_text}",
            },
            {"role": "user", "content": message},
        ]

        llm_response = await chat_completion(messages)

        # Attempt to parse as a structured action
        stripped = llm_response.strip()
        action_executed = False
        if stripped.startswith("{"):
            try:
                action_data = json.loads(stripped)
                if "action" in action_data:
                    action_executed = True
                    response_message, requires_approval = await _execute_action(
                        action_data, workspace_id, user_id, db, run_id
                    )
                    tool_calls.append(
                        {
                            "tool_name": action_data["action"],
                            "arguments": action_data,
                            "status": "executed",
                            "result": None,
                            "requires_approval": requires_approval,
                        }
                    )
                    if requires_approval:
                        response_status = "pending"
                        pending_approvals.append({"action": action_data["action"], "data": action_data})
            except (json.JSONDecodeError, Exception) as exc:
                logger.warning("Failed to parse LLM action response: %s", exc)

        if not action_executed:
            response_message = llm_response

        await db.commit()

    except OpenRouterError as exc:
        logger.warning("OpenRouter error: %s", exc)
        response_message = f"LLM service unavailable: {exc}"
        response_status = "failed"
    except Exception as exc:
        logger.exception("Agent execution failed")
        response_message = f"Agent execution failed: {exc}"
        response_status = "failed"

    if run is not None:
        run.output_message = response_message
        run.status = response_status if response_status in {"pending", "completed", "failed"} else "failed"
        await db.commit()

    return {
        "run_id": run_id,
        "message": response_message,
        "intent": intent.value,
        "execution_plan": execution_plan,
        "tool_calls": tool_calls,
        "pending_approvals": pending_approvals,
        "status": response_status,
    }
