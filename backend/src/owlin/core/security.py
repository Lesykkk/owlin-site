import asyncio
from dataclasses import dataclass
from functools import lru_cache
from typing import Any
from uuid import UUID

import jwt
from jwt import PyJWKClient, PyJWTError

from owlin.core.config import get_settings

JWT_ALGORITHMS = ["ES256"]
JWT_AUDIENCE = "authenticated"
# Clocks of two machines never agree exactly. A token issued a few seconds "in the future" (by our
# clock) is still accepted, so a slightly slow server or laptop does not reject fresh logins.
JWT_LEEWAY_SECONDS = 60


class AuthenticationError(Exception):
    """The access token is missing, malformed, expired or not signed by Supabase."""


@dataclass(frozen=True)
class TokenUser:
    """Who a valid token belongs to.

    `username` and `avatar_url` come from user_metadata, which users can edit themselves,
    so they are only fit for display. Never use them for access decisions.
    """

    id: UUID
    username: str
    avatar_url: str | None

    @classmethod
    def from_claims(cls, claims: dict[str, Any]) -> "TokenUser":
        meta = claims.get("user_metadata") or {}
        custom = meta.get("custom_claims") or {}
        return cls(
            id=UUID(claims["sub"]),
            username=custom.get("global_name") or meta.get("full_name") or meta.get("name") or "User",
            avatar_url=meta.get("avatar_url"),
        )


@lru_cache
def get_jwks_client() -> PyJWKClient:
    settings = get_settings()
    if not settings.supabase_url:
        raise RuntimeError("SUPABASE_URL is not set")
    # Keys are cached in memory for an hour; an unknown key id triggers one refresh.
    return PyJWKClient(settings.jwks_url, cache_keys=True, lifespan=3600)


async def verify_token(token: str) -> dict[str, Any]:
    """Check the signature, expiry, issuer and audience of a Supabase access token."""
    settings = get_settings()
    client = get_jwks_client()
    try:
        # PyJWKClient fetches keys over blocking HTTP, so keep it off the event loop.
        signing_key = await asyncio.to_thread(client.get_signing_key_from_jwt, token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=JWT_ALGORITHMS,
            audience=JWT_AUDIENCE,
            issuer=settings.jwt_issuer,
            options={"require": ["exp", "sub"]},
            leeway=JWT_LEEWAY_SECONDS,
        )
        UUID(claims["sub"])
    except (PyJWTError, ValueError) as error:
        raise AuthenticationError from error
    return claims
