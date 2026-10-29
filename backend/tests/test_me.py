from datetime import UTC, datetime
from uuid import uuid4

import pytest

from owlin.api.app import app
from owlin.api.deps import get_current_user
from owlin.core.config import Settings, get_settings
from owlin.core.security import TokenUser
from tests.conftest import FakeSession, make_row

USER = TokenUser(id=uuid4(), username="Pedro", avatar_url="https://cdn.example/a.png")
CREATED_AT = datetime(2026, 1, 5, 12, 0, tzinfo=UTC)


def sign_in(admin_ids: list[str] | None = None) -> None:
    app.dependency_overrides[get_current_user] = lambda: USER
    app.dependency_overrides[get_settings] = lambda: Settings(admin_discord_ids=admin_ids or [])


@pytest.mark.asyncio
async def test_me_requires_a_token(client) -> None:
    response = await client.get("/api/me")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.asyncio
async def test_me_rejects_an_invalid_token(client, monkeypatch) -> None:
    async def reject(_token: str):
        from owlin.core.security import AuthenticationError

        raise AuthenticationError

    monkeypatch.setattr("owlin.api.deps.verify_token", reject)

    response = await client.get("/api/me", headers={"Authorization": "Bearer nope"})

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_returns_the_profile(client, use_session) -> None:
    sign_in()
    use_session(FakeSession(row=make_row(discord_id="123", created_at=CREATED_AT)))

    response = await client.get("/api/me")

    assert response.status_code == 200
    assert response.json() == {
        "id": str(USER.id),
        "username": "Pedro",
        "avatar_url": "https://cdn.example/a.png",
        "discord_id": "123",
        "created_at": "2026-01-05T12:00:00Z",
        "is_admin": False,
    }


@pytest.mark.asyncio
async def test_me_marks_configured_discord_ids_as_admin(client, use_session) -> None:
    sign_in(admin_ids=["123"])
    use_session(FakeSession(row=make_row(discord_id="123", created_at=CREATED_AT)))

    response = await client.get("/api/me")

    assert response.json()["is_admin"] is True


@pytest.mark.asyncio
async def test_me_is_not_admin_without_a_discord_identity(client, use_session) -> None:
    sign_in(admin_ids=["123"])
    use_session(FakeSession(row=make_row(discord_id=None, created_at=CREATED_AT)))

    response = await client.get("/api/me")

    assert response.json()["is_admin"] is False


@pytest.mark.asyncio
async def test_me_rejects_a_user_missing_from_the_database(client, use_session) -> None:
    sign_in()
    use_session(FakeSession(row=None))

    response = await client.get("/api/me")

    assert response.status_code == 401
