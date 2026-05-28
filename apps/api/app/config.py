from __future__ import annotations

import logging
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


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
    cors_origins_raw: str = Field(
        default="",
        validation_alias=AliasChoices("CORS_ORIGINS", "cors_origins"),
    )
    client_config_path: str = Field(
        default="client-config.yaml",
        validation_alias=AliasChoices("CLIENT_CONFIG_PATH", "client_config_path"),
    )
    openrouter_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("OPENROUTER_API_KEY", "openrouter_api_key"),
    )
    openrouter_model: str = Field(
        default="deepseek/deepseek-r1-0528",
        validation_alias=AliasChoices("OPENROUTER_MODEL", "openrouter_model"),
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        if not self.cors_origins_raw:
            return []
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]


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
        # Search from api directory upward so CLIENT_CONFIG_PATH can be set
        # relative to either apps/api or repository root.
        candidates = [current.parent / configured_path]
        candidates.extend(parent / configured_path for parent in current.parents)
        configured_path = next((candidate for candidate in candidates if candidate.exists()), candidates[0])
    config_path = configured_path
    if not config_path.exists():
        logger.warning("Client config file not found at %s. Falling back to default configuration.", config_path)
        return deepcopy(DEFAULT_CLIENT_CONFIG)

    with config_path.open("r", encoding="utf-8") as file:
        loaded = yaml.safe_load(file) or {}

    if not isinstance(loaded, dict):
        return deepcopy(DEFAULT_CLIENT_CONFIG)

    return _deep_merge(DEFAULT_CLIENT_CONFIG, loaded)


settings = Settings()
client_config = load_client_config()
