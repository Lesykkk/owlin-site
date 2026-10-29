from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from owlin.modules.users.schemas import UserInfo


class ApproveOrderRequest(BaseModel):
    # What the admin saw arrive. Anything above the order amount goes to the user's balance.
    received_cents: int = Field(gt=0)


class RejectRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=300)


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    product: str
    period: str
    method: str
    coin: str | None
    amount_cents: int
    status: str
    received_cents: int | None
    balance_added_cents: int | None
    reject_reason: str | None


class AdminScreenshot(BaseModel):
    # A temporary link; empty if the file could not be signed.
    url: str | None
    content_type: str


class AdminOrderResponse(OrderResponse):
    """An order as an admin sees it: who paid, what they wrote and the proof screenshots."""

    proof_text: str | None
    note: str | None
    reviewed_at: datetime | None
    user: UserInfo
    screenshots: list[AdminScreenshot]
