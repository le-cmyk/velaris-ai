from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class DataColumnSchema(BaseModel):
    name: str
    type: str
    nullable: bool
    primary_key: bool
    indexed: bool
    foreign_key: str | None = None


class DataTableSchema(BaseModel):
    name: str
    description: str
    workspace_scoped: bool
    columns: list[DataColumnSchema]
    default_sort: str | None = None
    row_count: int | None = None


class DataRelationshipSchema(BaseModel):
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    on_delete: str | None = None


class DataCatalogResponse(BaseModel):
    tables: list[DataTableSchema]
    relationships: list[DataRelationshipSchema]


DataFilterOperator = Literal["eq", "ne", "lt", "lte", "gt", "gte", "ilike", "in", "contains"]
DataSortDirection = Literal["asc", "desc"]


class DataFilter(BaseModel):
    field: str
    op: DataFilterOperator = "eq"
    value: Any


class DataSort(BaseModel):
    field: str = "created_at"
    direction: DataSortDirection = "desc"


class DataQueryRequest(BaseModel):
    table: str = Field(..., description="Public Velaris data table to query")
    select: list[str] | None = Field(default=None, description="Optional list of columns to return")
    filters: list[DataFilter] = Field(default_factory=list)
    sort: DataSort | None = None
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class DataQueryResponse(BaseModel):
    table: str
    columns: list[str]
    rows: list[dict[str, Any]]
    row_count: int
    limit: int
    offset: int

