const YOUTUBE_ID = /^[\w-]{11}$/;
const TIKTOK_VIDEO_PATH = /^\/@[^/]+\/video\/(\d+)/;
const TIKTOK_HOSTS = ["tiktok.com", "vm.tiktok.com", "vt.tiktok.com"];
const YOUTUBE_HOSTS = ["youtube.com", "youtu.be"];
const TRACKING_PARAMS = ["fbclid", "gclid", "igshid", "si"];

function parseUrl(raw) {
  const text = raw.trim();
  if (!text) return null;

  try {
    const url = new URL(/^https?:\/\//i.test(text) ? text : `https://${text}`);
    return url.hostname.includes(".") ? url : null;
  } catch {
    return null;
  }
}

function youtubeVideoId(url, host) {
  if (host === "youtu.be") return url.pathname.slice(1).split("/")[0];
  if (url.pathname === "/watch") return url.searchParams.get("v");

  const match = url.pathname.match(/^\/(?:shorts|live|embed)\/([^/]+)/);
  return match ? match[1] : null;
}

function parseTiktok(url, host) {
  const match = url.pathname.match(TIKTOK_VIDEO_PATH);
  if (!TIKTOK_HOSTS.includes(host) || !match) {
    return { error: "Open the video in TikTok and copy its full link (tiktok.com/@name/video/…)." };
  }
  return { videoId: match[1], key: `tiktok:${match[1]}` };
}

function parseYoutube(url, host) {
  const videoId = YOUTUBE_HOSTS.includes(host) ? youtubeVideoId(url, host) : null;
  if (!videoId || !YOUTUBE_ID.test(videoId)) return { error: "Paste the link to a YouTube video." };
  return { videoId, key: `youtube:${videoId}` };
}

// Other sites have no video id, so the cleaned-up address itself is the key.
function parseOther(url, host) {
  if (TIKTOK_HOSTS.includes(host) || YOUTUBE_HOSTS.includes(host)) {
    return { error: "Choose TikTok or YouTube above for this link." };
  }
  const path = url.pathname.replace(/\/+$/, "");
  for (const name of [...url.searchParams.keys()]) {
    if (name.startsWith("utm_") || TRACKING_PARAMS.includes(name)) url.searchParams.delete(name);
  }
  return { key: `other:${host}${path}${url.search}` };
}

// Reduces any link to the same video to one key, so a video cannot be submitted twice
// through different URLs. Returns { key, videoId? } or { error }.
export function parseVideoLink(raw, platformId) {
  const url = parseUrl(raw);
  if (!url) return { error: "Paste a link to your video." };

  const host = url.hostname.replace(/^(www|m)\./, "");

  if (platformId === "tiktok") return parseTiktok(url, host);
  if (platformId === "youtube") return parseYoutube(url, host);
  return parseOther(url, host);
}
