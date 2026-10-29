from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile

from owlin.api.deps import CurrentUserDep, SessionDep, StorageDep
from owlin.core.errors import InvalidRequestError
from owlin.modules.catalog.constants import MAX_SCREENSHOT_BYTES, MAX_SCREENSHOTS_PER_ORDER
from owlin.modules.orders import service
from owlin.modules.orders.schemas import OrderResponse

router = APIRouter(prefix="/api", tags=["orders"])


async def read_screenshot(file: UploadFile) -> bytes:
    """Read one uploaded file, refusing to hold more than the allowed size in memory."""
    content = await file.read(MAX_SCREENSHOT_BYTES + 1)
    if len(content) > MAX_SCREENSHOT_BYTES:
        raise InvalidRequestError(f"Each screenshot must be at most {MAX_SCREENSHOT_BYTES // (1024 * 1024)} MB")
    return content


@router.post("/orders", status_code=201)
async def create_order(
    user: CurrentUserDep,
    session: SessionDep,
    storage: StorageDep,
    product: Annotated[str, Form()],
    period: Annotated[str, Form()],
    method: Annotated[str, Form()],
    screenshots: Annotated[list[UploadFile], File()],
    coin: Annotated[str | None, Form()] = None,
    proof_text: Annotated[str | None, Form(max_length=300)] = None,
    note: Annotated[str | None, Form(max_length=1000)] = None,
) -> OrderResponse:
    """Place an order: its data and screenshots in one multipart request.

    The order is either created under review with all its files stored, or refused and nothing is saved.
    """
    if len(screenshots) > MAX_SCREENSHOTS_PER_ORDER:
        raise InvalidRequestError(f"Attach from 1 to {MAX_SCREENSHOTS_PER_ORDER} screenshots")

    files = [await read_screenshot(file) for file in screenshots]
    data = service.NewOrder(
        product=product, period=period, method=method, coin=coin or None, proof_text=proof_text, note=note
    )
    order = await service.create_order(session, storage, user.id, data, files)
    return OrderResponse.model_validate(order)


@router.get("/me/orders")
async def list_my_orders(user: CurrentUserDep, session: SessionDep) -> list[OrderResponse]:
    orders = await service.list_orders(session, user.id)
    return [OrderResponse.model_validate(order) for order in orders]
