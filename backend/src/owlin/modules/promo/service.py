from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from owlin.core.errors import ConflictError, InvalidRequestError
from owlin.modules.catalog.constants import MAX_PROMO_SLOTS, MODULE_IDS, PROMO_PLATFORM_IDS
from owlin.modules.promo.models import PromoClaim
from owlin.modules.promo.video_links import ParsedVideo, parse_video_link

LIST_LIMIT = 100


async def count_occupied_slots(session: AsyncSession, user_id: UUID, now: datetime) -> int:
    """Claims that still use one of the user's slots: under review, or approved and not yet expired."""
    occupied = (PromoClaim.status == "review") | ((PromoClaim.status == "approved") & (PromoClaim.expires_at > now))
    count = await session.scalar(
        select(func.count()).select_from(PromoClaim).where(PromoClaim.user_id == user_id, occupied)
    )
    return count or 0


async def check_claim(
    session: AsyncSession, user_id: UUID, platform: str, url: str, reward_product: str, now: datetime
) -> ParsedVideo:
    """Everything that can be checked before submitting. Raises if the claim would be refused."""
    if platform not in PROMO_PLATFORM_IDS:
        raise InvalidRequestError("Unknown platform")
    if reward_product not in MODULE_IDS:
        raise InvalidRequestError("Unknown reward")

    video = parse_video_link(url, platform)

    taken = await session.scalar(
        select(PromoClaim.id).where(PromoClaim.video_key == video.key, PromoClaim.status != "rejected").limit(1)
    )
    if taken is not None:
        raise ConflictError("This video was already used for a promo reward. Submit a different one.")

    if await count_occupied_slots(session, user_id, now) >= MAX_PROMO_SLOTS:
        raise ConflictError(
            f"All {MAX_PROMO_SLOTS} promo slots are in use. A slot frees up when a video is rejected "
            "or its reward expires."
        )
    return video


async def create_claim(
    session: AsyncSession,
    user_id: UUID,
    platform: str,
    url: str,
    reward_product: str,
    now: datetime | None = None,
) -> PromoClaim:
    now = now or datetime.now(UTC)
    video = await check_claim(session, user_id, platform, url, reward_product, now)

    claim = PromoClaim(
        id=uuid4(),
        user_id=user_id,
        platform=platform,
        video_key=video.key,
        url=url.strip(),
        reward_product=reward_product,
        status="review",
    )
    session.add(claim)
    try:
        await session.flush()
    except IntegrityError:
        # Someone submitted the same video between our check and the insert.
        await session.rollback()
        raise ConflictError("This video was already used for a promo reward. Submit a different one.") from None

    await session.commit()
    await session.refresh(claim)
    return claim


async def list_claims(session: AsyncSession, user_id: UUID) -> list[PromoClaim]:
    result = await session.scalars(
        select(PromoClaim).where(PromoClaim.user_id == user_id).order_by(PromoClaim.created_at.desc()).limit(LIST_LIMIT)
    )
    return list(result.all())
