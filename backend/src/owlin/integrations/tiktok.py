"""Turns a TikTok short link (vm.tiktok.com/…) into the full video link by following its redirect.

A short link holds no video id, so the id behind it is only known to TikTok. Only TikTok hosts are
ever requested, and every redirect is checked before it is followed.
"""

from urllib.parse import urljoin, urlsplit

import httpx

from owlin.core.errors import InvalidRequestError
from owlin.modules.promo.video_links import TIKTOK_HOSTS, TIKTOK_VIDEO_PATH, split_link

SHORT_HOSTS = {"vm.tiktok.com", "vt.tiktok.com"}
MAX_REDIRECTS = 3
TIMEOUT_SECONDS = 5
USER_AGENT = "Mozilla/5.0 (compatible; OwlinLinkCheck/1.0)"
UNRESOLVED = "Could not check this TikTok link. Open the video in TikTok and copy its full link (tiktok.com/@name/video/…)."


def is_short_link(raw: str) -> bool:
    try:
        parts, host = split_link(raw)
    except InvalidRequestError:
        return False
    return host in SHORT_HOSTS and parts.path.strip("/") != ""


def is_tiktok_url(url: str) -> bool:
    parts = urlsplit(url)
    host = (parts.hostname or "").lower().removeprefix("www.").removeprefix("m.")
    return parts.scheme == "https" and host in TIKTOK_HOSTS


async def resolve_short_link(raw: str, transport: httpx.AsyncBaseTransport | None = None) -> str:
    """Returns the full video link behind a short link, or raises if it cannot be resolved."""
    parts, _host = split_link(raw)
    url = f"https://{parts.netloc}{parts.path}"

    try:
        async with httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT_SECONDS, follow_redirects=False, transport=transport
        ) as client:
            for _ in range(MAX_REDIRECTS + 1):
                if not is_tiktok_url(url):
                    break
                if TIKTOK_VIDEO_PATH.match(urlsplit(url).path):
                    return url
                response = await client.get(url)
                location = response.headers.get("location")
                if not response.is_redirect or not location:
                    break
                url = urljoin(url, location)
    except httpx.HTTPError:
        pass

    raise InvalidRequestError(UNRESOLVED)
