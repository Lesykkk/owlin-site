from types import SimpleNamespace
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from owlin.api.app import app
from owlin.api.deps import get_current_user
from owlin.core.config import Settings, get_settings
from owlin.core.security import AuthenticationError, TokenUser
from owlin.modules.overview import service as overview_service
from owlin.modules.overview.service import Overview
from owlin.modules.subscriptions import service as subscriptions
from owlin.modules.subscriptions.models import UserSubscription
from owlin.modules.subscriptions.schemas import SubscriptionInfo
from tests.conftest import ServiceSession

USER = TokenUser(id=uuid4(), username="Pedro", avatar_url="https://cdn.example/a.png")
CREATED_AT = datetime(2026, 1, 5, 12, 0, tzinfo=UTC)
LAST_SEEN = datetime(2026, 10, 28, 9, 0, tzinfo=UTC)
NOW = datetime(2026, 10, 29, 12, 0, tzinfo=UTC)


@pytest.fixture
def profile(monkeypatch: pytest.MonkeyPatch):
    """Signs in as USER and fakes the overview /api/me reads. Returns a setter for the Discord id."""
    state = {"discord_id": "123", "admins": []}

    async def load_overview(_session, _user_id, _now):
        if state["discord_id"] == "missing":
            return None
        return Overview(
            discord_id=state["discord_id"],
            created_at=CREATED_AT,
            subscriptions={
                "spoofer": SubscriptionInfo(active=True, expires_at=NOW + timedelta(days=20), lifetime=False),
                "dlc-unlock": SubscriptionInfo(active=False, expires_at=None, lifetime=False),
            },
            balance_cents=350,
            last_seen_at=LAST_SEEN,
        )

    monkeypatch.setattr(overview_service, "load_overview", load_overview)
    app.dependency_overrides[get_current_user] = lambda: USER
    app.dependency_overrides[get_settings] = lambda: Settings(admin_discord_ids=state["admins"])

    def configure(discord_id: str = "123", admins: list[str] | None = None) -> None:
        state["discord_id"] = discord_id
        state["admins"] = admins or []

    return configure


@pytest.mark.asyncio
async def test_me_requires_a_token(client) -> None:
    response = await client.get("/api/me")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.asyncio
async def test_me_rejects_an_invalid_token(client, monkeypatch) -> None:
    async def reject(_token: str):
        raise AuthenticationError

    monkeypatch.setattr("owlin.api.deps.verify_token", reject)

    response = await client.get("/api/me", headers={"Authorization": "Bearer nope"})

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_returns_the_whole_overview(client, use_session, profile) -> None:
    use_session(ServiceSession())

    response = await client.get("/api/me")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(USER.id)
    assert body["username"] == "Pedro"
    assert body["discord_id"] == "123"
    assert body["is_admin"] is False
    assert body["balance_cents"] == 350
    assert "promo_slots" not in body
    assert body["last_seen_at"] == "2026-10-28T09:00:00Z"
    assert body["subscriptions"]["spoofer"]["active"] is True
    assert body["subscriptions"]["spoofer"]["lifetime"] is False
    assert body["subscriptions"]["dlc-unlock"] == {"active": False, "started_at": None, "expires_at": None, "lifetime": False}


@pytest.mark.asyncio
async def test_me_marks_configured_discord_ids_as_admin(client, use_session, profile) -> None:
    profile(discord_id="123", admins=["123"])
    use_session(ServiceSession())

    assert (await client.get("/api/me")).json()["is_admin"] is True


@pytest.mark.asyncio
async def test_me_is_not_admin_without_a_discord_identity(client, use_session, profile, monkeypatch) -> None:
    profile(admins=["123"])

    async def no_discord(_session, _user_id, _now):
        return Overview(
            discord_id=None, created_at=CREATED_AT, subscriptions={}, balance_cents=0, last_seen_at=None
        )

    monkeypatch.setattr(overview_service, "load_overview", no_discord)
    use_session(ServiceSession())

    assert (await client.get("/api/me")).json()["is_admin"] is False


@pytest.mark.asyncio
async def test_me_rejects_a_user_missing_from_the_database(client, use_session, profile) -> None:
    profile(discord_id="missing")
    use_session(ServiceSession())

    assert (await client.get("/api/me")).status_code == 401


