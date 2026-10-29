from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from owlin.core.config import Settings, get_settings
from owlin.core.db import get_session
from owlin.core.security import AuthenticationError, TokenUser, verify_token
from owlin.integrations.supabase_storage import StorageClient, build_storage_client
from owlin.modules.users import service as users

def get_storage() -> StorageClient:
    return build_storage_client()


SessionDep = Annotated[AsyncSession, Depends(get_session)]
StorageDep = Annotated[StorageClient, Depends(get_storage)]
SettingsDep = Annotated[Settings, Depends(get_settings)]

bearer_scheme = HTTPBearer(auto_error=False)


def unauthorized(detail: str) -> HTTPException:
    return HTTPException(status_code=401, detail=detail, headers={"WWW-Authenticate": "Bearer"})


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> TokenUser:
    if credentials is None:
        raise unauthorized("Not authenticated")
    try:
        claims = await verify_token(credentials.credentials)
    except AuthenticationError:
        raise unauthorized("Invalid or expired token") from None
    return TokenUser.from_claims(claims)


CurrentUserDep = Annotated[TokenUser, Depends(get_current_user)]


async def get_admin(user: CurrentUserDep, session: SessionDep, settings: SettingsDep) -> TokenUser:
    """Allow only users whose Discord id is in ADMIN_DISCORD_IDS.

    The Discord id is read from auth.identities, which users cannot edit. The token's own
    metadata could be changed by the user, so it is never trusted for this.
    """
    account = await users.get_account(session, user.id)
    if account is None or account.discord_id not in settings.admin_discord_ids:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


AdminDep = Annotated[TokenUser, Depends(get_admin)]
