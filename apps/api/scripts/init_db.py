from __future__ import annotations

import argparse
import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings
from app.database import Base
from app.database_debug import normalize_database_url, print_database_debug


async def initialize_database(force: bool) -> None:
    database_url = normalize_database_url(settings.database_url)
    print_database_debug(
        "scripts.init_db.create_async_engine",
        database_url,
        settings.database_url,
        settings.model_config.get("env_file", ".env"),
    )
    engine = create_async_engine(database_url, future=True)
    try:
        async with engine.begin() as connection:
            result = await connection.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                      AND table_name IN (
                        'workspaces', 'users', 'agent_runs', 'tool_calls', 'approval_requests', 'audit_logs', 'memories'
                      )
                    """
                )
            )
            existing_tables = int(result.scalar_one() or 0)
            if existing_tables > 0 and not force:
                raise RuntimeError(
                    "Database already contains Velaris tables. Re-run with --force to continue without altering existing data."
                )

            try:
                await connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            except Exception:
                pass

            await connection.run_sync(Base.metadata.create_all)
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize Velaris database schema safely.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Proceed even when Velaris tables already exist. Existing data is preserved.",
    )
    args = parser.parse_args()
    asyncio.run(initialize_database(force=args.force))


if __name__ == "__main__":
    main()
