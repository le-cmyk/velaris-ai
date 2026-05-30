import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ProductCreate(BaseModel):
    name: str
    sku: str | None = None
    description: str | None = None
    price: Decimal = Decimal("0")
    category: str | None = None
    inventory_count: int = 0
    is_active: bool = True


class ProductUpdate(BaseModel):
    name: str | None = None
    sku: str | None = None
    description: str | None = None
    price: Decimal | None = None
    category: str | None = None
    inventory_count: int | None = None
    is_active: bool | None = None


class ProductSchema(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    sku: str | None
    description: str | None
    price: Decimal
    category: str | None
    inventory_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductListResponse(BaseModel):
    items: list[ProductSchema]
    total: int
