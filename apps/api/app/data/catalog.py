from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import Select, func, inspect, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.database import Base
from app.models.agent_template import AgentTemplate
from app.models.client_data import ClientDataRecord
from app.models.contact import Contact
from app.models.conversation import Conversation
from app.models.customer import Customer
from app.models.dashboard import Dashboard
from app.models.dashboard_widget import DashboardWidget
from app.models.deal import Deal
from app.models.invoice import Invoice
from app.models.message import Message
from app.models.notification import Notification
from app.models.product import Product
from app.models.scheduled_job import ScheduledJob
from app.models.support_ticket import SupportTicket
from app.models.task import Task
from app.models.ticket_comment import TicketComment
from app.models.workflow import Workflow
from app.models.workflow_run import WorkflowRun
from app.schemas.data_backend import (
    DataCatalogResponse,
    DataColumnSchema,
    DataFilter,
    DataQueryRequest,
    DataQueryResponse,
    DataRelationshipSchema,
    DataTableSchema,
)


PUBLIC_DATA_MODELS: dict[str, type[DeclarativeBase]] = {
    "agent_templates": AgentTemplate,
    "client_data_records": ClientDataRecord,
    "contacts": Contact,
    "conversations": Conversation,
    "customers": Customer,
    "dashboards": Dashboard,
    "dashboard_widgets": DashboardWidget,
    "deals": Deal,
    "invoices": Invoice,
    "messages": Message,
    "notifications": Notification,
    "products": Product,
    "scheduled_jobs": ScheduledJob,
    "support_tickets": SupportTicket,
    "tasks": Task,
    "ticket_comments": TicketComment,
    "workflows": Workflow,
    "workflow_runs": WorkflowRun,
}

TABLE_DESCRIPTIONS = {
    "customers": "Accounts, companies, or people the workspace sells to or supports.",
    "contacts": "People linked to customers.",
    "deals": "Pipeline opportunities linked to customers.",
    "invoices": "Commercial invoices linked to customers.",
    "support_tickets": "Support issues linked to customers.",
    "ticket_comments": "Comments and internal notes attached to support tickets.",
    "tasks": "Operational tasks and linked work items.",
    "products": "Products and services available to the workspace.",
    "client_data_records": "Flexible knowledge records for imported or unstructured client data.",
    "conversations": "Agent/user conversation containers.",
    "messages": "Messages within conversations.",
    "agent_templates": "Reusable agent configurations available to a workspace.",
    "scheduled_jobs": "Recurring agent jobs.",
    "workflows": "Automated workflow definitions.",
    "workflow_runs": "Execution history for workflows.",
    "dashboards": "Workspace dashboard definitions.",
    "dashboard_widgets": "Dashboard widgets and saved queries.",
    "notifications": "User and workspace notifications.",
}

EXCLUDED_COLUMNS = {"hashed_password", "key_hash"}


def _model_for_table(table: str) -> type[DeclarativeBase]:
    model = PUBLIC_DATA_MODELS.get(table)
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown data table '{table}'",
        )
    return model


def _workspace_scoped(model: type[DeclarativeBase]) -> bool:
    return "workspace_id" in model.__table__.columns


def _public_columns(model: type[DeclarativeBase]) -> list[str]:
    return [column.name for column in model.__table__.columns if column.name not in EXCLUDED_COLUMNS]


def _serialize(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, Decimal):
        return float(value)
    return value


def _relationships_for_models() -> list[DataRelationshipSchema]:
    public_tables = set(PUBLIC_DATA_MODELS)
    relationships: list[DataRelationshipSchema] = []
    for table_name, model in PUBLIC_DATA_MODELS.items():
        for column in model.__table__.columns:
            for fk in column.foreign_keys:
                target = fk.column.table.name
                if target not in public_tables and target != "workspaces":
                    continue
                relationships.append(
                    DataRelationshipSchema(
                        from_table=table_name,
                        from_column=column.name,
                        to_table=target,
                        to_column=fk.column.name,
                        on_delete=fk.ondelete,
                    )
                )
    return relationships


