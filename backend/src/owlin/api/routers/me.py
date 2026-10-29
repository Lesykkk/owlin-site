from datetime import UTC, datetime

from fastapi import APIRouter

from owlin.api.deps import CurrentUserDep, SessionDep, SettingsDep, unauthorized
from owlin.modules.overview import service as overview_service
from owlin.modules.users.schemas import MeResponse

router = APIRouter(prefix="/api", tags=["me"])


@router.get("/me")
async def read_me(user: CurrentUserDep, session: SessionDep, settings: SettingsDep) -> MeResponse:
    overview = await overview_service.load_overview(session, user.id, datetime.now(UTC))
    if overview is None:
        # A valid token for a user that no longer exists.
        raise unauthorized("User not found")

    return MeResponse(
        id=user.id,
        username=user.username,
        avatar_url=user.avatar_url,
        discord_id=overview.discord_id,
        created_at=overview.created_at,
        # The Discord id comes from auth.identities, which users cannot edit.
        is_admin=overview.discord_id in settings.admin_discord_ids,
        subscriptions=overview.subscriptions,
        balance_cents=overview.balance_cents,
        last_seen_at=overview.last_seen_at,
    )
