from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from owlin.modules.users.schemas import PromoSlots, UserInfo


class ClaimRequest(BaseModel):
    platform: str
    url: str = Field(min_length=1, max_length=2000)
    # The module the free days are for: "spoofer" or "dlc-unlock".
    reward_product: str


class ApproveClaimRequest(BaseModel):
    # The view count the admin saw. Required for platforms with a minimum.
    views: int | None = Field(default=None, ge=0)


class PromoClaimResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    platform: str
    url: str
    reward_product: str
    status: str
    views: int | None
    reject_reason: str | None
    # When the granted free days run out. Empty until approved.
    expires_at: datetime | None


class PromoOverview(BaseModel):
    claims: list[PromoClaimResponse]
    slots: PromoSlots


class AdminPromoClaimResponse(PromoClaimResponse):
    reviewed_at: datetime | None
    user: UserInfo
