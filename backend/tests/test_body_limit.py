import json

import httpx
import pytest

from owlin.api.middleware import DEFAULT_LIMIT_BYTES, LIMITS_BY_PATH, BodyLimitMiddleware

ORDERS_LIMIT = LIMITS_BY_PATH["/api/orders"]


async def echo_app(scope, receive, send) -> None:
    """Reads the whole body like a real endpoint would and answers with its size."""
    if scope["type"] != "http":
        return
    size = 0
    while True:
        message = await receive()
        size += len(message.get("body", b""))
        if not message.get("more_body"):
            break
    body = json.dumps({"size": size}).encode()
    await send({"type": "http.response.start", "status": 200, "headers": [(b"content-type", b"application/json")]})
    await send({"type": "http.response.body", "body": body})


@pytest.fixture
def client() -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=BodyLimitMiddleware(echo_app)), base_url="http://test")


async def chunks(total: int, size: int = 64 * 1024):
    sent = 0
    while sent < total:
        part = min(size, total - sent)
        sent += part
        yield b"x" * part


@pytest.mark.asyncio
async def test_a_body_within_the_limit_passes_through(client) -> None:
    response = await client.post("/api/orders", content=b"x" * 1000)

    assert response.status_code == 200
    assert response.json() == {"size": 1000}


@pytest.mark.asyncio
async def test_an_announced_body_over_the_limit_is_refused_at_once(client) -> None:
    response = await client.post("/api/orders", content=b"x" * (ORDERS_LIMIT + 1))

    assert response.status_code == 413
    assert response.json() == {"detail": "The request is too large"}


@pytest.mark.asyncio
async def test_a_chunked_body_over_the_limit_is_cut_off(client) -> None:
    # No Content-Length is announced, so the size is only known as the data arrives.
    response = await client.post("/api/orders", content=chunks(ORDERS_LIMIT + 200_000))

    assert response.status_code == 413


@pytest.mark.asyncio
async def test_other_endpoints_only_accept_small_bodies(client) -> None:
    assert (await client.post("/api/promo/claims", content=b"x" * DEFAULT_LIMIT_BYTES)).status_code == 200
    assert (await client.post("/api/promo/claims", content=b"x" * (DEFAULT_LIMIT_BYTES + 1))).status_code == 413


@pytest.mark.asyncio
async def test_reads_are_not_limited(client) -> None:
    assert (await client.get("/api/me")).status_code == 200
