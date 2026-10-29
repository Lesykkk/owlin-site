from datetime import UTC, datetime

from fastapi import APIRouter

from owlin.api.deps import CurrentUserDep, SessionDep
from owlin.modules.catalog.constants import MAX_PROMO_SLOTS
from owlin.modules.promo import service
from owlin.modules.promo.schemas import ClaimRequest, PromoClaimResponse, PromoOverview
from owlin.modules.users.schemas import PromoSlots

router = APIRouter(prefix="/api", tags=["promo"])


@router.post("/promo/check")
async def check_promo(body: ClaimRequest, user: CurrentUserDep, session: SessionDep) -> dict[str, str]:
    """Ask whether a video would be accepted, without submitting it."""
    await service.check_claim(session, user.id, body.platform, body.url, body.reward_product, datetime.now(UTC))
    return {"status": "ok"}


@router.post("/promo/claims", status_code=201)
async def create_promo_claim(body: ClaimRequest, user: CurrentUserDep, session: SessionDep) -> PromoClaimResponse:
    claim = await service.create_claim(session, user.id, body.platform, body.url, body.reward_product)
    return PromoClaimResponse.model_validate(claim)


@router.get("/me/promo")
async def my_promo(user: CurrentUserDep, session: SessionDep) -> PromoOverview:
    claims = await service.list_claims(session, user.id)
    used = await service.count_occupied_slots(session, user.id, datetime.now(UTC))
    return PromoOverview(
        claims=[PromoClaimResponse.model_validate(claim) for claim in claims],
        slots=PromoSlots(used=used, max=MAX_PROMO_SLOTS),
    )
