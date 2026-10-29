from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from owlin.modules.subscriptions.models import SubscriptionGrant, UserSubscription
from owlin.modules.subscriptions.service import UnknownProductError, grant_product, plan_grant

NOW = datetime(2026, 10, 29, 12, 0, tzinfo=UTC)


def days(count: int) -> timedelta:
    return timedelta(days=count)


class TestPlanGrant:
    def test_starts_now_without_access(self) -> None:
        plan = plan_grant(access=False, expires_at=None, days=30, now=NOW)

        assert plan.access is True
        assert plan.starts_at == NOW
        assert plan.ends_at == plan.expires_at == NOW + days(30)

    def test_starts_now_when_access_has_expired(self) -> None:
        plan = plan_grant(access=True, expires_at=NOW - days(5), days=30, now=NOW)

        assert plan.starts_at == NOW
        assert plan.expires_at == NOW + days(30)

    def test_ignores_the_old_end_date_when_access_is_off(self) -> None:
        plan = plan_grant(access=False, expires_at=NOW + days(10), days=30, now=NOW)

        assert plan.expires_at == NOW + days(30)

    def test_stacks_after_the_current_end_date(self) -> None:
        current_end = NOW + days(10)

        plan = plan_grant(access=True, expires_at=current_end, days=30, now=NOW)

        assert plan.starts_at == current_end
        assert plan.expires_at == current_end + days(30)

    def test_lifetime_has_no_end_date(self) -> None:
        plan = plan_grant(access=False, expires_at=None, days=None, now=NOW)

        assert plan.access is True
        assert plan.expires_at is None
        assert plan.ends_at is None

    def test_lifetime_replaces_a_time_limited_subscription(self) -> None:
        plan = plan_grant(access=True, expires_at=NOW + days(10), days=None, now=NOW)

        assert plan.expires_at is None

    def test_time_limited_grant_does_not_shorten_lifetime(self) -> None:
        plan = plan_grant(access=True, expires_at=None, days=30, now=NOW)

        assert plan.expires_at is None


class FakeSession:
    """Just enough of AsyncSession for grant_product."""

    def __init__(self, subscription: UserSubscription | None) -> None:
        self.subscription = subscription
        self.added: list[object] = []
        self.locked = False

    async def get(self, _model: type, _key: object, with_for_update: bool = False) -> UserSubscription | None:
        self.locked = with_for_update
        return self.subscription

    def add(self, item: object) -> None:
        self.added.append(item)
        if isinstance(item, UserSubscription):
            self.subscription = item

    async def flush(self) -> None:
        pass


def make_subscription(user_id, **values: object) -> UserSubscription:
    defaults = {
        "spoofer_access": False,
        "spoofer_expires_at": None,
        "dlc_access": False,
        "dlc_expires_at": None,
        "ets2_access": False,
        "ets2_expires_at": None,
        "ets2mp_access": False,
        "ets2mp_expires_at": None,
    }
    return UserSubscription(user_id=user_id, **{**defaults, **values})


@pytest.mark.asyncio
async def test_single_product_updates_only_its_module() -> None:
    user_id = uuid4()
    session = FakeSession(make_subscription(user_id))

    grants = await grant_product(session, user_id=user_id, product_id="spoofer", days=30, source="admin", now=NOW)

    assert session.locked is True
    assert session.subscription.spoofer_access is True
    assert session.subscription.spoofer_expires_at == NOW + days(30)
    assert session.subscription.dlc_access is False
    assert [grant.product for grant in grants] == ["spoofer"]


@pytest.mark.asyncio
async def test_bundle_grants_every_module_it_contains() -> None:
    user_id = uuid4()
    order_id = uuid4()
    session = FakeSession(make_subscription(user_id, dlc_access=True, dlc_expires_at=NOW + days(10)))

    grants = await grant_product(
        session, user_id=user_id, product_id="spoofer-dlc-unlock", days=30, source="order", order_id=order_id, now=NOW
    )

    subscription = session.subscription
    assert subscription.spoofer_expires_at == NOW + days(30)
    # DLC was already active, so the new days stack after its current end.
    assert subscription.dlc_expires_at == NOW + days(40)
    assert {grant.product for grant in grants} == {"spoofer", "dlc-unlock"}
    assert all(grant.order_id == order_id and grant.source == "order" for grant in grants)


@pytest.mark.asyncio
async def test_lifetime_grant_is_recorded_without_end_date() -> None:
    user_id = uuid4()
    session = FakeSession(make_subscription(user_id))

    grants = await grant_product(session, user_id=user_id, product_id="dlc-unlock", days=None, source="admin", now=NOW)

    assert session.subscription.dlc_access is True
    assert session.subscription.dlc_expires_at is None
    assert grants[0].days is None
    assert grants[0].ends_at is None


@pytest.mark.asyncio
async def test_missing_subscription_row_is_created() -> None:
    user_id = uuid4()
    session = FakeSession(None)

    await grant_product(session, user_id=user_id, product_id="spoofer", days=7, source="admin", now=NOW)

    assert session.subscription.user_id == user_id
    assert session.subscription.spoofer_access is True
    assert session.subscription.dlc_access is False


@pytest.mark.asyncio
async def test_unknown_product_is_rejected_before_touching_anything() -> None:
    session = FakeSession(None)

    with pytest.raises(UnknownProductError):
        await grant_product(session, user_id=uuid4(), product_id="nope", days=30, source="admin", now=NOW)

    assert session.added == []
