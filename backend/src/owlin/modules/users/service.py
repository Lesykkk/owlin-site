from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True)
class Account:
    """Facts about a user that only the server can set (read from Supabase's auth schema)."""

    discord_id: str | None
    created_at: datetime


async def get_account(session: AsyncSession, user_id: UUID) -> Account | None:
    result = await session.execute(
        text(
            """
            select u.created_at, i.provider_id as discord_id
            from auth.users u
            left join auth.identities i on i.user_id = u.id and i.provider = 'discord'
            where u.id = :user_id
            """
        ),
        {"user_id": user_id},
    )
    row = result.one_or_none()
    if row is None:
        return None
    return Account(discord_id=row.discord_id, created_at=row.created_at)
