from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(AsyncAttrs, DeclarativeBase):
    pass


database_url = settings.database_url
for prefix in ("postgresql://", "postgres://"):
    if database_url.startswith(prefix):
        database_url = database_url.replace(prefix, "postgresql+asyncpg://", 1)
        break

engine = create_async_engine(database_url, future=True, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
