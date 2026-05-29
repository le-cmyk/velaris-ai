from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse, urlunparse


def normalize_database_url(database_url: str) -> str:
    normalized = database_url or ""
    for prefix in ("postgresql://", "postgres://"):
        if normalized.startswith(prefix):
            normalized = normalized.replace(prefix, "postgresql+asyncpg://", 1)
            break
    return normalized


def redact_database_url(database_url: str) -> str:
    if not database_url:
        return ""
    parsed = urlparse(database_url)
    if parsed.password is None:
        return database_url
    host_part = parsed.hostname or ""
    if parsed.port:
        host_part = f"{host_part}:{parsed.port}"
    userinfo = parsed.username or ""
    netloc = f"{userinfo}:***@{host_part}" if userinfo else host_part
    return urlunparse((parsed.scheme, netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))


def print_database_debug(
    context: str,
    database_url: str,
    settings_database_url: str | None = None,
    env_file: str | Path = ".env",
) -> None:
    normalized = normalize_database_url(database_url)
    parsed = urlparse(normalized)
    normalized_settings_database_url = normalize_database_url(settings_database_url or "")
    env_database_url = os.environ.get("DATABASE_URL", "")
    normalized_env_database_url = normalize_database_url(env_database_url)

    print(f"=== DATABASE CONTEXT: {context} ===")
    print("DATABASE_URL (redacted):", redact_database_url(normalized))
    if settings_database_url is not None:
        print("settings.database_url (redacted):", redact_database_url(normalized_settings_database_url))
        print(
            "Matches settings.database_url:",
            normalized_settings_database_url == normalized,
        )
    print("os.environ has DATABASE_URL:", "DATABASE_URL" in os.environ)
    print("os.environ DATABASE_URL (redacted):", redact_database_url(normalized_env_database_url))
    print("Uses same as os.environ:", normalized_env_database_url == normalized)
    env_file_path = Path(env_file)
    print(".env file configured:", str(env_file_path))
    print(".env file exists in cwd:", env_file_path.exists())
    print("=== DATABASE DEBUG ===")
    print("Scheme:", parsed.scheme)
    print("Host:", parsed.hostname)
    print("Port:", parsed.port)
    print("Database:", parsed.path)
    print("Username:", parsed.username)
    print("Contains asyncpg:", "asyncpg" in normalized)
    print("=====================")
