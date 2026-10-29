from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from owlin.modules.balance.models import BalanceTransaction


async def get_balance(session: AsyncSession, user_id: UUID) -> int:
    """The user's balance in euro cents: the sum of all their balance transactions."""
    total = await session.scalar(
        select(func.coalesce(func.sum(BalanceTransaction.amount_cents), 0)).where(BalanceTransaction.user_id == user_id)
    )
    return int(total or 0)


def add_transaction(
    session: AsyncSession,
    *,
    user_id: UUID,
    amount_cents: int,
    reason: str,
    order_id: UUID | None = None,
    note: str | None = None,
) -> BalanceTransaction:
    """Queue a balance change. The caller commits it with the rest of its transaction."""
    transaction = BalanceTransaction(
        user_id=user_id, amount_cents=amount_cents, reason=reason, order_id=order_id, note=note
    )
    session.add(transaction)
    return transaction
