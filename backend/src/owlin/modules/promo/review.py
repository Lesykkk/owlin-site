"""Admin side of promo claims: the review queue, approving and rejecting."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from owlin.core.errors import ConflictError, InvalidRequestError, NotFoundError
from owlin.modules.catalog.constants import PROMO_DAYS, PROMO_MIN_VIEWS
from owlin.modules.promo.models import PromoClaim
from owlin.modules.promo.schemas import AdminPromoClaimResponse, PromoClaimResponse
from owlin.modules.subscriptions import service as subscriptions
from owlin.modules.users import service as users
from owlin.modules.users.schemas import UserInfo

ADMIN_LIST_LIMIT = 100


async def approve_claim(
    session: AsyncSession, claim_id: UUID, admin_id: UUID, views: int | None, now: datetime | None = None
) -> PromoClaim:
    """Accept a video: give the user free days. One transaction under a lock on the claim."""
    now = now or datetime.now(UTC)

    claim = await session.get(PromoClaim, claim_id, with_for_update=True)
    if claim is None:
        raise NotFoundError("Promo claim not found")
    if claim.status != "review":
        raise ConflictError("Only claims under review can be approved")

    minimum = PROMO_MIN_VIEWS[claim.platform]
    if minimum is not None and (views is None or views < minimum):
        raise InvalidRequestError(f"This video needs at least {minimum} views.")

    grants = await subscriptions.grant_product(
        session,
        user_id=claim.user_id,
        product_id=claim.reward_product,
        days=PROMO_DAYS,
        source="promo",
        promo_claim_id=claim.id,
        granted_by=admin_id,
        now=now,
    )

    claim.status = "approved"
    claim.views = views
    claim.reject_reason = None
    claim.reviewed_by = admin_id
    claim.reviewed_at = now
    # The claim keeps its slot until these free days run out.
    claim.expires_at = grants[0].ends_at

    await session.commit()
    await session.refresh(claim)
    return claim


async def reject_claim(
    session: AsyncSession, claim_id: UUID, admin_id: UUID, reason: str, now: datetime | None = None
) -> PromoClaim:
    now = now or datetime.now(UTC)

    claim = await session.get(PromoClaim, claim_id, with_for_update=True)
    if claim is None:
        raise NotFoundError("Promo claim not found")
    if claim.status != "review":
        raise ConflictError("Only claims under review can be rejected")

    claim.status = "rejected"
    claim.reject_reason = reason.strip()
    claim.reviewed_by = admin_id
    claim.reviewed_at = now

    await session.commit()
    await session.refresh(claim)
    return claim


async def list_claims_for_admin(session: AsyncSession, status: str | None) -> list[AdminPromoClaimResponse]:
    """The review queue (oldest first) or a history list (newest first)."""
    statement = select(PromoClaim)
    if status is not None:
        statement = statement.where(PromoClaim.status == status)
    ordering = PromoClaim.created_at.asc() if status == "review" else PromoClaim.created_at.desc()

    result = await session.scalars(statement.order_by(ordering).limit(ADMIN_LIST_LIMIT))
    return await describe_for_admin(session, list(result.all()))


async def describe_for_admin(session: AsyncSession, claims: list[PromoClaim]) -> list[AdminPromoClaimResponse]:
    profiles = await users.get_profiles(session, [claim.user_id for claim in claims])

    described = []
    for claim in claims:
        profile = profiles.get(claim.user_id)
        user = UserInfo(
            id=claim.user_id,
            username=profile.username if profile else "Unknown",
            avatar_url=profile.avatar_url if profile else None,
            discord_id=profile.discord_id if profile else None,
        )
        described.append(
            AdminPromoClaimResponse(
                **PromoClaimResponse.model_validate(claim).model_dump(), reviewed_at=claim.reviewed_at, user=user
            )
        )
    return described
