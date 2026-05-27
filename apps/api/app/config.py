from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = Field(
        default="postgresql+asyncpg://user:password@localhost:5432/velaris_ai",
        validation_alias=AliasChoices("DATABASE_URL", "database_url"),
    )
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        validation_alias=AliasChoices("REDIS_URL", "redis_url"),
    )
    secret_key: str = Field(
        default="change-me-in-production",
        validation_alias=AliasChoices("JWT_SECRET", "SECRET_KEY", "secret_key"),
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    environment: str = Field(default="development", validation_alias=AliasChoices("ENVIRONMENT", "environment"))
    cors_origins: list[str] = Field(default_factory=list, validation_alias=AliasChoices("CORS_ORIGINS", "cors_origins"))
    client_config_path: str = Field(
        default="client-config.yaml",
        validation_alias=AliasChoices("CLIENT_CONFIG_PATH", "client_config_path"),
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return []


DEFAULT_CLIENT_CONFIG: dict[str, Any] = {
    "cors_origins": [],
    "tools": {
        "postgres_query": {
            "enabled": True,
            "description": "Execute a SQL query against the PostgreSQL database",
            "requires_approval": True,
        }
    },
}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


@lru_cache(maxsize=1)
def load_client_config() -> dict[str, Any]:
    configured_path = Path(settings.client_config_path)
    if not configured_path.is_absolute():
        current = Path(__file__).resolve().parent
        candidates = [current.parent / configured_path]
        candidates.extend(parent / configured_path for parent in current.parents)
        configured_path = next((candidate for candidate in candidates if candidate.exists()), candidates[0])
    config_path = configured_path
    if not config_path.exists():
        return deepcopy(DEFAULT_CLIENT_CONFIG)

    with config_path.open("r", encoding="utf-8") as file:
        loaded = yaml.safe_load(file) or {}

    if not isinstance(loaded, dict):
        return deepcopy(DEFAULT_CLIENT_CONFIG)

    return _deep_merge(DEFAULT_CLIENT_CONFIG, loaded)


settings = Settings()
client_config = load_client_config()
