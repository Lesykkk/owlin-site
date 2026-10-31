"""Turns a pasted video link into one stable key, so the same video cannot be submitted twice.

The key is "platform:video id" for TikTok and YouTube. Other sites have no video id, so the
cleaned-up address itself is the key. The site's form runs the same checks to save the user a
round trip; this is the authoritative copy.
"""

import re
from dataclasses import dataclass
from urllib.parse import SplitResult, parse_qsl, urlencode, urlsplit

from owlin.core.errors import InvalidRequestError

YOUTUBE_ID = re.compile(r"[\w-]{11}")
YOUTUBE_PATH_ID = re.compile(r"/(?:shorts|live|embed)/([^/]+)")
TIKTOK_VIDEO_PATH = re.compile(r"/@[^/]+/video/(\d+)")
TIKTOK_HOSTS = {"tiktok.com", "vm.tiktok.com", "vt.tiktok.com"}
YOUTUBE_HOSTS = {"youtube.com", "youtu.be"}
TRACKING_PARAMS = {"fbclid", "gclid", "igshid", "si"}


@dataclass(frozen=True)
class ParsedVideo:
    key: str


def split_link(raw: str) -> tuple[SplitResult, str]:
    text = raw.strip()
    if not text:
        raise InvalidRequestError("Paste a link to your video.")
    if not re.match(r"https?://", text, re.IGNORECASE):
        text = f"https://{text}"

    try:
        parts = urlsplit(text)
        host = parts.hostname
    except ValueError:
        host = None
    if not host or "." not in host:
        raise InvalidRequestError("Paste a link to your video.")

    return parts, re.sub(r"^(www|m)\.", "", host.lower())


def parse_tiktok(parts: SplitResult, host: str) -> ParsedVideo:
    match = TIKTOK_VIDEO_PATH.match(parts.path)
    if host not in TIKTOK_HOSTS or not match:
        raise InvalidRequestError("Open the video in TikTok and copy its full link (tiktok.com/@name/video/…).")
    video_id = match.group(1)
    return ParsedVideo(key=f"tiktok:{video_id}")


def parse_youtube(parts: SplitResult, host: str) -> ParsedVideo:
    video_id = None
    if host == "youtu.be":
        video_id = parts.path[1:].split("/")[0]
    elif host == "youtube.com":
        if parts.path == "/watch":
            video_id = dict(parse_qsl(parts.query)).get("v")
        elif match := YOUTUBE_PATH_ID.match(parts.path):
            video_id = match.group(1)

    if not video_id or not YOUTUBE_ID.fullmatch(video_id):
        raise InvalidRequestError("Paste the link to a YouTube video.")
    return ParsedVideo(key=f"youtube:{video_id}")


def parse_other(parts: SplitResult, host: str) -> ParsedVideo:
    if host in TIKTOK_HOSTS or host in YOUTUBE_HOSTS:
        raise InvalidRequestError("Choose TikTok or YouTube for this link.")
    kept = [
        (name, value)
        for name, value in parse_qsl(parts.query, keep_blank_values=True)
        if not name.startswith("utm_") and name not in TRACKING_PARAMS
    ]
    query = f"?{urlencode(kept)}" if kept else ""
    return ParsedVideo(key=f"other:{host}{parts.path.rstrip('/')}{query}")


def parse_video_link(raw: str, platform: str) -> ParsedVideo:
    parts, host = split_link(raw)
    if platform == "tiktok":
        return parse_tiktok(parts, host)
    if platform == "youtube":
        return parse_youtube(parts, host)
    return parse_other(parts, host)
