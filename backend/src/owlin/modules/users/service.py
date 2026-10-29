from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import ARRAY, Uuid, bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True)
class Account:
    """Facts about a user that only the server can set (read from Supabase's auth schema)."""

    discord_id: str | None
    created_at: datetime


@dataclass(frozen=True)
class Profile:
    """How a user shows up in the admin lists. The name and avatar are user-editable, display only."""

    username: str
    avatar_url: str | None
    discord_id: str | None


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


async def get_profiles(session: AsyncSession, user_ids: list[UUID]) -> dict[UUID, Profile]:
    """Names, avatars and Discord ids of several users in one query."""
    if not user_ids:
        return {}

    statement = text(
        """
        select
            u.id,
            coalesce(
                u.raw_user_meta_data -> 'custom_claims' ->> 'global_name',
                u.raw_user_meta_data ->> 'full_name',
                u.raw_user_meta_data ->> 'name',
                'User'
            ) as username,
            u.raw_user_meta_data ->> 'avatar_url' as avatar_url,
            i.provider_id as discord_id
        from auth.users u
        left join auth.identities i on i.user_id = u.id and i.provider = 'discord'
        where u.id = any(:ids)
        """
    ).bindparams(bindparam("ids", type_=ARRAY(Uuid)))

    result = await session.execute(statement, {"ids": list(set(user_ids))})
    return {
        row.id: Profile(username=row.username, avatar_url=row.avatar_url, discord_id=row.discord_id)
        for row in result.all()
    }
