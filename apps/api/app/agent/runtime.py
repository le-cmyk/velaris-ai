from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.intents import Intent
from app.gateway.tool_gateway import tool_gateway
from app.models.agent_run import AgentRun

READ_KEYWORDS = ("select", "show", "list", "get", "fetch", "find")
WRITE_KEYWORDS = ("insert", "update", "delete", "write", "create", "remove", "drop", "alter", "truncate")
SUMMARY_KEYWORDS = ("summarize", "summary", "report")


def classify_intent(message: str) -> Intent:
    lowered = message.lower()
    if any(keyword in lowered for keyword in SUMMARY_KEYWORDS):
        return Intent.SUMMARIZE_DATA
    if any(keyword in lowered for keyword in WRITE_KEYWORDS):
        return Intent.DATABASE_WRITE_REQUEST
    if any(keyword in lowered for keyword in READ_KEYWORDS):
        return Intent.DATABASE_READ
    return Intent.UNKNOWN


def build_execution_plan(intent: Intent, query: str | None = None) -> dict[str, Any]:
    steps = ["Classify intent", "Build execution plan"]
    requires_approval = intent == Intent.DATABASE_WRITE_REQUEST
    if intent in {Intent.DATABASE_READ, Intent.DATABASE_WRITE_REQUEST, Intent.SUMMARIZE_DATA}:
        steps.append("Prepare postgres_query tool call")
        steps.append("Execute through tool gateway")
    else:
        steps.append("Respond without tool execution")
    return {
        "intent": intent.value,
        "steps": steps,
        "query": query,
        "requires_approval": requires_approval,
    }


def generate_mock_query(message: str, intent: Intent) -> str | None:
    lowered = message.lower()
    if intent == Intent.DATABASE_READ:
        if "order" in lowered:
            return "SELECT id, customer_id, amount, status, created_at FROM orders ORDER BY created_at DESC LIMIT 10"
        if "workspace" in lowered:
            return "SELECT id, name, slug, created_at FROM workspaces ORDER BY created_at DESC LIMIT 10"
        return "SELECT id, name, email, created_at FROM users ORDER BY created_at DESC LIMIT 10"
    if intent == Intent.DATABASE_WRITE_REQUEST:
        if "user" in lowered or "customer" in lowered:
            return "UPDATE users SET full_name = 'Updated User' WHERE id = 1"
        if "order" in lowered:
            return "INSERT INTO orders (customer_id, amount, status) VALUES (1, 100.0, 'pending')"
        return "DELETE FROM memories WHERE workspace_id IS NULL"
    if intent == Intent.SUMMARIZE_DATA:
        if "order" in lowered:
            return "SELECT id, customer_id, amount, status, created_at FROM orders ORDER BY created_at DESC LIMIT 10"
        return "SELECT id, name, email, created_at FROM users ORDER BY created_at DESC LIMIT 10"
    return None


async def run_agent(
    message: str,
    run_id: uuid.UUID,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> dict[str, Any]:
    run = await db.get(AgentRun, run_id)
    intent = classify_intent(message)
    query = generate_mock_query(message, intent)
    execution_plan = build_execution_plan(intent, query)

    if run is not None:
        run.status = "running"
        run.intent = intent.value
        run.execution_plan = execution_plan
        await db.commit()

    tool_calls: list[dict[str, Any]] = []
    pending_approvals: list[dict[str, Any]] = []
    response_message = "I could not confidently map this request to a supported database action yet."
    response_status = "completed"

    try:
        if intent in {Intent.DATABASE_READ, Intent.DATABASE_WRITE_REQUEST, Intent.SUMMARIZE_DATA} and query:
            gateway_response = await tool_gateway.execute(
                tool_name="postgres_query",
                arguments={"query": query},
                run_id=run_id,
                workspace_id=workspace_id,
                user_id=user_id,
                db=db,
            )
            tool_calls.append(
                {
                    "tool_name": "postgres_query",
                    "arguments": {"query": query},
                    "status": gateway_response["status"],
                    "result": gateway_response.get("result"),
                    "requires_approval": gateway_response.get("requires_approval", False),
                }
            )

            if gateway_response["status"] == "pending_approval":
                response_message = "Your request needs approval before the SQL write can be executed."
                response_status = "pending"
                pending_approvals.append(
                    {
                        "approval_id": gateway_response.get("approval_id"),
                        "tool_name": "postgres_query",
                        "query": query,
                    }
                )
            elif gateway_response["status"] == "executed":
                result = gateway_response.get("result") or {}
                if intent == Intent.SUMMARIZE_DATA:
                    row_count = result.get("row_count", 0)
                    response_message = f"Summary ready. I reviewed {row_count} rows from the requested dataset."
                else:
                    response_message = "Query executed successfully through the tool gateway."
            elif gateway_response["status"] == "failed":
                response_message = "The tool call failed during execution."
                response_status = "failed"
            else:
                response_message = "The requested tool call was blocked by gateway safety checks."
                response_status = "failed"
    except Exception as exc:
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
