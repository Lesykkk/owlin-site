from fastapi import APIRouter

from owlin.api.deps import CurrentUserDep, SessionDep, SettingsDep, unauthorized
from owlin.modules.users import service as users
from owlin.modules.users.schemas import MeResponse

router = APIRouter(prefix="/api", tags=["me"])


@router.get("/me")
async def read_me(user: CurrentUserDep, session: SessionDep, settings: SettingsDep) -> MeResponse:
    account = await users.get_account(session, user.id)
    if account is None:
        # A valid token for a user that no longer exists.
        raise unauthorized("User not found")

    return MeResponse(
        id=user.id,
        username=user.username,
        avatar_url=user.avatar_url,
        discord_id=account.discord_id,
        created_at=account.created_at,
        # The Discord id comes from auth.identities, which users cannot edit.
        is_admin=account.discord_id in settings.admin_discord_ids,
    )
