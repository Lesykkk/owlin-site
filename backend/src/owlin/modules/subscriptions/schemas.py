from datetime import datetime

from pydantic import BaseModel


class SubscriptionInfo(BaseModel):
    active: bool
    # When the current stretch of access began, from the grant history. Empty if unknown.
    started_at: datetime | None = None
    # When access ends. Empty while active means it never ends.
    expires_at: datetime | None
    lifetime: bool
