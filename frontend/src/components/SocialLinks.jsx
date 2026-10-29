import { LINKS } from "../config/links";
import { DiscordIcon, TikTokIcon, YouTubeIcon } from "./Icons";
import styles from "./SocialLinks.module.css";

const SOCIALS = [
  { id: "tiktok", label: "TikTok", Icon: TikTokIcon },
  { id: "youtube", label: "YouTube", Icon: YouTubeIcon },
  { id: "discord", label: "Discord", Icon: DiscordIcon },
];

// A row of social icons. Networks without a link in config/links.js are left out.
export default function SocialLinks() {
  return (
    <div className={styles.row}>
      {SOCIALS.filter(({ id }) => LINKS[id]).map(({ id, label, Icon }) => (
        <a key={id} href={LINKS[id]} target="_blank" rel="noopener noreferrer" aria-label={label} title={label}>
          <Icon />
        </a>
      ))}
    </div>
  );
}
