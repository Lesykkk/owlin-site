from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from owlin.core.db import Base, in_list
from owlin.modules.catalog.constants import BALANCE_REASONS


class BalanceTransaction(Base):
    """One change of a user's balance, in euro cents. The balance is the sum of a user's rows."""

    __tablename__ = "balance_transactions"
    __table_args__ = (
        CheckConstraint("amount_cents <> 0", name="amount_not_zero"),
        CheckConstraint(in_list("reason", BALANCE_REASONS), name="reason"),
        Index("ix_balance_transactions_user_created", "user_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    user_id: Mapped[UUID] = mapped_column(ForeignKey("auth.users.id", ondelete="CASCADE"))
    # Positive adds to the balance, negative spends it.
    amount_cents: Mapped[int]
    reason: Mapped[str]
    order_id: Mapped[UUID | None] = mapped_column(ForeignKey("orders.id", ondelete="SET NULL"))
    note: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
