import time
from types import SimpleNamespace
from uuid import uuid4

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec

from owlin.core import security
from owlin.core.config import Settings
from owlin.core.security import AuthenticationError, TokenUser, verify_token

SUPABASE_URL = "https://project.supabase.co"
ISSUER = f"{SUPABASE_URL}/auth/v1"


def make_key() -> ec.EllipticCurvePrivateKey:
    return ec.generate_private_key(ec.SECP256R1())


def make_token(key: ec.EllipticCurvePrivateKey, **overrides: object) -> str:
    claims = {
        "sub": str(uuid4()),
        "aud": "authenticated",
        "iss": ISSUER,
        "exp": int(time.time()) + 600,
        **overrides,
    }
    return jwt.encode(claims, key, algorithm="ES256", headers={"kid": "test-key"})


@pytest.fixture
def signing_key(monkeypatch: pytest.MonkeyPatch) -> ec.EllipticCurvePrivateKey:
    """Pretends Supabase publishes the public half of a freshly generated key."""
    key = make_key()
    jwks_client = SimpleNamespace(get_signing_key_from_jwt=lambda _token: SimpleNamespace(key=key.public_key()))
    monkeypatch.setattr(security, "get_jwks_client", lambda: jwks_client)
    monkeypatch.setattr(security, "get_settings", lambda: Settings(supabase_url=SUPABASE_URL))
    return key


@pytest.mark.asyncio
async def test_valid_token_returns_claims(signing_key) -> None:
    user_id = str(uuid4())

    claims = await verify_token(make_token(signing_key, sub=user_id))

    assert claims["sub"] == user_id


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "overrides",
    [
        {"exp": int(time.time()) - 300},
        {"aud": "someone-else"},
        {"iss": "https://evil.example/auth/v1"},
        {"sub": "not-a-uuid"},
    ],
)
async def test_bad_claims_are_rejected(signing_key, overrides) -> None:
    with pytest.raises(AuthenticationError):
        await verify_token(make_token(signing_key, **overrides))


@pytest.mark.asyncio
async def test_a_token_issued_a_few_seconds_ahead_of_our_clock_is_accepted(signing_key) -> None:
    # Our clock may run slightly behind the one that issued the token.
    claims = await verify_token(make_token(signing_key, iat=int(time.time()) + 20))

    assert "sub" in claims


@pytest.mark.asyncio
async def test_a_token_issued_far_in_the_future_is_still_rejected(signing_key) -> None:
    with pytest.raises(AuthenticationError):
        await verify_token(make_token(signing_key, iat=int(time.time()) + 600, exp=int(time.time()) + 1200))


@pytest.mark.asyncio
async def test_a_token_that_expired_a_few_seconds_ago_is_accepted_within_the_leeway(signing_key) -> None:
    claims = await verify_token(make_token(signing_key, exp=int(time.time()) - 10))

    assert "sub" in claims


@pytest.mark.asyncio
async def test_token_signed_with_another_key_is_rejected(signing_key) -> None:
    with pytest.raises(AuthenticationError):
        await verify_token(make_token(make_key()))


@pytest.mark.asyncio
async def test_garbage_token_is_rejected(signing_key) -> None:
    with pytest.raises(AuthenticationError):
        await verify_token("not-a-jwt")


def test_user_is_built_from_discord_metadata() -> None:
    user_id = uuid4()

    user = TokenUser.from_claims(
        {
            "sub": str(user_id),
            "user_metadata": {
                "custom_claims": {"global_name": "Pedro"},
                "full_name": "pedro#0",
                "avatar_url": "https://cdn.example/a.png",
            },
        }
    )

    assert user == TokenUser(id=user_id, username="Pedro", avatar_url="https://cdn.example/a.png")


def test_user_falls_back_when_metadata_is_missing() -> None:
    user = TokenUser.from_claims({"sub": str(uuid4())})

    assert user.username == "User"
    assert user.avatar_url is None
