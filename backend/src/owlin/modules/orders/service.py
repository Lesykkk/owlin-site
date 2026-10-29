import logging
from dataclasses import dataclass
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from owlin.core.errors import ConflictError, InvalidRequestError
from owlin.integrations.supabase_storage import StorageClient
from owlin.modules.catalog.constants import (
    CRYPTO_COIN_IDS,
    MAX_OPEN_ORDERS,
    MAX_SCREENSHOT_BYTES,
    MAX_SCREENSHOTS_PER_ORDER,
    PAYMENT_METHOD_IDS,
    PRICES_CENTS,
)
from owlin.modules.orders.images import detect_image
from owlin.modules.orders.models import Order, OrderScreenshot

logger = logging.getLogger(__name__)

LIST_LIMIT = 50


@dataclass(frozen=True)
class NewOrder:
    product: str
    period: str
    method: str
    coin: str | None
    proof_text: str | None
    note: str | None


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


def validate_screenshots(files: list[bytes]) -> list[tuple[str, str]]:
    """Check the uploaded files and return each one's (content type, extension), judged by its content."""
    if not 1 <= len(files) <= MAX_SCREENSHOTS_PER_ORDER:
        raise InvalidRequestError(f"Attach from 1 to {MAX_SCREENSHOTS_PER_ORDER} screenshots")

    kinds = []
    for content in files:
        if len(content) > MAX_SCREENSHOT_BYTES:
            raise InvalidRequestError(f"Each screenshot must be at most {MAX_SCREENSHOT_BYTES // (1024 * 1024)} MB")
        kind = detect_image(content)
        if kind is None:
            raise InvalidRequestError("Screenshots must be PNG, JPG or WebP images")
        kinds.append(kind)
    return kinds


def clean_text(value: str | None) -> str | None:
    value = (value or "").strip()
    return value or None


async def count_open_orders(session: AsyncSession, user_id: UUID) -> int:
    count = await session.scalar(
        select(func.count()).select_from(Order).where(Order.user_id == user_id, Order.status == "review")
    )
    return count or 0


async def discard_files(storage: StorageClient, paths: list[str]) -> None:
    """Remove files of an order that could not be completed. Failures are logged, not raised."""
    for path in paths:
        try:
            await storage.delete_object(path)
        except Exception:
            logger.exception("Could not remove an orphaned file: %s", path)


async def create_order(
    session: AsyncSession, storage: StorageClient, user_id: UUID, data: NewOrder, files: list[bytes]
) -> Order:
    """Place an order in one go. Either it exists afterwards, under review with all its files stored,
    or nothing was created: no row and no files.

    Everything that can be checked cheaply is checked first, then the open-order limit, and only
    then are files uploaded, so a refused request never writes to storage.
    """
    amount_cents = price_cents(data.product, data.period)
    validate_payment(data.method, data.coin)
    kinds = validate_screenshots(files)

    if await count_open_orders(session, user_id) >= MAX_OPEN_ORDERS:
        raise ConflictError(
            f"You already have {MAX_OPEN_ORDERS} orders waiting for review. Wait for them to be checked first."
        )

    order = Order(
        id=uuid4(),
        user_id=user_id,
        product=data.product,
        period=data.period,
        method=data.method,
        coin=data.coin,
        amount_cents=amount_cents,
        status="review",
        proof_text=clean_text(data.proof_text),
        note=clean_text(data.note),
    )

    uploaded: list[str] = []
    try:
        for content, (content_type, extension) in zip(files, kinds, strict=True):
            path = f"{user_id}/{order.id}/{uuid4()}.{extension}"
            await storage.upload_object(path, content, content_type)
            uploaded.append(path)
            session.add(
                OrderScreenshot(order_id=order.id, storage_path=path, content_type=content_type, size_bytes=len(content))
            )
        session.add(order)
        await session.commit()
    except BaseException:
        # Whatever went wrong, do not leave files behind for an order that does not exist.
        await discard_files(storage, uploaded)
        raise

    await session.refresh(order)
    return order


async def list_orders(session: AsyncSession, user_id: UUID) -> list[Order]:
    """A user's orders, newest first."""
    result = await session.scalars(
        select(Order).where(Order.user_id == user_id).order_by(Order.created_at.desc()).limit(LIST_LIMIT)
    )
    return list(result.all())
