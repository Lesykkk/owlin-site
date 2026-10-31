from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from owlin.api.app import app
from owlin.api.deps import get_current_user, get_storage
from owlin.core.errors import ConflictError, InvalidRequestError, UpstreamError
from owlin.core.security import TokenUser
from owlin.modules.catalog.constants import MAX_OPEN_ORDERS, MAX_SCREENSHOT_BYTES
from owlin.modules.orders import service
from owlin.modules.orders.models import Order, OrderScreenshot
from owlin.modules.orders.service import NewOrder

NOW = datetime(2026, 10, 29, 12, 0, tzinfo=UTC)

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 100
WEBP = b"RIFF" + b"\x10\x00\x00\x00" + b"WEBP" + b"VP8 " + b"\x00" * 50


class FakeSession:
    """Just enough of AsyncSession for the orders service."""

    def __init__(self, open_orders: int = 0, orders: list[Order] | None = None) -> None:
        self.open_orders = open_orders
        self.orders = orders or []
        self.added: list[object] = []
        self.committed = False
        self.commit_error: Exception | None = None

    async def scalar(self, _statement: object) -> int:
        return self.open_orders

    async def scalars(self, _statement: object):
        return SimpleNamespace(all=lambda: self.orders)

    def add(self, item: object) -> None:
        self.added.append(item)

    async def commit(self) -> None:
        if self.commit_error:
            raise self.commit_error
        self.committed = True

    async def refresh(self, item: object) -> None:
        if getattr(item, "created_at", None) is None:
            item.created_at = NOW


class FakeStorage:
    def __init__(self, fail_on_upload: int | None = None) -> None:
        self.uploaded: list[tuple[str, bytes, str]] = []
        self.deleted: list[str] = []
        self.fail_on_upload = fail_on_upload

    async def upload_object(self, path: str, data: bytes, content_type: str) -> None:
        if self.fail_on_upload == len(self.uploaded) + 1:
            raise UpstreamError("File storage refused the upload")
        self.uploaded.append((path, data, content_type))

    async def delete_object(self, path: str) -> None:
        self.deleted.append(path)


def new_order(**overrides: object) -> NewOrder:
    values = dict(product="spoofer", period="3m", method="paypal", coin=None, proof_text=None, note=None)
    return NewOrder(**{**values, **overrides})


class TestPricing:
    def test_amount_comes_from_the_catalog(self) -> None:
        assert service.price_cents("spoofer", "3m") == 899
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


class TestScreenshotValidation:
    def test_the_type_comes_from_the_content(self) -> None:
        assert service.validate_screenshots([PNG, JPEG, WEBP]) == [
            ("image/png", "png"),
            ("image/jpeg", "jpg"),
            ("image/webp", "webp"),
        ]

    def test_one_to_three_files_are_required(self) -> None:
        with pytest.raises(InvalidRequestError):
            service.validate_screenshots([])
        with pytest.raises(InvalidRequestError):
            service.validate_screenshots([PNG] * 4)

    def test_a_file_over_the_size_limit_is_rejected(self) -> None:
        service.validate_screenshots([PNG + b"\x00" * (MAX_SCREENSHOT_BYTES - len(PNG))])
        with pytest.raises(InvalidRequestError, match="5 MB"):
            service.validate_screenshots([PNG + b"\x00" * (MAX_SCREENSHOT_BYTES - len(PNG) + 1)])

    @pytest.mark.parametrize("content", [b"", b"<html></html>", b"GIF89a" + b"\x00" * 20, b"%PDF-1.7"])
    def test_something_that_is_not_an_image_is_rejected(self, content: bytes) -> None:
        with pytest.raises(InvalidRequestError, match="PNG, JPG or WebP"):
            service.validate_screenshots([content])


