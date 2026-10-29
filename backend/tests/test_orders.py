from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from owlin.api.app import app
from owlin.api.deps import get_current_user, get_storage
from owlin.core.errors import ConflictError, InvalidRequestError, NotFoundError
from owlin.core.security import TokenUser
from owlin.integrations.supabase_storage import ObjectInfo, UploadTarget
from owlin.modules.orders import service
from owlin.modules.orders.models import Order, OrderScreenshot
from owlin.modules.orders.schemas import CreateOrderRequest, ScreenshotDeclaration

NOW = datetime(2026, 10, 29, 12, 0, tzinfo=UTC)
PNG = ScreenshotDeclaration(content_type="image/png", size_bytes=1000)


class FakeSession:
    """Just enough of AsyncSession for the orders service."""

    def __init__(self, open_orders: int = 0, order: Order | None = None, orders: list[Order] | None = None) -> None:
        self.open_orders = open_orders
        self.order = order
        self.orders = orders or []
        self.added: list[object] = []
        self.committed = False

    async def scalar(self, _statement: object) -> int:
        return self.open_orders

    async def scalars(self, _statement: object):
        return SimpleNamespace(all=lambda: self.orders)

    async def get(self, _model: type, _key: object, with_for_update: bool = False) -> Order | None:
        return self.order

    def add(self, item: object) -> None:
        self.added.append(item)

    async def flush(self) -> None:
        for item in self.added:
            if isinstance(item, Order) and item.created_at is None:
                item.created_at = NOW

    async def commit(self) -> None:
        self.committed = True

    async def refresh(self, _item: object) -> None:
        pass


class FakeStorage:
    def __init__(self, files: dict[str, ObjectInfo] | None = None) -> None:
        self.files = files or {}
        self.signed: list[str] = []

    async def create_upload_target(self, path: str) -> UploadTarget:
        self.signed.append(path)
        return UploadTarget(path=path, token=f"token-for-{path}")

    async def get_object_info(self, path: str) -> ObjectInfo | None:
        return self.files.get(path)


def make_request(**overrides: object) -> CreateOrderRequest:
    values = {"product": "spoofer", "period": "3m", "method": "paypal", "coin": None, "screenshots": [PNG]}
    return CreateOrderRequest(**{**values, **overrides})


def make_pending_order(user_id: UUID, **overrides: object) -> Order:
    values = dict(
        id=uuid4(), user_id=user_id, product="spoofer", period="3m", method="paypal", coin=None,
        amount_cents=900, status="pending", created_at=NOW,
    )  # fmt: skip
    return Order(**{**values, **overrides})


class TestPricing:
    def test_amount_comes_from_the_catalog(self) -> None:
        assert service.price_cents("spoofer", "3m") == 900
        assert service.price_cents("spoofer-dlc-unlock", "lifetime") == 3099

    @pytest.mark.parametrize("product, period", [("nope", "3m"), ("spoofer", "2y")])
    def test_unknown_plan_is_rejected(self, product: str, period: str) -> None:
        with pytest.raises(InvalidRequestError):
            service.price_cents(product, period)


class TestPaymentValidation:
    def test_crypto_needs_a_known_coin(self) -> None:
        service.validate_payment("crypto", "usdt-trc20")
        with pytest.raises(InvalidRequestError):
            service.validate_payment("crypto", None)
        with pytest.raises(InvalidRequestError):
            service.validate_payment("crypto", "doge")

    def test_other_methods_take_no_coin(self) -> None:
        service.validate_payment("paypal", None)
        with pytest.raises(InvalidRequestError):
            service.validate_payment("steam", "btc")

    def test_unknown_method_is_rejected(self) -> None:
        with pytest.raises(InvalidRequestError):
            service.validate_payment("cash", None)

    def test_screenshots_are_limited_by_type_and_size(self) -> None:
        service.validate_screenshot("image/webp", 25 * 1024 * 1024)
        with pytest.raises(InvalidRequestError):
            service.validate_screenshot("application/pdf", 10)
        with pytest.raises(InvalidRequestError):
            service.validate_screenshot("image/png", 25 * 1024 * 1024 + 1)