class TestSubscriptionOverview:
    @pytest.mark.asyncio
    async def test_reports_active_expired_and_lifetime_modules(self) -> None:
        subscription = UserSubscription(
            user_id=uuid4(),
            spoofer_access=True,
            spoofer_expires_at=NOW + timedelta(days=5),
            dlc_access=True,
            dlc_expires_at=None,
        )
        session = ServiceSession({UserSubscription: subscription})

        overview = await subscriptions.get_overview(session, subscription.user_id, NOW)

        assert overview["spoofer"] == SubscriptionInfo(active=True, expires_at=NOW + timedelta(days=5), lifetime=False)
        assert overview["dlc-unlock"] == SubscriptionInfo(active=True, expires_at=None, lifetime=True)

    @pytest.mark.asyncio
    async def test_started_at_comes_from_the_earliest_unfinished_grant(self) -> None:
        subscription = UserSubscription(
            user_id=uuid4(), spoofer_access=True, spoofer_expires_at=NOW + timedelta(days=5), dlc_access=False
        )
        session = ServiceSession({UserSubscription: subscription})
        session.execute_rows = [("spoofer", NOW - timedelta(days=25)), ("dlc-unlock", NOW - timedelta(days=3))]

        overview = await subscriptions.get_overview(session, subscription.user_id, NOW)

        assert overview["spoofer"].started_at == NOW - timedelta(days=25)
        # DLC is not active, so a stale start date is not reported.
        assert overview["dlc-unlock"].started_at is None

    @pytest.mark.asyncio
    async def test_an_expired_or_disabled_module_is_inactive_without_a_date(self) -> None:
        subscription = UserSubscription(
            user_id=uuid4(),
            spoofer_access=True,
            spoofer_expires_at=NOW - timedelta(days=1),
            dlc_access=False,
            dlc_expires_at=NOW + timedelta(days=9),
        )
        session = ServiceSession({UserSubscription: subscription})

        overview = await subscriptions.get_overview(session, subscription.user_id, NOW)

        inactive = SubscriptionInfo(active=False, expires_at=None, lifetime=False)
        assert overview["spoofer"] == inactive
        assert overview["dlc-unlock"] == inactive

    @pytest.mark.asyncio
    async def test_a_user_without_a_row_has_nothing_active(self) -> None:
        overview = await subscriptions.get_overview(ServiceSession(), uuid4(), NOW)

        assert not any(info.active for info in overview.values())


class FakeRow:
    def __init__(self, **values: object) -> None:
        self._mapping = values


class OverviewSession:
    def __init__(self, row: FakeRow | None) -> None:
        self.row = row
        self.queries = 0

    async def execute(self, _statement: object, _params: object = None):
        self.queries += 1
        return SimpleNamespace(one_or_none=lambda: self.row)


class TestLoadOverview:
    def row(self, **overrides: object) -> FakeRow:
        values = dict(
            created_at=CREATED_AT, discord_id="123",
            spoofer_access=True, spoofer_expires_at=NOW + timedelta(days=5), spoofer_started_at=NOW - timedelta(days=25),
            dlc_access=True, dlc_expires_at=None, dlc_started_at=None,
            balance_cents=350, last_seen_at=LAST_SEEN,
        )  # fmt: skip
        return FakeRow(**{**values, **overrides})

    @pytest.mark.asyncio
    async def test_reads_everything_in_one_query(self) -> None:
        session = OverviewSession(self.row())

        overview = await overview_service.load_overview(session, uuid4(), NOW)

        assert session.queries == 1
        assert (overview.discord_id, overview.balance_cents) == ("123", 350)
        assert overview.last_seen_at == LAST_SEEN
        assert overview.subscriptions["spoofer"] == SubscriptionInfo(
            active=True, started_at=NOW - timedelta(days=25), expires_at=NOW + timedelta(days=5), lifetime=False
        )
        assert overview.subscriptions["dlc-unlock"].lifetime is True

    @pytest.mark.asyncio
    async def test_a_user_without_a_subscription_row_has_nothing_active(self) -> None:
        row = self.row(
            spoofer_access=None, spoofer_expires_at=None, spoofer_started_at=None,
            dlc_access=None, dlc_expires_at=None, dlc_started_at=None, last_seen_at=None,
        )  # fmt: skip

        overview = await overview_service.load_overview(OverviewSession(row), uuid4(), NOW)

        assert not any(info.active for info in overview.subscriptions.values())
        assert overview.last_seen_at is None

    @pytest.mark.asyncio
    async def test_an_unknown_user_gives_none(self) -> None:
        assert await overview_service.load_overview(OverviewSession(None), uuid4(), NOW) is None

    def test_the_query_covers_every_module(self) -> None:
        sql = str(overview_service.QUERY)

        for prefix in ("spoofer", "dlc"):
            assert f"{prefix}_access" in sql and f"{prefix}_started_at" in sql
