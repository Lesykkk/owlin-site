from datetime import datetime
from uuid import UUID

from sqlalchemy import ForeignKey, false, func
from sqlalchemy.orm import Mapped, mapped_column

from owlin.core.db import Base


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
