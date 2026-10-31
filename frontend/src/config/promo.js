import { LINKS } from "./links";

export const PROMO_DAYS = 14;
// Pending and active claims share this limit; expired and rejected ones do not count.
export const MAX_PROMO_SLOTS = 4;

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

// A sample video shown next to the submission form.
export const EXAMPLE_VIDEO = {
  platformId: "tiktok",
  embedUrl: "https://www.tiktok.com/player/v1/7695863549985312021?music_info=0&description=0&rel=0&native_context_menu=0",
  url: "https://www.tiktok.com/@pedrokapucci/video/7695863549985312021",
  author: "@pedrokapucci",
};

// The Discord invite and the site address a promo video must link to; shown as links inside the rules.
export const PROMO_LINK_TARGETS = [LINKS.discord, "owlin.software"];

// "5,000 views on TikTok or 1,000 on YouTube", taken from the platform list so the two never disagree.
const viewsRule = () => {
  const [tiktok, youtube] = ["tiktok", "youtube"].map((id) => PROMO_PLATFORMS.find((platform) => platform.id === id));
  return `The video has at least ${tiktok.minViews.toLocaleString("en-US")} views on TikTok or ${youtube.minViews.toLocaleString("en-US")} on YouTube. Videos on other sites are checked manually.`;
};

export const PROMO_RULES = [
  "Owlin is mentioned or shown in the video, so that viewers clearly notice it.",
  `The video also links to our Discord server (${LINKS.discord}) or to owlin.software.`,
  "The video does not advertise competitors' products together with Owlin.",
  viewsRule(),
  `One video gives ${PROMO_DAYS} days of Spoofer or DLC Unlock.`,
  `You can have up to ${MAX_PROMO_SLOTS} pending and active promo videos at a time. Expired and rejected ones do not count.`,
];
