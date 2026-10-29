import re
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from owlin.core.errors import ConflictError, InvalidRequestError, NotFoundError
from owlin.integrations.supabase_storage import StorageClient, UploadTarget
from owlin.modules.catalog.constants import (
    CRYPTO_COIN_IDS,
    MAX_OPEN_ORDERS,
    MAX_SCREENSHOT_BYTES,
    MAX_SCREENSHOTS_PER_ORDER,
    PAYMENT_METHOD_IDS,
    PRICES_CENTS,
    SCREENSHOT_CONTENT_TYPES,
)
from owlin.modules.orders.models import Order, OrderScreenshot
from owlin.modules.orders.schemas import CreateOrderRequest

FILE_EXTENSIONS = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}
# An order that was created but never submitted stops counting as open after this long.
PENDING_ORDER_TTL = timedelta(hours=1)
LIST_LIMIT = 50


def price_cents(product_id: str, period_id: str) -> int:
    try:
        return PRICES_CENTS[product_id][period_id]
    except KeyError:
        raise InvalidRequestError("Unknown plan") from None


def validate_payment(method: str, coin: str | None) -> None:
    if method not in PAYMENT_METHOD_IDS:
        raise InvalidRequestError("Unknown payment method")
    if method == "crypto":
        if coin not in CRYPTO_COIN_IDS:
            raise InvalidRequestError("Choose a coin for the crypto payment")
    elif coin is not None:
        raise InvalidRequestError("A coin only applies to crypto payments")


def validate_screenshot(content_type: str, size_bytes: int) -> None:
    if content_type not in SCREENSHOT_CONTENT_TYPES:
        raise InvalidRequestError("Screenshots must be PNG, JPG or WebP images")
    if size_bytes > MAX_SCREENSHOT_BYTES:
        raise InvalidRequestError(f"Each screenshot must be at most {MAX_SCREENSHOT_BYTES // (1024 * 1024)} MB")


def clean_text(value: str | None) -> str | None:
    value = (value or "").strip()
    return value or None


async def count_open_orders(session: AsyncSession, user_id: UUID, now: datetime) -> int:
    open_orders = or_(
        Order.status == "review",
        (Order.status == "pending") & (Order.created_at > now - PENDING_ORDER_TTL),
    )
    count = await session.scalar(select(func.count()).select_from(Order).where(Order.user_id == user_id, open_orders))
    return count or 0


async def create_order(
    session: AsyncSession,
    storage: StorageClient,
    user_id: UUID,
    request: CreateOrderRequest,
    now: datetime | None = None,
) -> tuple[Order, list[UploadTarget]]:
    """Start an order: store it as pending and hand out one upload slot per screenshot."""
    now = now or datetime.now(UTC)

    amount_cents = price_cents(request.product, request.period)
    validate_payment(request.method, request.coin)
    for screenshot in request.screenshots:
        validate_screenshot(screenshot.content_type, screenshot.size_bytes)

    if await count_open_orders(session, user_id, now) >= MAX_OPEN_ORDERS:
        raise ConflictError("You already have orders waiting for review. Wait for them to be checked first.")

    order = Order(
        id=uuid4(),
        user_id=user_id,
        product=request.product,
        period=request.period,
        method=request.method,
        coin=request.coin,
        amount_cents=amount_cents,
        status="pending",
    )
    session.add(order)
    await session.flush()

    targets = [
        await storage.create_upload_target(
            f"{user_id}/{order.id}/{uuid4()}.{FILE_EXTENSIONS[screenshot.content_type]}"
        )
        for screenshot in request.screenshots
    ]

    await session.commit()
    await session.refresh(order)
    return order, targets


def expected_path_pattern(user_id: UUID, order_id: UUID) -> re.Pattern[str]:
    return re.compile(rf"{user_id}/{order_id}/[0-9a-f-]{{36}}\.(png|jpg|webp)")


async def submit_order(
    session: AsyncSession,
    storage: StorageClient,
    user_id: UUID,
    order_id: UUID,
    paths: list[str],
    proof_text: str | None,
    note: str | None,
) -> Order:
    """Finish an order after its files are uploaded: verify them and send the order to review."""
    # Locked so that two submits of the same order cannot both go through.
    order = await session.get(Order, order_id, with_for_update=True)
    if order is None or order.user_id != user_id:
        raise NotFoundError("Order not found")
    if order.status != "pending":
        raise ConflictError("This order was already submitted")

    pattern = expected_path_pattern(user_id, order_id)
    if len(set(paths)) != len(paths) or len(paths) > MAX_SCREENSHOTS_PER_ORDER:
        raise InvalidRequestError("Invalid list of files")
    if not all(pattern.fullmatch(path) for path in paths):
        raise InvalidRequestError("Invalid file path")

    for path in paths:
        info = await storage.get_object_info(path)
        if info is None:
            raise InvalidRequestError("A file was not uploaded. Try again.")
        validate_screenshot(info.content_type, info.size_bytes)
        session.add(
            OrderScreenshot(
                order_id=order.id,
                storage_path=path,
                content_type=info.content_type,
                size_bytes=info.size_bytes,
            )
        )

    order.status = "review"
    order.proof_text = clean_text(proof_text)
    order.note = clean_text(note)

    await session.commit()
    await session.refresh(order)
    return order


async def list_orders(session: AsyncSession, user_id: UUID) -> list[Order]:
    """A user's orders, newest first. Orders that were never submitted are left out."""
    result = await session.scalars(
        select(Order)
        .where(Order.user_id == user_id, Order.status != "pending")
        .order_by(Order.created_at.desc())
        .limit(LIST_LIMIT)
    )
    return list(result.all())
