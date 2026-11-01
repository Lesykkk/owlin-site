from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from owlin.api.app import app
from owlin.api.deps import get_current_user, get_settings, get_storage
from owlin.core.config import Settings
from owlin.core.errors import ConflictError, InvalidRequestError, NotFoundError
from owlin.core.security import TokenUser
from owlin.modules.balance.models import BalanceTransaction
from owlin.modules.orders import review
from owlin.modules.orders.models import Order
from owlin.modules.subscriptions.models import SubscriptionGrant, UserSubscription
from owlin.modules.users import service as users
from tests.conftest import ServiceSession

NOW = datetime(2026, 10, 29, 12, 0, tzinfo=UTC)
ADMIN_ID = uuid4()


def make_order(**overrides: object) -> Order:
    values = dict(
        id=uuid4(), user_id=uuid4(), product="spoofer", period="1m", method="paypal", coin=None,
        amount_cents=400, status="review", created_at=NOW,
    )  # fmt: skip
    return Order(**{**values, **overrides})


def make_subscription(user_id, **values: object) -> UserSubscription:
    defaults = dict(
        spoofer_access=False, spoofer_expires_at=None, dlc_access=False, dlc_expires_at=None,
        ets2_access=False, ets2_expires_at=None, ets2mp_access=False, ets2mp_expires_at=None,
    )  # fmt: skip
    return UserSubscription(user_id=user_id, **{**defaults, **values})


def session_for(order: Order) -> ServiceSession:
    return ServiceSession({Order: order, UserSubscription: make_subscription(order.user_id)})


class TestApprove:
    @pytest.mark.asyncio
    async def test_exact_payment_grants_the_plan_and_adds_nothing_to_the_balance(self) -> None:
        order = make_order()
        session = session_for(order)

        result = await review.approve_order(session, order.id, ADMIN_ID, 400, now=NOW)

        assert result.status == "approved"
        assert result.received_cents == 400
        assert result.balance_added_cents == 0
        assert (result.reviewed_by, result.reviewed_at) == (ADMIN_ID, NOW)
        assert session.objects[UserSubscription].spoofer_expires_at == NOW + timedelta(days=30)
        assert session.added_of(BalanceTransaction) == []
        assert session.committed is True

    @pytest.mark.asyncio
    async def test_surplus_goes_to_the_balance_and_is_linked_to_the_order(self) -> None:
        order = make_order()
        session = session_for(order)

        result = await review.approve_order(session, order.id, ADMIN_ID, 550, now=NOW)

        assert result.balance_added_cents == 150
        [transaction] = session.added_of(BalanceTransaction)
        assert (transaction.amount_cents, transaction.reason) == (150, "order_overpay")
        assert (transaction.user_id, transaction.order_id) == (order.user_id, order.id)

    @pytest.mark.asyncio
    async def test_a_bundle_grants_every_module_and_records_who_approved(self) -> None:
        order = make_order(product="spoofer-dlc-unlock", period="3m", amount_cents=1300)
        session = session_for(order)

        await review.approve_order(session, order.id, ADMIN_ID, 1300, now=NOW)

        subscription = session.objects[UserSubscription]
        assert subscription.spoofer_expires_at == NOW + timedelta(days=90)
        assert subscription.dlc_expires_at == NOW + timedelta(days=90)
        grants = session.added_of(SubscriptionGrant)
        assert {grant.product for grant in grants} == {"spoofer", "dlc-unlock"}
        assert all(grant.order_id == order.id and grant.granted_by == ADMIN_ID for grant in grants)

    @pytest.mark.asyncio
    async def test_a_lifetime_order_leaves_no_end_date(self) -> None:
        order = make_order(product="dlc-unlock", period="lifetime", amount_cents=1099)
        session = session_for(order)

        await review.approve_order(session, order.id, ADMIN_ID, 1099, now=NOW)

        subscription = session.objects[UserSubscription]
        assert subscription.dlc_access is True
        assert subscription.dlc_expires_at is None

    @pytest.mark.asyncio
    async def test_less_than_the_price_changes_nothing(self) -> None:
        order = make_order()
        session = session_for(order)

        with pytest.raises(InvalidRequestError):
            await review.approve_order(session, order.id, ADMIN_ID, 399, now=NOW)

        assert order.status == "review"
        assert session.added == []
        assert session.committed is False

    @pytest.mark.asyncio
    @pytest.mark.parametrize("status", ["approved", "rejected"])
    async def test_only_orders_under_review_can_be_approved(self, status: str) -> None:
        order = make_order(status=status)

        with pytest.raises(ConflictError):
            await review.approve_order(session_for(order), order.id, ADMIN_ID, 400, now=NOW)

    @pytest.mark.asyncio
    async def test_unknown_order(self) -> None:
        with pytest.raises(NotFoundError):
            await review.approve_order(ServiceSession(), uuid4(), ADMIN_ID, 400, now=NOW)


