from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from owlin.modules.catalog.constants import MAX_SCREENSHOTS_PER_ORDER
from owlin.modules.users.schemas import UserInfo


class ScreenshotDeclaration(BaseModel):
    content_type: str
    size_bytes: int = Field(gt=0)


class CreateOrderRequest(BaseModel):
    product: str
    period: str
    method: str
    coin: str | None = None
    # Declared up front so the server can hand out one upload slot per file.
    screenshots: list[ScreenshotDeclaration] = Field(min_length=1, max_length=MAX_SCREENSHOTS_PER_ORDER)


class UploadSlot(BaseModel):
    path: str
    token: str


class CreateOrderResponse(BaseModel):
    id: UUID
    amount_cents: int
    uploads: list[UploadSlot]


class SubmitOrderRequest(BaseModel):
    paths: list[str] = Field(min_length=1, max_length=MAX_SCREENSHOTS_PER_ORDER)
    proof_text: str | None = Field(default=None, max_length=300)
    note: str | None = Field(default=None, max_length=1000)


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
