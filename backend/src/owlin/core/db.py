from collections.abc import AsyncIterator
from datetime import datetime
from functools import lru_cache

from sqlalchemy import Column, DateTime, MetaData, Table, Text, Uuid
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from owlin.core.config import get_settings


class Base(DeclarativeBase):
    """Base class of all ORM models."""

    # Gives every new constraint a predictable name (named CheckConstraints become ck_<table>_<name>).
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )

    # Every str column is text and every datetime column is timestamptz.
    type_annotation_map = {str: Text(), datetime: DateTime(timezone=True)}


# Stand-in for Supabase's own auth.users so foreign keys to it can be declared.
# Alembic ignores it (it only manages the public schema), so it is never created.
auth_users = Table("users", Base.metadata, Column("id", Uuid, primary_key=True), schema="auth")


def in_list(column: str, values: tuple[str, ...]) -> str:
    """SQL text of a CHECK that limits a column to the given values."""
    return f"{column} IN ({', '.join(repr(value) for value in values)})"


@lru_cache
def get_engine() -> AsyncEngine:
    database_url = get_settings().database_url
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    return create_async_engine(
        database_url,
        pool_pre_ping=True,
        # Supabase's session pooler allows 15 clients in total, shared with Storage, the dashboard and
        # the release command. Staying at 5 with no overflow means a burst of requests waits for a
        # free connection instead of being refused by the pooler with a 500.
        pool_size=5,
        max_overflow=0,
        pool_timeout=30,
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
