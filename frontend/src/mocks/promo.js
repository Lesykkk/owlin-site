// Demo stand-in for the backend: keys of videos that already earned a reward.
const USED_VIDEO_KEYS = new Set(["youtube:dKiSnET6eNs", "tiktok:7301234567890123456", "other:example.com/clip"]);

// TODO: replace with an API call; the backend must also enforce a UNIQUE (platform, video_id) constraint,
// the slot limit and the video age (TikTok ids carry their creation time), since the page cannot be trusted.
export async function isVideoUsed(key) {
  await new Promise((resolve) => setTimeout(resolve, 400));
  return USED_VIDEO_KEYS.has(key);
}