class TestCreateOrder:
    @pytest.mark.asyncio
    async def test_creates_a_pending_order_with_the_server_price_and_upload_slots(self) -> None:
        user_id = uuid4()
        session, storage = FakeSession(), FakeStorage()

        order, targets = await service.create_order(
            session, storage, user_id, make_request(screenshots=[PNG, PNG]), now=NOW
        )

        assert order.status == "pending"
        assert order.amount_cents == 900
        assert order.user_id == user_id
        assert session.committed is True
        assert len(targets) == 2
        assert all(target.path.startswith(f"{user_id}/{order.id}/") and target.path.endswith(".png") for target in targets)

    @pytest.mark.asyncio
    async def test_refuses_when_too_many_orders_are_waiting(self) -> None:
        session = FakeSession(open_orders=3)

        with pytest.raises(ConflictError):
            await service.create_order(session, FakeStorage(), uuid4(), make_request(), now=NOW)

        assert session.added == []

    @pytest.mark.asyncio
    async def test_invalid_requests_never_reach_the_database(self) -> None:
        session = FakeSession()

        with pytest.raises(InvalidRequestError):
            await service.create_order(session, FakeStorage(), uuid4(), make_request(product="nope"), now=NOW)

        assert session.added == []


class TestSubmitOrder:
    def uploaded(self, user_id: UUID, order: Order, count: int = 1):
        paths = [f"{user_id}/{order.id}/{uuid4()}.png" for _ in range(count)]
        files = {path: ObjectInfo(size_bytes=500, content_type="image/png") for path in paths}
        return paths, FakeStorage(files)

    @pytest.mark.asyncio
    async def test_moves_the_order_to_review_and_records_screenshots(self) -> None:
        user_id = uuid4()
        order = make_pending_order(user_id)
        paths, storage = self.uploaded(user_id, order, count=2)
        session = FakeSession(order=order)

        result = await service.submit_order(session, storage, user_id, order.id, paths, "  0xabc  ", "  ")

        assert result.status == "review"
        assert result.proof_text == "0xabc"
        assert result.note is None
        screenshots = [item for item in session.added if isinstance(item, OrderScreenshot)]
        assert {item.storage_path for item in screenshots} == set(paths)
        assert session.committed is True

    @pytest.mark.asyncio
    async def test_someone_elses_order_looks_like_it_does_not_exist(self) -> None:
        order = make_pending_order(uuid4())
        paths, storage = self.uploaded(order.user_id, order)

        with pytest.raises(NotFoundError):
            await service.submit_order(FakeSession(order=order), storage, uuid4(), order.id, paths, None, None)

    @pytest.mark.asyncio
    async def test_an_order_cannot_be_submitted_twice(self) -> None:
        user_id = uuid4()
        order = make_pending_order(user_id, status="review")
        paths, storage = self.uploaded(user_id, order)

        with pytest.raises(ConflictError):
            await service.submit_order(FakeSession(order=order), storage, user_id, order.id, paths, None, None)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("bad_path", ["../other/file.png", "someone/else/file.png", "{prefix}../x.png", "{prefix}a.png"])
    async def test_paths_outside_the_order_are_rejected(self, bad_path: str) -> None:
        user_id = uuid4()
        order = make_pending_order(user_id)
        path = bad_path.format(prefix=f"{user_id}/{order.id}/")

        with pytest.raises(InvalidRequestError):
            await service.submit_order(FakeSession(order=order), FakeStorage(), user_id, order.id, [path], None, None)

    @pytest.mark.asyncio
    async def test_a_file_that_was_never_uploaded_is_rejected(self) -> None:
        user_id = uuid4()
        order = make_pending_order(user_id)
        path = f"{user_id}/{order.id}/{uuid4()}.png"

        with pytest.raises(InvalidRequestError):
            await service.submit_order(FakeSession(order=order), FakeStorage(), user_id, order.id, [path], None, None)

    @pytest.mark.asyncio
    async def test_the_real_type_and_size_are_checked_not_the_declared_ones(self) -> None:
        user_id = uuid4()
        order = make_pending_order(user_id)
        path = f"{user_id}/{order.id}/{uuid4()}.png"
        storage = FakeStorage({path: ObjectInfo(size_bytes=500, content_type="text/html")})

        with pytest.raises(InvalidRequestError):
            await service.submit_order(FakeSession(order=order), storage, user_id, order.id, [path], None, None)

    @pytest.mark.asyncio
    async def test_the_same_file_cannot_be_listed_twice(self) -> None:
        user_id = uuid4()
        order = make_pending_order(user_id)
        paths, storage = self.uploaded(user_id, order)

        with pytest.raises(InvalidRequestError):
            await service.submit_order(FakeSession(order=order), storage, user_id, order.id, paths * 2, None, None)


