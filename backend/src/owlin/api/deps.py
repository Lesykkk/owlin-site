from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from owlin.core.config import Settings, get_settings
from owlin.core.db import get_session
from owlin.core.security import AuthenticationError, TokenUser, verify_token

SessionDep = Annotated[AsyncSession, Depends(get_session)]
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