class TestReject:
    @pytest.mark.asyncio
    async def test_records_the_reason_and_the_reviewer(self) -> None:
        order = make_order()
        session = session_for(order)

        result = await review.reject_order(session, order.id, ADMIN_ID, "  Amount does not match.  ", now=NOW)

        assert result.status == "rejected"
        assert result.reject_reason == "Amount does not match."
        assert (result.reviewed_by, result.reviewed_at) == (ADMIN_ID, NOW)
        assert session.added == []
        assert session.committed is True

    @pytest.mark.asyncio
    async def test_an_approved_order_cannot_be_rejected(self) -> None:
        order = make_order(status="approved")

        with pytest.raises(ConflictError):
            await review.reject_order(session_for(order), order.id, ADMIN_ID, "late", now=NOW)


ADMIN = TokenUser(id=ADMIN_ID, username="Admin", avatar_url=None)


class TestAdminEndpoints:
    @pytest.fixture
    def sign_in(self, monkeypatch: pytest.MonkeyPatch, use_session):
        def configure(discord_id: str | None, admins: list[str]) -> None:
            async def get_account(_session, _user_id):
                return users.Account(discord_id=discord_id, created_at=NOW)

            monkeypatch.setattr(users, "get_account", get_account)
            app.dependency_overrides[get_current_user] = lambda: ADMIN
            app.dependency_overrides[get_settings] = lambda: Settings(admin_discord_ids=admins)
            app.dependency_overrides[get_storage] = lambda: object()
            use_session(ServiceSession())

        return configure

    @pytest.mark.asyncio
    async def test_needs_a_token(self, client) -> None:
        assert (await client.get("/api/admin/orders")).status_code == 401

    @pytest.mark.asyncio
    @pytest.mark.parametrize("discord_id", ["999", None])
    async def test_a_regular_user_is_forbidden(self, client, sign_in, discord_id) -> None:
        sign_in(discord_id, admins=["123"])

        for method, path in [("get", "/api/admin/orders"), ("post", f"/api/admin/orders/{uuid4()}/approve")]:
            response = await getattr(client, method)(path, **({"json": {"received_cents": 100}} if method == "post" else {}))
            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_an_empty_admin_list_locks_everyone_out(self, client, sign_in) -> None:
        sign_in("123", admins=[])

        assert (await client.get("/api/admin/orders")).status_code == 403

    @pytest.mark.asyncio
    @pytest.mark.parametrize("status, expected", [("review", "review"), ("all", None), (None, "review")])
    async def test_list_passes_the_status_filter(self, client, sign_in, monkeypatch, status, expected) -> None:
        sign_in("123", admins=["123"])
        seen = []

        async def fake_list(_session, _storage, requested):
            seen.append(requested)
            return []

        monkeypatch.setattr(review, "list_orders_for_admin", fake_list)

        response = await client.get("/api/admin/orders", params={"status": status} if status else {})

        assert response.status_code == 200
        assert seen == [expected]

    @pytest.mark.asyncio
    async def test_an_unknown_status_is_rejected(self, client, sign_in) -> None:
        sign_in("123", admins=["123"])

        assert (await client.get("/api/admin/orders", params={"status": "pending"})).status_code == 422

    @pytest.mark.asyncio
    async def test_review_errors_become_http_errors(self, client, sign_in, monkeypatch) -> None:
        sign_in("123", admins=["123"])

        async def conflict(*_args):
            raise ConflictError("Only orders under review can be approved")

        monkeypatch.setattr(review, "approve_order", conflict)

        response = await client.post(f"/api/admin/orders/{uuid4()}/approve", json={"received_cents": 400})

        assert response.status_code == 409
        assert response.json() == {"detail": "Only orders under review can be approved"}

    @pytest.mark.asyncio
    async def test_the_received_amount_must_be_positive_and_a_reason_is_required(self, client, sign_in) -> None:
        sign_in("123", admins=["123"])

        assert (await client.post(f"/api/admin/orders/{uuid4()}/approve", json={"received_cents": 0})).status_code == 422
        assert (await client.post(f"/api/admin/orders/{uuid4()}/reject", json={"reason": ""})).status_code == 422