class TestCreateOrder:
    @pytest.mark.asyncio
    async def test_creates_an_order_under_review_with_the_server_price_and_stored_files(self) -> None:
        user_id = uuid4()
        session, storage = FakeSession(), FakeStorage()

        order = await service.create_order(session, storage, user_id, new_order(), [PNG, JPEG])

        assert (order.status, order.amount_cents, order.user_id) == ("review", 899, user_id)
        assert session.committed is True
        assert [(content_type, data) for _path, data, content_type in storage.uploaded] == [
            ("image/png", PNG),
            ("image/jpeg", JPEG),
        ]
        paths = [path for path, _data, _type in storage.uploaded]
        assert all(path.startswith(f"{user_id}/{order.id}/") for path in paths)
        assert paths[0].endswith(".png") and paths[1].endswith(".jpg")

    @pytest.mark.asyncio
    async def test_screenshots_are_recorded_with_their_real_size_and_type(self) -> None:
        session, storage = FakeSession(), FakeStorage()

        order = await service.create_order(session, storage, uuid4(), new_order(), [WEBP])

        [shot] = [item for item in session.added if isinstance(item, OrderScreenshot)]
        assert (shot.order_id, shot.content_type, shot.size_bytes) == (order.id, "image/webp", len(WEBP))
        assert shot.storage_path == storage.uploaded[0][0]

    @pytest.mark.asyncio
    async def test_text_is_trimmed_and_empty_text_is_dropped(self) -> None:
        order = await service.create_order(
            FakeSession(), FakeStorage(), uuid4(), new_order(proof_text="  0xabc  ", note="   "), [PNG]
        )

        assert order.proof_text == "0xabc"
        assert order.note is None

    @pytest.mark.asyncio
    async def test_a_full_review_queue_refuses_the_order_before_anything_is_stored(self) -> None:
        session, storage = FakeSession(open_orders=MAX_OPEN_ORDERS), FakeStorage()

        with pytest.raises(ConflictError, match=str(MAX_OPEN_ORDERS)):
            await service.create_order(session, storage, uuid4(), new_order(), [PNG])

        assert storage.uploaded == []
        assert session.added == []
        assert session.committed is False

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "order, files",
        [
            (new_order(product="nope"), [PNG]),
            (new_order(method="crypto"), [PNG]),
            (new_order(), []),
            (new_order(), [PNG] * 4),
            (new_order(), [b"not an image"]),
        ],
    )
    async def test_invalid_requests_store_nothing(self, order: NewOrder, files: list[bytes]) -> None:
        session, storage = FakeSession(), FakeStorage()

        with pytest.raises(InvalidRequestError):
            await service.create_order(session, storage, uuid4(), order, files)

        assert storage.uploaded == []
        assert session.added == []

    @pytest.mark.asyncio
    async def test_a_failed_upload_removes_the_files_already_stored_and_saves_no_order(self) -> None:
        session, storage = FakeSession(), FakeStorage(fail_on_upload=2)

        with pytest.raises(UpstreamError):
            await service.create_order(session, storage, uuid4(), new_order(), [PNG, JPEG, WEBP])

        assert storage.deleted == [storage.uploaded[0][0]]
        assert session.committed is False

    @pytest.mark.asyncio
    async def test_a_failed_save_removes_every_stored_file(self) -> None:
        session, storage = FakeSession(), FakeStorage()
        session.commit_error = RuntimeError("database down")

        with pytest.raises(RuntimeError):
            await service.create_order(session, storage, uuid4(), new_order(), [PNG, JPEG])

        assert sorted(storage.deleted) == sorted(path for path, _data, _type in storage.uploaded)
        assert len(storage.deleted) == 2


USER = TokenUser(id=uuid4(), username="Pedro", avatar_url=None)


