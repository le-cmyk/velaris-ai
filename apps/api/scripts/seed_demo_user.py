from __future__ import annotations

import argparse
import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.core.security import hash_password
from app.database_debug import normalize_database_url, print_database_debug
from app.models.user import User
from app.models.workspace import Workspace


async def seed_demo_user(force: bool) -> None:
    database_url = normalize_database_url(settings.database_url)
    print_database_debug(
        "scripts.seed_demo_user.create_async_engine",
        database_url,
        settings.database_url,
        settings.model_config.get("env_file", ".env"),
    )
    engine = create_async_engine(database_url, future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with session_factory() as session:
            existing_user = await session.scalar(select(User).where(User.email == "demo@velaris.ai"))
            if existing_user is not None and not force:
                raise RuntimeError(
                    "Demo user already exists. Re-run with --force to skip safety prompt and keep existing data."
                )
            if existing_user is not None:
                return

            workspace = await session.scalar(select(Workspace).where(Workspace.slug == "demo-workspace"))
            if workspace is None:
                workspace = Workspace(
                    name="Demo Workspace",
                    slug="demo-workspace",
                    description="Seed workspace for Velaris demos",
                )
                session.add(workspace)
                await session.flush()

            user = User(
                workspace_id=workspace.id,
                email="demo@velaris.ai",
                hashed_password=hash_password("demo123"),
                full_name="Velaris Demo User",
                is_active=True,
                is_superuser=True,
            )
            session.add(user)
            await session.commit()
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo workspace and user safely.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip failure when demo records already exist. Existing rows are not overwritten.",
    )
    args = parser.parse_args()
    asyncio.run(seed_demo_user(force=args.force))


if __name__ == "__main__":
    main()
