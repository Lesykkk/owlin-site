from collections.abc import AsyncIterator, Iterator
from types import SimpleNamespace

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from owlin.api.app import app
from owlin.core.db import get_session


class FakeResult:
    def __init__(self, row: object | None) -> None:
        self.row = row

    def one_or_none(self) -> object | None:
        return self.row


class FakeSession:
    """Stands in for AsyncSession. `row` is returned by execute(); `error` is raised instead."""

    def __init__(self, row: object | None = None, error: Exception | None = None) -> None:
        self.row = row
        self.error = error

    async def execute(self, *_args: object, **_kwargs: object) -> FakeResult:
        if self.error:
            raise self.error
        return FakeResult(self.row)


def make_row(**values: object) -> SimpleNamespace:
    return SimpleNamespace(**values)


@pytest.fixture(autouse=True)
def clear_overrides() -> Iterator[None]:
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def use_session():
    def install(session: object) -> None:
        async def override() -> AsyncIterator[FakeSession]:
            yield session

        app.dependency_overrides[get_session] = override

    return install


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http_client:
        yield http_client
