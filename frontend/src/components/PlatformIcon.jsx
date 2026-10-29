import { LinkIcon, TikTokIcon, YouTubeIcon } from "./Icons";

const ICONS = { tiktok: TikTokIcon, youtube: YouTubeIcon, other: LinkIcon };

export default function PlatformIcon({ platformId, ...props }) {
  const Icon = ICONS[platformId];
  return Icon ? <Icon {...props} /> : null;
}
