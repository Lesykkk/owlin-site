from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from owlin.core.db import Base, in_list
from owlin.modules.catalog.constants import (
    MAX_SCREENSHOT_BYTES,
    ORDER_STATUSES,
    SCREENSHOT_CONTENT_TYPES,
)


class Order(Base):
    """A manual payment: the user pays outside the site, uploads proof, an admin reviews it.

    Statuses: pending (created, screenshots still uploading) -> review -> approved / rejected.
    All money is in euro cents.
    """

    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint(in_list("status", ORDER_STATUSES), name="status"),
        CheckConstraint("amount_cents > 0", name="amount_positive"),
        CheckConstraint("received_cents IS NULL OR received_cents > 0", name="received_positive"),
        CheckConstraint("balance_added_cents IS NULL OR balance_added_cents >= 0", name="balance_added_not_negative"),
        Index("ix_orders_user_created", "user_id", "created_at"),
        Index("ix_orders_status_created", "status", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    user_id: Mapped[UUID] = mapped_column(ForeignKey("auth.users.id", ondelete="CASCADE"))

    # Catalog ids (see modules/catalog); validated in code, not by the database.
    product: Mapped[str]
    period: Mapped[str]
    method: Mapped[str]
    # Crypto only: which coin and network was used, e.g. "usdt-trc20".
    coin: Mapped[str | None]
    # What the user had to pay, calculated by the server.
    amount_cents: Mapped[int]

    status: Mapped[str] = mapped_column(server_default="pending")
    # Transaction hash, PayPal name or Steam name, whatever the method asks for (optional).
    proof_text: Mapped[str | None]
    note: Mapped[str | None]

    # Filled in on review: what the admin saw arrive, and the surplus that went to the balance.
    received_cents: Mapped[int | None]
    balance_added_cents: Mapped[int | None]
    reject_reason: Mapped[str | None]
    reviewed_by: Mapped[UUID | None] = mapped_column(ForeignKey("auth.users.id", ondelete="SET NULL"))
    reviewed_at: Mapped[datetime | None]

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())


class OrderScreenshot(Base):
    """A proof-of-payment image stored in the private Supabase Storage bucket."""

    __tablename__ = "order_screenshots"
    __table_args__ = (
        CheckConstraint(in_list("content_type", SCREENSHOT_CONTENT_TYPES), name="content_type"),
        CheckConstraint(f"size_bytes > 0 AND size_bytes <= {MAX_SCREENSHOT_BYTES}", name="size"),
        Index("ix_order_screenshots_order_id", "order_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    order_id: Mapped[UUID] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    storage_path: Mapped[str] = mapped_column(unique=True)
    content_type: Mapped[str]
    size_bytes: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
