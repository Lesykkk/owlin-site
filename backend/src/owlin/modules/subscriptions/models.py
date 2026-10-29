from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, false, func
from sqlalchemy.orm import Mapped, mapped_column

from owlin.core.db import Base, in_list
from owlin.modules.catalog.constants import GRANT_SOURCES, MODULE_IDS


class UserSubscription(Base):
    """Current access of a user to each module. The loader reads this table.

    `<module>_access` with an empty `<module>_expires_at` means access without an end date.
    Created automatically for every new auth user by a database trigger.
    """

    __tablename__ = "user_subscriptions"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("auth.users.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())

    spoofer_access: Mapped[bool] = mapped_column(server_default=false())
    spoofer_expires_at: Mapped[datetime | None]
    dlc_access: Mapped[bool] = mapped_column(server_default=false())
    dlc_expires_at: Mapped[datetime | None]
    ets2_access: Mapped[bool] = mapped_column(server_default=false())
    ets2_expires_at: Mapped[datetime | None]
    ets2mp_access: Mapped[bool] = mapped_column(server_default=false())
    ets2mp_expires_at: Mapped[datetime | None]


class SubscriptionGrant(Base):
    """History of access given to a user: from an order, a promo video or by an admin.

    user_subscriptions only holds the current state, so this table is the record of how it got there.
    Empty `days` / `ends_at` mean the grant has no end date.
    """

    __tablename__ = "subscription_grants"
    __table_args__ = (
        CheckConstraint(in_list("product", MODULE_IDS), name="product"),
        CheckConstraint(in_list("source", GRANT_SOURCES), name="source"),
        CheckConstraint("days IS NULL OR days > 0", name="days_positive"),
        CheckConstraint(
            "(source = 'order' AND order_id IS NOT NULL)"
            " OR (source = 'promo' AND promo_claim_id IS NOT NULL)"
            " OR source = 'admin'",
            name="source_reference",
        ),
        Index("ix_subscription_grants_user_created", "user_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    user_id: Mapped[UUID] = mapped_column(ForeignKey("auth.users.id", ondelete="CASCADE"))
    product: Mapped[str]
    source: Mapped[str]
    order_id: Mapped[UUID | None] = mapped_column(ForeignKey("orders.id", ondelete="SET NULL"))
    promo_claim_id: Mapped[UUID | None] = mapped_column(ForeignKey("promo_claims.id", ondelete="SET NULL"))
    granted_by: Mapped[UUID | None] = mapped_column(ForeignKey("auth.users.id", ondelete="SET NULL"))
    days: Mapped[int | None]
    starts_at: Mapped[datetime]
    ends_at: Mapped[datetime | None]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
