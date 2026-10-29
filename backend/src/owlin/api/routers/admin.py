from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Query

from owlin.api.deps import AdminDep, SessionDep, StorageDep
from owlin.modules.orders import review as order_review
from owlin.modules.orders.schemas import AdminOrderResponse, ApproveOrderRequest, RejectRequest
from owlin.modules.promo import review as promo_review
from owlin.modules.promo.schemas import AdminPromoClaimResponse, ApproveClaimRequest

router = APIRouter(prefix="/api/admin", tags=["admin"])

StatusFilter = Annotated[Literal["review", "approved", "rejected", "all"], Query()]


def status_or_none(status: str) -> str | None:
    return None if status == "all" else status


@router.get("/orders")
async def list_orders(
    admin: AdminDep, session: SessionDep, storage: StorageDep, status: StatusFilter = "review"
) -> list[AdminOrderResponse]:
    return await order_review.list_orders_for_admin(session, storage, status_or_none(status))


@router.post("/orders/{order_id}/approve")
async def approve_order(
    order_id: UUID, body: ApproveOrderRequest, admin: AdminDep, session: SessionDep, storage: StorageDep
) -> AdminOrderResponse:
    order = await order_review.approve_order(session, order_id, admin.id, body.received_cents)
    return (await order_review.describe_for_admin(session, storage, [order]))[0]


@router.post("/orders/{order_id}/reject")
async def reject_order(
    order_id: UUID, body: RejectRequest, admin: AdminDep, session: SessionDep, storage: StorageDep
) -> AdminOrderResponse:
    order = await order_review.reject_order(session, order_id, admin.id, body.reason)
    return (await order_review.describe_for_admin(session, storage, [order]))[0]


@router.get("/promo-claims")
async def list_promo_claims(
    admin: AdminDep, session: SessionDep, status: StatusFilter = "review"
) -> list[AdminPromoClaimResponse]:
    return await promo_review.list_claims_for_admin(session, status_or_none(status))


@router.post("/promo-claims/{claim_id}/approve")
async def approve_promo_claim(
    claim_id: UUID, body: ApproveClaimRequest, admin: AdminDep, session: SessionDep
) -> AdminPromoClaimResponse:
    claim = await promo_review.approve_claim(session, claim_id, admin.id, body.views)
    return (await promo_review.describe_for_admin(session, [claim]))[0]


@router.post("/promo-claims/{claim_id}/reject")
async def reject_promo_claim(
    claim_id: UUID, body: RejectRequest, admin: AdminDep, session: SessionDep
) -> AdminPromoClaimResponse:
    claim = await promo_review.reject_claim(session, claim_id, admin.id, body.reason)
    return (await promo_review.describe_for_admin(session, [claim]))[0]
