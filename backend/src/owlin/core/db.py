from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from owlin.core.config import get_settings


class Base(DeclarativeBase):
    """Base class of all ORM models."""


@lru_cache
def get_engine() -> AsyncEngine:
    database_url = get_settings().database_url
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    return create_async_engine(
        database_url,
        pool_pre_ping=True,
        # Supabase's transaction pooler (port 6543) cannot reuse prepared statements.
        connect_args={"statement_cache_size": 0, "prepared_statement_cache_size": 0},
    )


@lru_cache
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_engine(), expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: one session per request. Services commit explicitly."""
    async with get_sessionmaker()() as session:
        yield session
