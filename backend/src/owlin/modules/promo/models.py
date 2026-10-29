from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, func, text
from sqlalchemy.orm import Mapped, mapped_column

from owlin.core.db import Base, in_list
from owlin.modules.catalog.constants import MODULE_IDS, PROMO_CLAIM_STATUSES


class PromoClaim(Base):
    """A video submitted for free days. An admin checks it by hand.

    `video_key` is the normalized link, e.g. "youtube:dKiSnET6eNs". Only one claim per video may
    be open or approved, but a rejected video can be submitted again.
    A claim occupies one of the user's slots while it is under review or approved and not expired.
    """

    __tablename__ = "promo_claims"
    __table_args__ = (
        CheckConstraint(in_list("reward_product", MODULE_IDS), name="reward_product"),
        CheckConstraint(in_list("status", PROMO_CLAIM_STATUSES), name="status"),
        CheckConstraint("views IS NULL OR views >= 0", name="views_not_negative"),
        Index("uq_promo_claims_video_key_open", "video_key", unique=True, postgresql_where=text("status <> 'rejected'")),
        Index("ix_promo_claims_user_status", "user_id", "status"),
        Index("ix_promo_claims_status_created", "status", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    user_id: Mapped[UUID] = mapped_column(ForeignKey("auth.users.id", ondelete="CASCADE"))

    # Catalog id (tiktok, youtube, other); validated in code, not by the database.
    platform: Mapped[str]
    video_key: Mapped[str]
    url: Mapped[str]
    reward_product: Mapped[str]

    status: Mapped[str] = mapped_column(server_default="review")
    # The view count the admin saw when approving (optional for "other" platforms).
    views: Mapped[int | None]
    reject_reason: Mapped[str | None]
    reviewed_by: Mapped[UUID | None] = mapped_column(ForeignKey("auth.users.id", ondelete="SET NULL"))
    reviewed_at: Mapped[datetime | None]
    # When the granted free days run out; set on approval.
    expires_at: Mapped[datetime | None]

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
