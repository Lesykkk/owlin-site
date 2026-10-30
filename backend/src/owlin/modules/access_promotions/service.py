"""Which global promotions are running, worked out the same way as the loader's authorize_session_v3.

Only the sold modules are reported. ETS2 and ETS2 Multiplayer are free for everyone through
user_subscriptions, so a promotion flag for them is never shown.
"""

import time as clock
from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from owlin.modules.access_promotions.models import AccessPromotion
from owlin.modules.access_promotions.schemas import ActivePromotion

# Promotion flag for each module the site sells.
SOLD_MODULE_FLAGS = {"spoofer": "spoofer_access", "dlc-unlock": "dlc_access"}

SECONDS_PER_DAY = 86400
SECONDS_PER_WEEK = 7 * SECONDS_PER_DAY
# Promotions change rarely, so the rows are kept for a short while instead of read on every visit.
CACHE_SECONDS = 30


@dataclass(frozen=True)
class PromotionRow:
    """The fields of an access_promotions row that decide whether it is running."""

    name: str
    promotion_type: str
    timezone: str
    spoofer_access: bool
    dlc_access: bool
    starts_at: datetime | None
    ends_at: datetime | None
    start_day: int | None
    end_day: int | None
    start_time: time | None
    end_time: time | None


def _aware(moment: datetime) -> datetime:
    return moment if moment.tzinfo else moment.replace(tzinfo=UTC)


def _seconds_into_day(moment: time) -> int:
    return moment.hour * 3600 + moment.minute * 60 + moment.second


def window_end(row: PromotionRow, now: datetime) -> datetime | None:
    """The end of the window that is open at `now`, or None when the promotion is not running."""
    if row.promotion_type == "date_range":
        # An open start or end never matches, as in the database function.
        if row.starts_at is None or row.ends_at is None:
            return None
        starts_at, ends_at = _aware(row.starts_at), _aware(row.ends_at)
        return ends_at if starts_at <= now < ends_at else None

    if row.promotion_type == "weekly":
        if None in (row.start_day, row.end_day, row.start_time, row.end_time):
            return None
        zone = ZoneInfo(row.timezone)
        local_now = now.astimezone(zone)
        # Days count from Sunday = 0, like Postgres' extract(dow).
        current = ((local_now.weekday() + 1) % 7) * SECONDS_PER_DAY + _seconds_into_day(local_now.time())
        start = row.start_day * SECONDS_PER_DAY + _seconds_into_day(row.start_time)
        end = row.end_day * SECONDS_PER_DAY + _seconds_into_day(row.end_time)
        if start < end:
            is_open = start <= current < end
        elif start > end:
            # The window wraps around the end of the week.
            is_open = current >= start or current < end
        else:
            is_open = False
        if not is_open:
            return None
        until_end = (end - current) % SECONDS_PER_WEEK
        # Add the seconds on the wall clock, then read the result back in the promotion's time zone.
        wall_end = local_now.replace(tzinfo=None) + timedelta(seconds=until_end)
        return wall_end.replace(tzinfo=zone).astimezone(UTC)

    return None


def active_promotions(rows: list[PromotionRow], now: datetime) -> list[ActivePromotion]:
    """Running promotions that open at least one sold module, with only those modules listed."""
    active: list[ActivePromotion] = []
    for row in rows:
        ends_at = window_end(row, now)
        if ends_at is None:
            continue
        modules = [module for module, flag in SOLD_MODULE_FLAGS.items() if getattr(row, flag)]
        if modules:
            active.append(ActivePromotion(name=row.name, modules=modules, ends_at=ends_at))
    return sorted(active, key=lambda promotion: promotion.ends_at)


_cache: tuple[float, list[PromotionRow]] | None = None


def clear_cache() -> None:
    global _cache
    _cache = None


async def load_rows(session: AsyncSession) -> list[PromotionRow]:
    global _cache
    if _cache is not None and clock.monotonic() - _cache[0] < CACHE_SECONDS:
        return _cache[1]
    result = await session.scalars(select(AccessPromotion).where(AccessPromotion.is_active.is_(True)))
    rows = [
        PromotionRow(
            name=promotion.name,
            promotion_type=promotion.promotion_type,
            timezone=promotion.timezone,
            spoofer_access=promotion.spoofer_access,
            dlc_access=promotion.dlc_access,
            starts_at=promotion.starts_at,
            ends_at=promotion.ends_at,
            start_day=promotion.start_day,
            end_day=promotion.end_day,
            start_time=promotion.start_time,
            end_time=promotion.end_time,
        )
        for promotion in result
    ]
    _cache = (clock.monotonic(), rows)
    return rows


async def list_active(session: AsyncSession, now: datetime) -> list[ActivePromotion]:
    return active_promotions(await load_rows(session), now)
