from datetime import datetime

from pydantic import BaseModel


class ActivePromotion(BaseModel):
    """A promotion running right now that opens modules which are otherwise sold."""

    name: str
    # Module ids from the catalog, e.g. "dlc-unlock".
    modules: list[str]
    # When the current window closes. For a weekly promotion this is the end of this week's window.
    ends_at: datetime


class ActivePromotions(BaseModel):
    promotions: list[ActivePromotion]
