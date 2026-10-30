import { EXAMPLE_VIDEO } from "../config/promo";
import PlatformIcon from "./PlatformIcon";
import styles from "./ExampleVideo.module.css";

// A sample promo video next to the submission form, so people see what a good one looks like.
export default function ExampleVideo() {
  return (
    <aside className={styles.example}>
      <iframe
        className={styles.frame}
        src={EXAMPLE_VIDEO.embedUrl}
        title={`Example promo video by ${EXAMPLE_VIDEO.author}`}
        loading="lazy"
        allow="encrypted-media; fullscreen"
        allowFullScreen
      />
      <a className={styles.author} href={EXAMPLE_VIDEO.url} target="_blank" rel="noopener noreferrer">
        <PlatformIcon platformId={EXAMPLE_VIDEO.platformId} />
        Example · {EXAMPLE_VIDEO.author} ↗
      </a>
    </aside>
  );
}
