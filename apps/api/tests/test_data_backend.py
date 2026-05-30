from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.data.catalog import build_data_catalog, execute_data_query
from app.models.customer import Customer
from app.schemas.data_backend import DataFilter, DataQueryRequest


def _mock_scalars(items: list[object]):
    result = MagicMock()
    result.scalars.return_value.all.return_value = items
    return result


@pytest.mark.asyncio
async def test_catalog_exposes_tables_and_relationships() -> None:
    db = AsyncMock()
    workspace_id = uuid.uuid4()

    catalog = await build_data_catalog(db, workspace_id=workspace_id)

    table_names = {table.name for table in catalog.tables}
    assert "customers" in table_names
    assert "deals" in table_names
    assert any(
        relationship.from_table == "deals"
        and relationship.from_column == "customer_id"
        and relationship.to_table == "customers"
        for relationship in catalog.relationships
    )


@pytest.mark.asyncio
async def test_structured_query_is_workspace_scoped_and_serialized() -> None:
    workspace_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    customer = Customer(
        id=customer_id,
        workspace_id=workspace_id,
        name="Acme",
        email="ops@acme.test",
        status="active",
        mrr=1000,
        tags=["priority"],
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
    )
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_mock_scalars([customer]))

    result = await execute_data_query(
        db,
        workspace_id=workspace_id,
        request=DataQueryRequest(
            table="customers",
            select=["id", "name", "mrr", "created_at"],
            filters=[DataFilter(field="status", op="eq", value="active")],
            limit=10,
        ),
    )

    assert result.columns == ["id", "name", "mrr", "created_at"]
    assert result.rows == [
        {
            "id": str(customer_id),
            "name": "Acme",
            "mrr": 1000.0,
            "created_at": "2026-01-01T00:00:00+00:00",
        }
    ]
    executed_query = db.execute.call_args.args[0]
    assert "customers.workspace_id" in str(executed_query)


@pytest.mark.asyncio
async def test_structured_query_rejects_restricted_workspace_filter() -> None:
    db = AsyncMock()

    with pytest.raises(HTTPException, match="workspace_id is enforced"):
        await execute_data_query(
            db,
            workspace_id=uuid.uuid4(),
            request=DataQueryRequest(
                table="customers",
                filters=[DataFilter(field="workspace_id", op="eq", value=str(uuid.uuid4()))],
            ),
        )


@pytest.mark.asyncio
async def test_structured_query_rejects_unknown_table() -> None:
    db = AsyncMock()

    with pytest.raises(HTTPException, match="Unknown data table"):
        await execute_data_query(
            db,
            workspace_id=uuid.uuid4(),
            request=DataQueryRequest(table="users"),
        )
