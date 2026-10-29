from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from owlin.modules.devices.models import UserDevice


async def get_last_seen(session: AsyncSession, user_id: UUID) -> datetime | None:
    """The last time the loader signed in from any of the user's computers."""
    return await session.scalar(select(func.max(UserDevice.last_seen_at)).where(UserDevice.user_id == user_id))
