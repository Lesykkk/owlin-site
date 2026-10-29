import logging
from urllib.parse import quote

import httpx

from owlin.core.config import Settings, get_settings
from owlin.core.errors import UpstreamError

logger = logging.getLogger(__name__)

UPLOAD_TIMEOUT_SECONDS = 30


class StorageClient:
    """Minimal client for one private Supabase Storage bucket, using the server-side secret key."""

    def __init__(self, base_url: str, secret_key: str, bucket: str, transport: httpx.AsyncBaseTransport | None = None):
        self.base_url = base_url
        self.bucket = bucket
        self._headers = {"apikey": secret_key}
        self._transport = transport

    def _object_path(self, path: str) -> str:
        return f"{self.bucket}/{quote(path, safe='/')}"

    async def _request(self, method: str, url: str, timeout: float = 10, **kwargs) -> httpx.Response:
        try:
            async with httpx.AsyncClient(headers=self._headers, timeout=timeout, transport=self._transport) as client:
                return await client.request(method, url, **kwargs)
        except httpx.HTTPError as error:
            logger.exception("Storage request failed")
            raise UpstreamError("File storage is unavailable") from error

    async def upload_object(self, path: str, data: bytes, content_type: str) -> None:
        """Store a file. Never overwrites: a path that already exists is an error."""
        response = await self._request(
            "POST",
            f"{self.base_url}/object/{self._object_path(path)}",
            timeout=UPLOAD_TIMEOUT_SECONDS,
            content=data,
            headers={"Content-Type": content_type, "x-upsert": "false"},
        )
        if response.status_code != 200:
            logger.error("Storage refused an upload: %s %s", response.status_code, response.text)
            raise UpstreamError("File storage refused the upload")

    async def create_download_urls(self, paths: list[str], expires_in: int = 600) -> dict[str, str]:
        """Temporary links for many files in one request. Files that cannot be signed are left out."""
        if not paths:
            return {}
        response = await self._request(
            "POST",
            f"{self.base_url}/object/sign/{self.bucket}",
            json={"expiresIn": expires_in, "paths": paths},
        )
        if response.status_code != 200:
            logger.error("Storage refused to sign downloads: %s %s", response.status_code, response.text)
            raise UpstreamError("File storage refused the request")
        return {
            item["path"]: f"{self.base_url}{item['signedURL']}"
            for item in response.json()
            if item.get("signedURL")
        }

    async def delete_object(self, path: str) -> None:
        response = await self._request("DELETE", f"{self.base_url}/object/{self._object_path(path)}")
        if response.status_code not in (200, 404):
            logger.error("Storage delete failed: %s %s", response.status_code, response.text)
            raise UpstreamError("File storage refused the request")


def build_storage_client(settings: Settings | None = None) -> StorageClient:
    settings = settings or get_settings()
    if not settings.supabase_url or not settings.supabase_secret_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SECRET_KEY must be set")
    return StorageClient(settings.storage_url, settings.supabase_secret_key, settings.storage_bucket)
