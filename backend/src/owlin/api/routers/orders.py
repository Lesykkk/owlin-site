from uuid import UUID

from fastapi import APIRouter

from owlin.api.deps import CurrentUserDep, SessionDep, StorageDep
from owlin.modules.orders import service
from owlin.modules.orders.schemas import (
    CreateOrderRequest,
    CreateOrderResponse,
    OrderResponse,
    SubmitOrderRequest,
    UploadSlot,
)

router = APIRouter(prefix="/api", tags=["orders"])


@router.post("/orders", status_code=201)
async def create_order(
    body: CreateOrderRequest, user: CurrentUserDep, session: SessionDep, storage: StorageDep
) -> CreateOrderResponse:
    """Step 1: create the order and get a place to upload each screenshot."""
    order, targets = await service.create_order(session, storage, user.id, body)
    return CreateOrderResponse(
        id=order.id,
        amount_cents=order.amount_cents,
        uploads=[UploadSlot(path=target.path, token=target.token) for target in targets],
    )


@router.post("/orders/{order_id}/submit")
async def submit_order(
    order_id: UUID, body: SubmitOrderRequest, user: CurrentUserDep, session: SessionDep, storage: StorageDep
) -> OrderResponse:
    """Step 2: after uploading the files, send the order to review."""
    order = await service.submit_order(session, storage, user.id, order_id, body.paths, body.proof_text, body.note)
    return OrderResponse.model_validate(order)


@router.get("/me/orders")
async def list_my_orders(user: CurrentUserDep, session: SessionDep) -> list[OrderResponse]:
    orders = await service.list_orders(session, user.id)
    return [OrderResponse.model_validate(order) for order in orders]
