"""Admin side of orders: the review queue, approving and rejecting."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from owlin.core.errors import ConflictError, InvalidRequestError, NotFoundError
from owlin.integrations.supabase_storage import StorageClient
from owlin.modules.balance import service as balance
from owlin.modules.catalog.constants import PERIOD_DAYS
from owlin.modules.orders.models import Order, OrderScreenshot
from owlin.modules.orders.schemas import AdminOrderResponse, AdminScreenshot, OrderResponse
from owlin.modules.subscriptions import service as subscriptions
from owlin.modules.users import service as users
from owlin.modules.users.schemas import UserInfo

ADMIN_LIST_LIMIT = 100


async def approve_order(
    session: AsyncSession, order_id: UUID, admin_id: UUID, received_cents: int, now: datetime | None = None
) -> Order:
    """Accept a payment: give the user their plan and put any surplus on their balance.

    Everything happens in one transaction under a lock on the order, so a double click or a
    second admin cannot grant twice.
    """
    now = now or datetime.now(UTC)

    order = await session.get(Order, order_id, with_for_update=True)
    if order is None:
        raise NotFoundError("Order not found")
    if order.status != "review":
        raise ConflictError("Only orders under review can be approved")
    if received_cents < order.amount_cents:
        raise InvalidRequestError("The received amount is less than the order amount")
    if order.period not in PERIOD_DAYS:
        raise InvalidRequestError("The order has an unknown period")

    await subscriptions.grant_product(
        session,
        user_id=order.user_id,
        product_id=order.product,
        days=PERIOD_DAYS[order.period],
        source="order",
        order_id=order.id,
        granted_by=admin_id,
        now=now,
    )

    surplus_cents = received_cents - order.amount_cents
    if surplus_cents > 0:
        balance.add_transaction(
            session, user_id=order.user_id, amount_cents=surplus_cents, reason="order_overpay", order_id=order.id
        )

    order.status = "approved"
    order.received_cents = received_cents
    order.balance_added_cents = surplus_cents
    order.reject_reason = None
    order.reviewed_by = admin_id
    order.reviewed_at = now

    await session.commit()
    await session.refresh(order)
    return order


async def reject_order(
    session: AsyncSession, order_id: UUID, admin_id: UUID, reason: str, now: datetime | None = None
) -> Order:
    now = now or datetime.now(UTC)

    order = await session.get(Order, order_id, with_for_update=True)
    if order is None:
        raise NotFoundError("Order not found")
    if order.status != "review":
        raise ConflictError("Only orders under review can be rejected")

    order.status = "rejected"
    order.reject_reason = reason.strip()
    order.reviewed_by = admin_id
    order.reviewed_at = now

    await session.commit()
    await session.refresh(order)
    return order


async def list_orders_for_admin(
    session: AsyncSession, storage: StorageClient, status: str | None
) -> list[AdminOrderResponse]:
    """The review queue (oldest first) or a history list (newest first). Unsubmitted orders are left out."""
    statement = select(Order).where(Order.status != "pending")
    if status is not None:
        statement = statement.where(Order.status == status)
    ordering = Order.created_at.asc() if status == "review" else Order.created_at.desc()

    result = await session.scalars(statement.order_by(ordering).limit(ADMIN_LIST_LIMIT))
    return await describe_for_admin(session, storage, list(result.all()))


async def describe_for_admin(
    session: AsyncSession, storage: StorageClient, orders: list[Order]
) -> list[AdminOrderResponse]:
    """Attach the paying user and temporary screenshot links to each order."""
    if not orders:
        return []

    result = await session.scalars(
        select(OrderScreenshot)
        .where(OrderScreenshot.order_id.in_([order.id for order in orders]))
        .order_by(OrderScreenshot.created_at)
    )
    screenshots_by_order: dict[UUID, list[OrderScreenshot]] = {}
    for screenshot in result.all():
        screenshots_by_order.setdefault(screenshot.order_id, []).append(screenshot)

    urls = await storage.create_download_urls(
        [shot.storage_path for shots in screenshots_by_order.values() for shot in shots]
    )
    profiles = await users.get_profiles(session, [order.user_id for order in orders])

    described = []
    for order in orders:
        profile = profiles.get(order.user_id)
        user = UserInfo(
            id=order.user_id,
            username=profile.username if profile else "Unknown",
            avatar_url=profile.avatar_url if profile else None,
            discord_id=profile.discord_id if profile else None,
        )
        described.append(
            AdminOrderResponse(
                **OrderResponse.model_validate(order).model_dump(),
                proof_text=order.proof_text,
                note=order.note,
                reviewed_at=order.reviewed_at,
                user=user,
                screenshots=[
                    AdminScreenshot(url=urls.get(shot.storage_path), content_type=shot.content_type)
                    for shot in screenshots_by_order.get(order.id, [])
                ],
            )
        )
    return described
