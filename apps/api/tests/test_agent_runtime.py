"""Unit tests for the agent runtime: intent classification and execution planning."""

import pytest
from unittest.mock import AsyncMock, MagicMock
import uuid

from app.agent.intents import Intent
from app.agent.runtime import _execute_action, classify_intent, build_execution_plan
from app.models.client_endpoint import ClientEndpoint


class TestIntentClassification:
    """Tests for classify_intent()."""

    def test_list_customers_is_database_read(self) -> None:
        assert classify_intent("Show me the list of customers") == Intent.DATABASE_READ

    def test_select_keyword_is_database_read(self) -> None:
        assert classify_intent("select all orders from last month") == Intent.DATABASE_READ

    def test_get_is_database_read(self) -> None:
        assert classify_intent("get all users from this week") == Intent.DATABASE_READ

    def test_find_is_database_read(self) -> None:
        assert classify_intent("find the invoice for customer 42") == Intent.DATABASE_READ

    def test_summarize_is_summarize_data(self) -> None:
        assert classify_intent("summarize sales for Q1") == Intent.SUMMARIZE_DATA

    def test_summary_is_summarize_data(self) -> None:
        assert classify_intent("give me a summary of active users") == Intent.SUMMARIZE_DATA

    def test_report_is_summarize_data(self) -> None:
        assert classify_intent("generate a report on revenue") == Intent.SUMMARIZE_DATA

    def test_update_is_database_write_request(self) -> None:
        assert classify_intent("update the price for product 5") == Intent.DATABASE_WRITE_REQUEST

    def test_delete_is_database_write_request(self) -> None:
        assert classify_intent("delete the order with id 99") == Intent.DATABASE_WRITE_REQUEST

    def test_create_is_database_write_request(self) -> None:
        assert classify_intent("create a new customer record") == Intent.DATABASE_WRITE_REQUEST

    def test_insert_is_database_write_request(self) -> None:
        assert classify_intent("insert a row into the users table") == Intent.DATABASE_WRITE_REQUEST

    def test_unknown_intent(self) -> None:
        assert classify_intent("what is the meaning of life") == Intent.UNKNOWN

    def test_empty_message(self) -> None:
        assert classify_intent("") == Intent.UNKNOWN

    def test_case_insensitive(self) -> None:
        assert classify_intent("LIST all products") == Intent.DATABASE_READ
        assert classify_intent("SUMMARIZE revenue") == Intent.SUMMARIZE_DATA

    def test_create_route_is_database_write_request(self) -> None:
        assert classify_intent("create a route for support triage") == Intent.DATABASE_WRITE_REQUEST
        assert classify_intent("add an API endpoint for leads") == Intent.DATABASE_WRITE_REQUEST


class TestExecutionPlan:
    """Tests for build_execution_plan()."""

    def test_database_read_plan_has_llm_step(self) -> None:
        plan = build_execution_plan(Intent.DATABASE_READ)
        assert "Call OpenRouter LLM with context" in plan["steps"]
        assert plan["intent"] == "database_read"
        assert plan["requires_approval"] is False

    def test_database_write_plan_requires_approval(self) -> None:
        plan = build_execution_plan(Intent.DATABASE_WRITE_REQUEST)
        assert plan["requires_approval"] is True

    def test_unknown_intent_plan_has_llm_step(self) -> None:
        plan = build_execution_plan(Intent.UNKNOWN)
        assert "Call OpenRouter LLM" in plan["steps"]
        assert plan["requires_approval"] is False

    def test_summarize_plan_has_llm_step(self) -> None:
        plan = build_execution_plan(Intent.SUMMARIZE_DATA)
        assert "Call OpenRouter LLM with context" in plan["steps"]

    def test_plan_has_intent_field(self) -> None:
        plan = build_execution_plan(Intent.SUMMARIZE_DATA)
        assert plan["intent"] == Intent.SUMMARIZE_DATA.value

    def test_plan_has_steps_list(self) -> None:
        plan = build_execution_plan(Intent.DATABASE_READ)
        assert isinstance(plan["steps"], list)
        assert len(plan["steps"]) > 0


@pytest.mark.asyncio
async def test_execute_create_client_endpoint_action() -> None:
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    workspace_id = uuid.uuid4()
    user_id = uuid.uuid4()

    message, requires_approval = await _execute_action(
        {
            "action": "create_client_endpoint",
            "name": "Support triage",
            "method": "POST",
            "path": "/support/triage",
            "mode": "agent_task",
            "description": "Route support requests to an agent",
            "config": {"instruction": "Triage support requests"},
        },
        workspace_id,
        user_id,
        db,
        uuid.uuid4(),
    )

    assert requires_approval is False
    assert "POST /client-api/support/triage" in message
    created_endpoint = next(call.args[0] for call in db.add.call_args_list if isinstance(call.args[0], ClientEndpoint))
    assert created_endpoint.workspace_id == workspace_id
    assert created_endpoint.created_by_id == user_id
    assert created_endpoint.mode == "agent_task"
