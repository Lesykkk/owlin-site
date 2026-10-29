from datetime import datetime, time
from uuid import UUID

from sqlalchemy import CheckConstraint, Index, SmallInteger, false, func, text, true
from sqlalchemy.orm import Mapped, mapped_column

from owlin.core.db import Base


class AccessPromotion(Base):
    """A global promotion that opens modules for everyone, for a date range or weekly."""

    __tablename__ = "access_promotions"
    __table_args__ = (
        CheckConstraint("promotion_type IN ('date_range', 'weekly')", name="access_promotions_promotion_type_check"),
        CheckConstraint("start_day IS NULL OR start_day BETWEEN 0 AND 6", name="access_promotions_start_day_check"),
        CheckConstraint("end_day IS NULL OR end_day BETWEEN 0 AND 6", name="access_promotions_end_day_check"),
        Index("access_promotions_active_idx", "is_active", postgresql_where=text("is_active = true")),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    name: Mapped[str]
    is_active: Mapped[bool] = mapped_column(server_default=true())
    spoofer_access: Mapped[bool] = mapped_column(server_default=false())
    dlc_access: Mapped[bool] = mapped_column(server_default=false())
    ets2_access: Mapped[bool] = mapped_column(server_default=false())
    ets2mp_access: Mapped[bool] = mapped_column(server_default=false())
    promotion_type: Mapped[str]
    timezone: Mapped[str] = mapped_column(server_default=text("'UTC'"))
    starts_at: Mapped[datetime | None]
    ends_at: Mapped[datetime | None]
    start_day: Mapped[int | None] = mapped_column(SmallInteger)
    end_day: Mapped[int | None] = mapped_column(SmallInteger)
    start_time: Mapped[time | None]
    end_time: Mapped[time | None]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())
