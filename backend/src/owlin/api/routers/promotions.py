from datetime import UTC, datetime

from fastapi import APIRouter, Response

from owlin.api.deps import SessionDep
from owlin.modules.access_promotions import service
from owlin.modules.access_promotions.schemas import ActivePromotions

router = APIRouter(prefix="/api", tags=["promotions"])


@router.get("/promotions/active")
async def active_promotions(response: Response, session: SessionDep) -> ActivePromotions:
    """Promotions that are open for everyone right now. Public: it holds nothing personal."""
    response.headers["Cache-Control"] = f"public, max-age={service.CACHE_SECONDS}"
    return ActivePromotions(promotions=await service.list_active(session, datetime.now(UTC)))
