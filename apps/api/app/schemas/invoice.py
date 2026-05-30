import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict


class InvoiceCreate(BaseModel):
    customer_id: uuid.UUID | None = None
    invoice_number: str
    amount: Decimal
    currency: str = "USD"
    status: str = "draft"
    due_date: date | None = None
    paid_at: datetime | None = None
    line_items: list[dict[str, Any]] = []
    notes: str | None = None


class InvoiceUpdate(BaseModel):
    customer_id: uuid.UUID | None = None
    invoice_number: str | None = None
    amount: Decimal | None = None
    currency: str | None = None
    status: str | None = None
    due_date: date | None = None
    paid_at: datetime | None = None
    line_items: list[dict[str, Any]] | None = None
    notes: str | None = None


class InvoiceSchema(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    customer_id: uuid.UUID | None
    invoice_number: str
    amount: Decimal
    currency: str
    status: str
    due_date: date | None
    paid_at: datetime | None
    line_items: list[dict[str, Any]]
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvoiceListResponse(BaseModel):
    items: list[InvoiceSchema]
    total: int
