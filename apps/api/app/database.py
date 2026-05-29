from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings
from app.database_debug import normalize_database_url, print_database_debug


class Base(AsyncAttrs, DeclarativeBase):
    pass


database_url = normalize_database_url(settings.database_url)
print_database_debug("app.database.create_async_engine", database_url, settings.database_url)

engine = create_async_engine(database_url, future=True, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
