import pytest

from tests.conftest import FakeSession


@pytest.mark.asyncio
async def test_health_returns_ok(client) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_health_db_returns_ok_when_database_answers(client, use_session) -> None:
    use_session(FakeSession())

    response = await client.get("/health/db")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


@pytest.mark.asyncio
async def test_health_db_hides_details_when_database_fails(client, use_session) -> None:
    use_session(FakeSession(error=ConnectionError("password=secret host=db")))

    response = await client.get("/health/db")

    assert response.status_code == 503
    assert "secret" not in response.text
