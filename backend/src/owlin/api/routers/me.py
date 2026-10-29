from datetime import UTC, datetime

from fastapi import APIRouter

from owlin.api.deps import CurrentUserDep, SessionDep, SettingsDep, unauthorized
from owlin.modules.balance import service as balance
from owlin.modules.catalog.constants import MAX_PROMO_SLOTS
from owlin.modules.devices import service as devices
from owlin.modules.promo import service as promo
from owlin.modules.subscriptions import service as subscriptions
from owlin.modules.users import service as users
from owlin.modules.users.schemas import MeResponse, PromoSlots

router = APIRouter(prefix="/api", tags=["me"])


@router.get("/me")
async def read_me(user: CurrentUserDep, session: SessionDep, settings: SettingsDep) -> MeResponse:
    account = await users.get_account(session, user.id)
    if account is None:
        # A valid token for a user that no longer exists.
        raise unauthorized("User not found")

    now = datetime.now(UTC)
    return MeResponse(
        id=user.id,
        username=user.username,
        avatar_url=user.avatar_url,
        discord_id=account.discord_id,
        created_at=account.created_at,
        # The Discord id comes from auth.identities, which users cannot edit.
        is_admin=account.discord_id in settings.admin_discord_ids,
        subscriptions=await subscriptions.get_overview(session, user.id, now),
        balance_cents=await balance.get_balance(session, user.id),
        promo_slots=PromoSlots(used=await promo.count_occupied_slots(session, user.id, now), max=MAX_PROMO_SLOTS),
        last_seen_at=await devices.get_last_seen(session, user.id),
    )
