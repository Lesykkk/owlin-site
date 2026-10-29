from collections.abc import AsyncIterator, Iterator

import pytest
from httpx import ASGITransport, AsyncClient

from owlin.api.app import app
from owlin.core.db import get_session


class FakeSession:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error

    async def execute(self, *_args: object, **_kwargs: object) -> None:
        if self.error:
            raise self.error


@pytest.fixture(autouse=True)
def clear_overrides() -> Iterator[None]:
    yield
    app.dependency_overrides.clear()


def use_session(session: FakeSession) -> None:
    async def override() -> AsyncIterator[FakeSession]:
        yield session

    app.dependency_overrides[get_session] = override


async def get(path: str):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.get(path)


@pytest.mark.asyncio
async def test_health_returns_ok() -> None:
    response = await get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_health_db_returns_ok_when_database_answers() -> None:
    use_session(FakeSession())

    response = await get("/health/db")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


@pytest.mark.asyncio
async def test_health_db_hides_details_when_database_fails() -> None:
    use_session(FakeSession(error=ConnectionError("password=secret host=db")))

    response = await get("/health/db")

    assert response.status_code == 503
    assert "secret" not in response.text
