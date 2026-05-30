import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class DealCreate(BaseModel):
    customer_id: uuid.UUID | None = None
    name: str
    value: Decimal = Decimal("0")
    currency: str = "USD"
    stage: str = "discovery"
    probability: int = 50
    close_date: date | None = None
    owner: str | None = None
    notes: str | None = None
    tags: list[str] = []


class DealUpdate(BaseModel):
    customer_id: uuid.UUID | None = None
    name: str | None = None
    value: Decimal | None = None
    currency: str | None = None
    stage: str | None = None
    probability: int | None = None
    close_date: date | None = None
    owner: str | None = None
    notes: str | None = None
    tags: list[str] | None = None


class DealSchema(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    customer_id: uuid.UUID | None
    name: str
    value: Decimal
    currency: str
    stage: str
    probability: int
    close_date: date | None
    owner: str | None
    notes: str | None
    tags: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DealListResponse(BaseModel):
    items: list[DealSchema]
    total: int
