"""Everything /api/me shows about a user, read in a single database round trip.

The same facts are available from the individual modules (users, subscriptions, balance, promo,
devices), but asking each one separately costs one network round trip apiece. That adds up
quickly, so this module reads them all with one query instead.
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from owlin.modules.subscriptions.schemas import SubscriptionInfo
from owlin.modules.subscriptions.service import MODULE_COLUMNS, build_info


@dataclass(frozen=True)
class Overview:
    discord_id: str | None
    created_at: datetime
    subscriptions: dict[str, SubscriptionInfo]
    balance_cents: int
    promo_slots_used: int
    last_seen_at: datetime | None


def _subscription_columns() -> str:
    """Select list with each module's access, end date and the start of its current access."""
    return ",\n".join(
        f"""
            s.{prefix}_access as {prefix}_access,
            s.{prefix}_expires_at as {prefix}_expires_at,
            (
                select min(g.starts_at) from public.subscription_grants g
                where g.user_id = u.id and g.product = '{module}' and (g.ends_at is null or g.ends_at > :now)
            ) as {prefix}_started_at"""
        for module, prefix in MODULE_COLUMNS.items()
    )


# Built once from the module list, so a new module needs no change here.
QUERY = text(
    f"""
    select
        u.created_at,
        i.provider_id as discord_id,
        {_subscription_columns()},
        (select coalesce(sum(b.amount_cents), 0) from public.balance_transactions b where b.user_id = u.id)
            as balance_cents,
        (
            select count(*) from public.promo_claims c
            where c.user_id = u.id
              and (c.status = 'review' or (c.status = 'approved' and c.expires_at > :now))
        ) as promo_slots_used,
        (select max(d.last_seen_at) from public.user_devices d where d.user_id = u.id) as last_seen_at
    from auth.users u
    left join auth.identities i on i.user_id = u.id and i.provider = 'discord'
    left join public.user_subscriptions s on s.user_id = u.id
    where u.id = :user_id
    """
)


async def load_overview(session: AsyncSession, user_id: UUID, now: datetime) -> Overview | None:
    """The user's overview, or None if there is no such user."""
    result = await session.execute(QUERY, {"user_id": user_id, "now": now})
    row = result.one_or_none()
    if row is None:
        return None

    columns = row._mapping
    return Overview(
        discord_id=columns["discord_id"],
        created_at=columns["created_at"],
        subscriptions={
            module: build_info(
                access=columns[f"{prefix}_access"],
                expires_at=columns[f"{prefix}_expires_at"],
                started_at=columns[f"{prefix}_started_at"],
                now=now,
            )
            for module, prefix in MODULE_COLUMNS.items()
        },
        balance_cents=int(columns["balance_cents"]),
        promo_slots_used=int(columns["promo_slots_used"]),
        last_seen_at=columns["last_seen_at"],
    )
