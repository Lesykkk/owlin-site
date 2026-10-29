from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from owlin.modules.catalog.constants import PRODUCTS
from owlin.modules.subscriptions.models import SubscriptionGrant, UserSubscription
from owlin.modules.subscriptions.schemas import SubscriptionInfo

# Column prefix of each module in user_subscriptions (spoofer_access, dlc_expires_at, ...).
MODULE_COLUMNS = {"spoofer": "spoofer", "dlc-unlock": "dlc"}


class UnknownProductError(ValueError):
    """The product id is not in the catalog."""


@dataclass(frozen=True)
class GrantPlan:
    """What a grant does to one module of a user_subscriptions row."""

    access: bool
    expires_at: datetime | None  # new value of <module>_expires_at, None = no end date
    starts_at: datetime  # when this grant takes effect
    ends_at: datetime | None  # when this grant runs out, None = no end date


def plan_grant(access: bool, expires_at: datetime | None, days: int | None, now: datetime) -> GrantPlan:
    """Work out the effect of granting `days` days (None = no end date) on one module.

    A new grant starts when the current access ends, so purchases stack instead of overlapping.
    Access that never ends stays that way: a time-limited grant adds nothing to it.
    """
    is_active = access and (expires_at is None or expires_at > now)

    if days is None:
        return GrantPlan(access=True, expires_at=None, starts_at=now, ends_at=None)

    if is_active and expires_at is None:
        return GrantPlan(access=True, expires_at=None, starts_at=now, ends_at=now + timedelta(days=days))

    starts_at = expires_at if is_active else now
    ends_at = starts_at + timedelta(days=days)
    return GrantPlan(access=True, expires_at=ends_at, starts_at=starts_at, ends_at=ends_at)


async def get_overview(
    session: AsyncSession, user_id: UUID, now: datetime | None = None
) -> dict[str, SubscriptionInfo]:
    """Whether each module is active for the user, and until when. No lock, read only."""
    now = now or datetime.now(UTC)
    subscription = await session.get(UserSubscription, user_id)

    overview = {}
    for module, prefix in MODULE_COLUMNS.items():
        access = bool(subscription and getattr(subscription, f"{prefix}_access"))
        expires_at = subscription and getattr(subscription, f"{prefix}_expires_at")
        active = access and (expires_at is None or expires_at > now)
        overview[module] = SubscriptionInfo(
            active=active,
            expires_at=expires_at if active else None,
            lifetime=active and expires_at is None,
        )
    return overview


async def get_subscription_for_update(session: AsyncSession, user_id: UUID) -> UserSubscription:
    """Load the user's row and lock it until the transaction ends, so grants cannot interleave."""
    subscription = await session.get(UserSubscription, user_id, with_for_update=True)
    if subscription is None:
        # A database trigger normally creates the row when the auth user is created.
        subscription = UserSubscription(
            user_id=user_id,
            spoofer_access=False,
            dlc_access=False,
            ets2_access=False,
            ets2mp_access=False,
        )
        session.add(subscription)
    return subscription


async def grant_product(
    session: AsyncSession,
    *,
    user_id: UUID,
    product_id: str,
    days: int | None,
    source: str,
    order_id: UUID | None = None,
    promo_claim_id: UUID | None = None,
    granted_by: UUID | None = None,
    now: datetime | None = None,
) -> list[SubscriptionGrant]:
    """Give a user every module of a product and record one grant per module.

    Does not commit: the caller does it in the same transaction as whatever caused the grant
    (approving an order, approving a promo video), so either everything happens or nothing does.
    """
    modules = PRODUCTS.get(product_id)
    if modules is None:
        raise UnknownProductError(product_id)

    now = now or datetime.now(UTC)
    subscription = await get_subscription_for_update(session, user_id)
    grants = []

    for module in modules:
        prefix = MODULE_COLUMNS[module]
        plan = plan_grant(
            access=getattr(subscription, f"{prefix}_access"),
            expires_at=getattr(subscription, f"{prefix}_expires_at"),
            days=days,
            now=now,
        )
        setattr(subscription, f"{prefix}_access", plan.access)
        setattr(subscription, f"{prefix}_expires_at", plan.expires_at)

        grant = SubscriptionGrant(
            user_id=user_id,
            product=module,
            source=source,
            order_id=order_id,
            promo_claim_id=promo_claim_id,
            granted_by=granted_by,
            days=days,
            starts_at=plan.starts_at,
            ends_at=plan.ends_at,
        )
        session.add(grant)
        grants.append(grant)

    subscription.updated_at = now
    await session.flush()
    return grants