USER = TokenUser(id=uuid4(), username="Pedro", avatar_url=None)


class TestEndpoints:
    @pytest.fixture(autouse=True)
    def sign_in(self) -> None:
        app.dependency_overrides[get_current_user] = lambda: USER
        app.dependency_overrides[get_storage] = lambda: FakeStorage()

    @pytest.mark.asyncio
    async def test_orders_require_a_token(self, client) -> None:
        app.dependency_overrides.pop(get_current_user)

        assert (await client.post("/api/orders", json={})).status_code == 401
        assert (await client.get("/api/me/orders")).status_code == 401

    @pytest.mark.asyncio
    async def test_create_returns_the_price_and_upload_slots(self, client, use_session) -> None:
        use_session(FakeSession())

        response = await client.post(
            "/api/orders",
            json={"product": "spoofer", "period": "1m", "method": "paypal", "screenshots": [{"content_type": "image/png", "size_bytes": 10}]},
        )

        assert response.status_code == 201
        body = response.json()
        assert body["amount_cents"] == 400
        assert len(body["uploads"]) == 1
        assert body["uploads"][0]["token"].startswith("token-for-")

    @pytest.mark.asyncio
    async def test_unknown_plan_is_a_422_with_a_message(self, client, use_session) -> None:
        use_session(FakeSession())

        response = await client.post(
            "/api/orders",
            json={"product": "nope", "period": "1m", "method": "paypal", "screenshots": [{"content_type": "image/png", "size_bytes": 10}]},
        )

        assert response.status_code == 422
        assert response.json() == {"detail": "Unknown plan"}

    @pytest.mark.asyncio
    async def test_at_least_one_and_at_most_three_screenshots(self, client, use_session) -> None:
        use_session(FakeSession())
        base = {"product": "spoofer", "period": "1m", "method": "paypal"}
        shot = {"content_type": "image/png", "size_bytes": 10}

        assert (await client.post("/api/orders", json={**base, "screenshots": []})).status_code == 422
        assert (await client.post("/api/orders", json={**base, "screenshots": [shot] * 4})).status_code == 422

    @pytest.mark.asyncio
    async def test_too_many_open_orders_is_a_409(self, client, use_session) -> None:
        use_session(FakeSession(open_orders=3))

        response = await client.post(
            "/api/orders",
            json={"product": "spoofer", "period": "1m", "method": "paypal", "screenshots": [{"content_type": "image/png", "size_bytes": 10}]},
        )

        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_my_orders_lists_the_orders(self, client, use_session) -> None:
        order = make_pending_order(USER.id, status="approved", received_cents=1000, balance_added_cents=100)
        use_session(FakeSession(orders=[order]))

        response = await client.get("/api/me/orders")

        assert response.status_code == 200
        [item] = response.json()
        assert item["status"] == "approved"
        assert item["balance_added_cents"] == 100
        assert "proof_text" not in item
