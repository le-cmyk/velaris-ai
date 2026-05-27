from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/velaris_ai"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


DEFAULT_CLIENT_CONFIG: dict[str, Any] = {
    "cors_origins": ["http://localhost:3000"],
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
    config_path = Path(__file__).resolve().parents[1] / "client-config.yaml"
    if not config_path.exists():
        return deepcopy(DEFAULT_CLIENT_CONFIG)

    with config_path.open("r", encoding="utf-8") as file:
        loaded = yaml.safe_load(file) or {}

    if not isinstance(loaded, dict):
        return deepcopy(DEFAULT_CLIENT_CONFIG)

    return _deep_merge(DEFAULT_CLIENT_CONFIG, loaded)


settings = Settings()
client_config = load_client_config()
