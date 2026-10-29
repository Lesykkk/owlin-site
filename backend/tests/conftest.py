from datetime import UTC, datetime
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


class ServiceSession:
    """A stand-in for AsyncSession in service tests.

    get() returns `objects[model]`; scalar() returns the given values one by one, in call order.
    """

    def __init__(self, objects: dict[type, object] | None = None, scalar_values: list[object] | None = None) -> None:
        self.objects = objects or {}
        self.scalar_values = list(scalar_values or [])
        self.added: list[object] = []
        self.committed = False
        self.rolled_back = False
        self.flush_error: Exception | None = None
        self.execute_rows: list[tuple] = []

    async def get(self, model: type, _key: object, with_for_update: bool = False) -> object | None:
        return self.objects.get(model)

    async def execute(self, _statement: object) -> SimpleNamespace:
        return SimpleNamespace(all=lambda: self.execute_rows)

    async def scalar(self, _statement: object) -> object | None:
        return self.scalar_values.pop(0) if self.scalar_values else None

    def add(self, item: object) -> None:
        self.added.append(item)

    async def flush(self) -> None:
        if self.flush_error:
            raise self.flush_error

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.rolled_back = True

    async def refresh(self, item: object) -> None:
        # The real refresh reloads database defaults such as created_at.
        if getattr(item, "created_at", "n/a") is None:
            item.created_at = datetime(2026, 10, 29, 12, 0, tzinfo=UTC)

    def added_of(self, model: type) -> list:
        return [item for item in self.added if isinstance(item, model)]


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
