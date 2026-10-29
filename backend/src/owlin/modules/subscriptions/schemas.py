from datetime import datetime

from pydantic import BaseModel


class SubscriptionInfo(BaseModel):
    active: bool
    # When access ends. Empty while active means it never ends.
    expires_at: datetime | None
    lifetime: bool
