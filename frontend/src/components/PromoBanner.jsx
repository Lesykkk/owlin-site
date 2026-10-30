import { PROMO_DAYS, PROMO_PLATFORMS } from "../config/promo";
import Button from "./Button";
import Eyebrow from "./Eyebrow";
import PlatformIcon from "./PlatformIcon";
import styles from "./PromoBanner.module.css";

// Invitation to the video promo. Used on the home and pricing pages.
export default function PromoBanner({ className = "" }) {
  return (
    <section className={`container ${styles.section} ${className}`}>
      <div className={styles.banner}>
        <div className={styles.copy}>
          <Eyebrow className={styles.tag}>Free</Eyebrow>
          <h2 className={styles.title}>Make a video, get <span className={styles.free}>{PROMO_DAYS} days</span> free.</h2>
          <p className={styles.text}>
            Post a video about Owlin on TikTok, YouTube or elsewhere and get {PROMO_DAYS} days of Spoofer or DLC Unlock.
          </p>
          <ul className={styles.platforms}>
            {PROMO_PLATFORMS.map((platform) => (
              <li key={platform.id}>
                <PlatformIcon platformId={platform.id} />
                {platform.label}
              </li>
            ))}
          </ul>
        </div>
        <Button href="/promo" variant="primary" className={styles.action}>
          Get free days
        </Button>
      </div>
    </section>
  );
}
