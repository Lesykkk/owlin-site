import { LINKS } from "./links";

export const PROMO_DAYS = 7;
export const MAX_VIDEO_AGE_DAYS = 14;
// Pending and active claims share this limit; expired and rejected ones do not count.
export const MAX_PROMO_SLOTS = 8;

// `minViews: null` means there is no fixed number and the video is reviewed manually.
export const PROMO_PLATFORMS = [
  { id: "tiktok", label: "TikTok", minViews: 5000, placeholder: "https://www.tiktok.com/@name/video/…" },
  { id: "youtube", label: "YouTube", minViews: 1000, placeholder: "https://www.youtube.com/watch?v=…" },
  { id: "other", label: "Other", minViews: null, placeholder: "https://" },
];

export const PROMO_REWARDS = [
  { id: "spoofer", label: "Spoofer" },
  { id: "dlc-unlock", label: "DLC Unlock" },
];

export const PROMO_RULES = [
  "Owlin is mentioned or shown in the video, so that viewers clearly notice it.",
  `The video also links to our Discord server (${LINKS.discord}) or to owlin.software.`,
  "The video does not advertise competitors' products together with Owlin.",
  `The video is not older than ${MAX_VIDEO_AGE_DAYS} days when you submit it.`,
  `One video gives ${PROMO_DAYS} days of Spoofer or DLC Unlock.`,
  `You can have up to ${MAX_PROMO_SLOTS} pending and active promo videos at a time. Expired and rejected ones do not count.`,
];
