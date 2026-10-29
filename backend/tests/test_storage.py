import httpx
import pytest

from owlin.core.errors import UpstreamError
from owlin.integrations.supabase_storage import StorageClient

BASE = "https://project.supabase.co/storage/v1"


def make_client(handler) -> StorageClient:
    return StorageClient(BASE, "sb_secret_test", "payment-proofs", transport=httpx.MockTransport(handler))


@pytest.mark.asyncio
async def test_upload_sends_the_file_with_the_secret_key_and_never_overwrites() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"Key": "payment-proofs/user/order/file.png"})

    await make_client(handler).upload_object("user/order/file.png", b"png-bytes", "image/png")

    [request] = seen
    assert request.method == "POST"
    assert str(request.url) == f"{BASE}/object/payment-proofs/user/order/file.png"
    assert request.content == b"png-bytes"
    assert request.headers["content-type"] == "image/png"
    assert request.headers["x-upsert"] == "false"
    assert request.headers["apikey"] == "sb_secret_test"


@pytest.mark.asyncio
async def test_a_refused_upload_becomes_an_upstream_error_without_leaking_details() -> None:
    client = make_client(lambda _request: httpx.Response(400, text="secret internal detail"))

    with pytest.raises(UpstreamError) as error:
        await client.upload_object("a.png", b"x", "image/png")

    assert "secret" not in error.value.message


@pytest.mark.asyncio
async def test_a_network_failure_becomes_an_upstream_error() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom")

    with pytest.raises(UpstreamError):
        await make_client(handler).upload_object("a.png", b"x", "image/png")


@pytest.mark.asyncio
async def test_download_urls_are_requested_in_one_call_and_made_absolute() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            200,
            json=[
                {"path": "a.png", "signedURL": "/object/sign/payment-proofs/a.png?token=t1", "error": None},
                {"path": "gone.png", "signedURL": None, "error": "not found"},
            ],
        )

    urls = await make_client(handler).create_download_urls(["a.png", "gone.png"])

    assert urls == {"a.png": f"{BASE}/object/sign/payment-proofs/a.png?token=t1"}
    assert len(seen) == 1
    assert str(seen[0].url) == f"{BASE}/object/sign/payment-proofs"


@pytest.mark.asyncio
async def test_no_paths_means_no_request() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise AssertionError("no request expected")

    assert await make_client(handler).create_download_urls([]) == {}


@pytest.mark.asyncio
@pytest.mark.parametrize("status, expected_ok", [(200, True), (404, True), (500, False)])
async def test_deleting_a_missing_file_is_fine(status: int, expected_ok: bool) -> None:
    client = make_client(lambda _request: httpx.Response(status, json={}))

    if expected_ok:
        await client.delete_object("a.png")
    else:
        with pytest.raises(UpstreamError):
            await client.delete_object("a.png")
