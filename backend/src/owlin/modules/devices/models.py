from datetime import datetime
from uuid import UUID

from sqlalchemy import ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from owlin.core.db import Base


class UserDevice(Base):
    """Hardware fingerprints of the computers a user has signed in from. Written by the loader."""

    __tablename__ = "user_devices"
    __table_args__ = (
        Index("idx_user_devices_user_id", "user_id"),
        Index("idx_user_devices_user_smbios", "user_id", "smbios_uuid"),
        Index("idx_user_devices_user_motherboard", "user_id", "motherboard_serial"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    user_id: Mapped[UUID] = mapped_column(ForeignKey("auth.users.id", ondelete="CASCADE", onupdate="CASCADE"))
    smbios_uuid: Mapped[str | None]
    motherboard_serial: Mapped[str | None]
    cpu_id: Mapped[str | None]
    disk_serial: Mapped[str | None]
    machine_guid: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(server_default=func.now())
