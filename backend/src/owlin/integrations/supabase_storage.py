import logging
from dataclasses import dataclass
from urllib.parse import quote

import httpx

from owlin.core.config import Settings, get_settings
from owlin.core.errors import UpstreamError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UploadTarget:
    """What a browser needs to upload one file straight into the bucket."""

    path: str
    token: str


@dataclass(frozen=True)
class ObjectInfo:
    size_bytes: int
    content_type: str


class StorageClient:
    """Minimal client for one private Supabase Storage bucket, using the server-side secret key."""

    def __init__(self, base_url: str, secret_key: str, bucket: str, transport: httpx.AsyncBaseTransport | None = None):
        self.base_url = base_url
        self.bucket = bucket
        self._headers = {"apikey": secret_key}
        self._transport = transport

    def _object_path(self, path: str) -> str:
        return f"{self.bucket}/{quote(path, safe='/')}"

    async def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        try:
            async with httpx.AsyncClient(headers=self._headers, timeout=10, transport=self._transport) as client:
                return await client.request(method, url, **kwargs)
        except httpx.HTTPError as error:
            logger.exception("Storage request failed")
            raise UpstreamError("File storage is unavailable") from error

    async def create_upload_target(self, path: str) -> UploadTarget:
        response = await self._request("POST", f"{self.base_url}/object/upload/sign/{self._object_path(path)}")
        if response.status_code != 200:
            logger.error("Storage refused to sign an upload: %s %s", response.status_code, response.text)
            raise UpstreamError("File storage refused the request")
        return UploadTarget(path=path, token=response.json()["token"])

    async def get_object_info(self, path: str) -> ObjectInfo | None:
        """Metadata of an uploaded file, or None if there is no such file."""
        response = await self._request("GET", f"{self.base_url}/object/info/{self._object_path(path)}")
        if response.status_code in (400, 404):
            return None
        if response.status_code != 200:
            logger.error("Storage info failed: %s %s", response.status_code, response.text)
            raise UpstreamError("File storage refused the request")
        data = response.json()
        return ObjectInfo(size_bytes=int(data["size"]), content_type=data["content_type"])

    async def create_download_url(self, path: str, expires_in: int = 600) -> str:
        """A temporary link anyone can open without credentials, for an admin to view a file."""
        response = await self._request(
            "POST", f"{self.base_url}/object/sign/{self._object_path(path)}", json={"expiresIn": expires_in}
        )
        if response.status_code != 200:
            logger.error("Storage refused to sign a download: %s %s", response.status_code, response.text)
            raise UpstreamError("File storage refused the request")
        return f"{self.base_url}{response.json()['signedURL']}"

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
