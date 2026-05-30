import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict


class CustomerCreate(BaseModel):
    name: str
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    status: str = "prospect"
    tier: str | None = None
    mrr: Decimal = Decimal("0")
    churn_risk_score: float | None = None
    industry: str | None = None
    country: str | None = None
    tags: list[str] = []
    notes: str | None = None
    last_contact_at: datetime | None = None


class CustomerUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    status: str | None = None
    tier: str | None = None
    mrr: Decimal | None = None
    churn_risk_score: float | None = None
    industry: str | None = None
    country: str | None = None
    tags: list[str] | None = None
    notes: str | None = None
    last_contact_at: datetime | None = None


class CustomerSchema(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    email: str | None
    phone: str | None
    company: str | None
    status: str
    tier: str | None
    mrr: Decimal
    churn_risk_score: float | None
    industry: str | None
    country: str | None
    tags: list[str]
    notes: str | None
    last_contact_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CustomerListResponse(BaseModel):
    items: list[CustomerSchema]
    total: int