class TestEndpoints:
    FORM = {"product": "spoofer", "period": "1m", "method": "paypal"}

    @pytest.fixture(autouse=True)
    def sign_in(self) -> None:
        app.dependency_overrides[get_current_user] = lambda: USER
        self.storage = FakeStorage()
        app.dependency_overrides[get_storage] = lambda: self.storage

    @pytest.mark.asyncio
    async def test_orders_require_a_token(self, client) -> None:
        app.dependency_overrides.pop(get_current_user)

        assert (await client.post("/api/orders", data=self.FORM, files=[("screenshots", ("a.png", PNG))])).status_code == 401
        assert (await client.get("/api/me/orders")).status_code == 401

    @pytest.mark.asyncio
    async def test_an_order_is_created_in_one_request(self, client, use_session) -> None:
        use_session(FakeSession())

        response = await client.post(
            "/api/orders",
            data={**self.FORM, "proof_text": "anna.k", "note": "hello"},
            files=[("screenshots", ("pay.png", PNG, "image/png")), ("screenshots", ("pay2.jpg", JPEG, "image/jpeg"))],
        )

        assert response.status_code == 201
        body = response.json()
        assert (body["status"], body["amount_cents"], body["product"]) == ("review", 399, "spoofer")
        assert len(self.storage.uploaded) == 2
        assert "proof_text" not in body

    @pytest.mark.asyncio
    async def test_a_filename_or_declared_type_does_not_decide_what_a_file_is(self, client, use_session) -> None:
        use_session(FakeSession())

        response = await client.post(
            "/api/orders", data=self.FORM, files=[("screenshots", ("evil.png", b"<html>hi</html>", "image/png"))]
        )

        assert response.status_code == 422
        assert "PNG, JPG or WebP" in response.json()["detail"]
        assert self.storage.uploaded == []

    @pytest.mark.asyncio
    async def test_an_empty_coin_field_counts_as_no_coin(self, client, use_session) -> None:
        use_session(FakeSession())

        response = await client.post(
            "/api/orders", data={**self.FORM, "coin": ""}, files=[("screenshots", ("a.png", PNG, "image/png"))]
        )

        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_unknown_plan_is_a_422_with_a_message(self, client, use_session) -> None:
        use_session(FakeSession())

        response = await client.post(
            "/api/orders", data={**self.FORM, "product": "nope"}, files=[("screenshots", ("a.png", PNG, "image/png"))]
        )

        assert response.status_code == 422
        assert response.json() == {"detail": "Unknown plan"}

    @pytest.mark.asyncio
    async def test_the_screenshots_are_required_and_at_most_three(self, client, use_session) -> None:
        use_session(FakeSession())
        shot = ("screenshots", ("a.png", PNG, "image/png"))

        assert (await client.post("/api/orders", data=self.FORM)).status_code == 422
        assert (await client.post("/api/orders", data=self.FORM, files=[shot] * 4)).status_code == 422
        assert self.storage.uploaded == []

    @pytest.mark.asyncio
    async def test_a_screenshot_over_the_limit_is_refused(self, client, use_session) -> None:
        use_session(FakeSession())
        too_big = PNG + b"\x00" * MAX_SCREENSHOT_BYTES

        response = await client.post("/api/orders", data=self.FORM, files=[("screenshots", ("big.png", too_big, "image/png"))])

        assert response.status_code == 422
        assert "5 MB" in response.json()["detail"]
        assert self.storage.uploaded == []

    @pytest.mark.asyncio
    async def test_a_huge_request_is_refused_before_it_is_read(self, client, use_session) -> None:
        use_session(FakeSession())

        response = await client.post(
            "/api/orders", data=self.FORM, files=[("screenshots", ("huge.png", b"\x89PNG" + b"0" * 17_000_000, "image/png"))]
        )

        assert response.status_code == 413

    @pytest.mark.asyncio
    async def test_a_full_queue_is_a_409_and_nothing_is_uploaded(self, client, use_session) -> None:
        use_session(FakeSession(open_orders=MAX_OPEN_ORDERS))

        response = await client.post("/api/orders", data=self.FORM, files=[("screenshots", ("a.png", PNG, "image/png"))])

        assert response.status_code == 409
        assert self.storage.uploaded == []

    @pytest.mark.asyncio
    async def test_my_orders_lists_the_orders(self, client, use_session) -> None:
        order = Order(
            id=uuid4(), user_id=USER.id, product="spoofer", period="3m", method="paypal", coin=None,
            amount_cents=900, status="approved", created_at=NOW, received_cents=1000, balance_added_cents=100,
        )  # fmt: skip
        use_session(FakeSession(orders=[order]))

        response = await client.get("/api/me/orders")

        assert response.status_code == 200
        [item] = response.json()
        assert (item["status"], item["balance_added_cents"]) == ("approved", 100)
        assert "proof_text" not in item
