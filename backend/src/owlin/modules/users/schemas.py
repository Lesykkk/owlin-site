from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from owlin.modules.subscriptions.schemas import SubscriptionInfo


class UserInfo(BaseModel):
    """A user as shown to an admin."""

    id: UUID
    username: str
    avatar_url: str | None
    discord_id: str | None


class PromoSlots(BaseModel):
    used: int
    max: int


class MeResponse(BaseModel):
    id: UUID
    username: str
    avatar_url: str | None
    discord_id: str | None
    created_at: datetime
    is_admin: bool
    # Keyed by module id: "spoofer", "dlc-unlock".
    subscriptions: dict[str, SubscriptionInfo]
    balance_cents: int
    # The last time the loader signed in from any of the user's computers.
    last_seen_at: datetime | None
