import httpx
import pytest

from owlin.core.errors import UpstreamError
from owlin.integrations.supabase_storage import StorageClient

BASE = "https://project.supabase.co/storage/v1"


def make_client(handler) -> StorageClient:
    return StorageClient(BASE, "sb_secret_test", "payment-proofs", transport=httpx.MockTransport(handler))


@pytest.mark.asyncio
async def test_upload_target_requests_a_signed_url_with_the_secret_key() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"url": "/object/upload/sign/x", "token": "tok-123"})

    target = await make_client(handler).create_upload_target("user/order/file.png")

    assert target.token == "tok-123"
    assert target.path == "user/order/file.png"
    assert str(seen[0].url) == f"{BASE}/object/upload/sign/payment-proofs/user/order/file.png"
    assert seen[0].method == "POST"
    assert seen[0].headers["apikey"] == "sb_secret_test"


@pytest.mark.asyncio
async def test_object_info_returns_size_and_type() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"size": 70, "content_type": "image/png"})

    info = await make_client(handler).get_object_info("a/b.png")

    assert (info.size_bytes, info.content_type) == (70, "image/png")


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [400, 404])
async def test_object_info_is_none_when_the_file_is_missing(status: int) -> None:
    client = make_client(lambda _request: httpx.Response(status, json={"error": "not_found"}))

    assert await client.get_object_info("a/b.png") is None


@pytest.mark.asyncio
async def test_download_url_is_absolute() -> None:
    client = make_client(lambda _request: httpx.Response(200, json={"signedURL": "/object/sign/payment-proofs/a.png?token=t"}))

    url = await client.create_download_url("a.png")

    assert url == f"{BASE}/object/sign/payment-proofs/a.png?token=t"


@pytest.mark.asyncio
async def test_storage_errors_become_upstream_errors_without_leaking_details() -> None:
    client = make_client(lambda _request: httpx.Response(500, text="secret internal detail"))

    with pytest.raises(UpstreamError) as error:
        await client.create_upload_target("a.png")

    assert "secret" not in error.value.message


@pytest.mark.asyncio
async def test_network_failure_becomes_an_upstream_error() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom")

    with pytest.raises(UpstreamError):
        await make_client(handler).create_upload_target("a.png")
