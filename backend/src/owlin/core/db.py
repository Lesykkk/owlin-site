from collections.abc import AsyncIterator
from datetime import datetime
from functools import lru_cache

from sqlalchemy import Column, DateTime, Table, Text, Uuid
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from owlin.core.config import get_settings


class Base(DeclarativeBase):
    """Base class of all ORM models."""

    # Every str column is text and every datetime column is timestamptz.
    type_annotation_map = {str: Text(), datetime: DateTime(timezone=True)}


# Stand-in for Supabase's own auth.users so foreign keys to it can be declared.
# Alembic ignores it (it only manages the public schema), so it is never created.
auth_users = Table("users", Base.metadata, Column("id", Uuid, primary_key=True), schema="auth")


@lru_cache
def get_engine() -> AsyncEngine:
    database_url = get_settings().database_url
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    return create_async_engine(
        database_url,
        pool_pre_ping=True,
        # Keeps working if the URL ever points at Supabase's transaction pooler (port 6543),
        # which cannot reuse prepared statements.
        connect_args={"statement_cache_size": 0, "prepared_statement_cache_size": 0},
    )


@lru_cache
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_engine(), expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: one session per request. Services commit explicitly."""
    async with get_sessionmaker()() as session:
        yield session