async def build_data_catalog(
    db: AsyncSession,
    *,
    workspace_id: uuid.UUID,
    include_counts: bool = False,
) -> DataCatalogResponse:
    tables: list[DataTableSchema] = []
    for table_name, model in sorted(PUBLIC_DATA_MODELS.items()):
        mapper = inspect(model)
        indexed_columns = {column.name for index in model.__table__.indexes for column in index.columns}
        columns = []
        for column in model.__table__.columns:
            if column.name in EXCLUDED_COLUMNS:
                continue
            foreign_key = next(iter(column.foreign_keys), None)
            columns.append(
                DataColumnSchema(
                    name=column.name,
                    type=str(column.type),
                    nullable=column.nullable,
                    primary_key=column.primary_key,
                    indexed=column.index is True or column.name in indexed_columns,
                    foreign_key=(
                        f"{foreign_key.column.table.name}.{foreign_key.column.name}"
                        if foreign_key is not None
                        else None
                    ),
                )
            )

        row_count = None
        if include_counts and _workspace_scoped(model):
            row_count = await db.scalar(
                select(func.count()).select_from(model).where(model.workspace_id == workspace_id)
            )

        default_sort = "updated_at" if "updated_at" in mapper.columns else "created_at"
        tables.append(
            DataTableSchema(
                name=table_name,
                description=TABLE_DESCRIPTIONS.get(table_name, "Workspace data table."),
                workspace_scoped=_workspace_scoped(model),
                columns=columns,
                default_sort=default_sort if default_sort in mapper.columns else None,
                row_count=row_count,
            )
        )

    return DataCatalogResponse(tables=tables, relationships=_relationships_for_models())


def _column(model: type[DeclarativeBase], field: str):
    if field in EXCLUDED_COLUMNS or field not in model.__table__.columns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown or restricted field '{field}'",
        )
    return getattr(model, field)


def _apply_filter(query: Select, model: type[DeclarativeBase], filter_: DataFilter) -> Select:
    column = _column(model, filter_.field)
    value = filter_.value
    if filter_.op == "eq":
        return query.where(column == value)
    if filter_.op == "ne":
        return query.where(column != value)
    if filter_.op == "lt":
        return query.where(column < value)
    if filter_.op == "lte":
        return query.where(column <= value)
    if filter_.op == "gt":
        return query.where(column > value)
    if filter_.op == "gte":
        return query.where(column >= value)
    if filter_.op == "ilike":
        return query.where(column.ilike(f"%{value}%"))
    if filter_.op == "in":
        if not isinstance(value, list):
            raise HTTPException(status_code=400, detail="'in' filters require a list value")
        return query.where(column.in_(value))
    if filter_.op == "contains":
        return query.where(column.contains(value))
    raise HTTPException(status_code=400, detail=f"Unsupported filter operator '{filter_.op}'")


async def execute_data_query(
    db: AsyncSession,
    *,
    workspace_id: uuid.UUID,
    request: DataQueryRequest,
) -> DataQueryResponse:
    model = _model_for_table(request.table)
    if not _workspace_scoped(model):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Table '{request.table}' is not available through workspace data queries",
        )

    available_columns = _public_columns(model)
    requested_columns = request.select or available_columns
    for field in requested_columns:
        _column(model, field)

    query = select(model).where(model.workspace_id == workspace_id)
    for filter_ in request.filters:
        if filter_.field == "workspace_id":
            raise HTTPException(status_code=400, detail="workspace_id is enforced by Velaris")
        query = _apply_filter(query, model, filter_)

    sort = request.sort
    if sort is not None:
        sort_column = _column(model, sort.field)
        query = query.order_by(sort_column.asc() if sort.direction == "asc" else sort_column.desc())
    elif "updated_at" in model.__table__.columns:
        query = query.order_by(getattr(model, "updated_at").desc())
    elif "created_at" in model.__table__.columns:
        query = query.order_by(getattr(model, "created_at").desc())

    result = await db.execute(query.offset(request.offset).limit(request.limit))
    records = result.scalars().all()
    rows = [
        {field: _serialize(getattr(record, field)) for field in requested_columns}
        for record in records
    ]
    return DataQueryResponse(
        table=request.table,
        columns=requested_columns,
        rows=rows,
        row_count=len(rows),
        limit=request.limit,
        offset=request.offset,
    )

