import { useState } from "react";
import { PlayIcon } from "../components/Icons";
import SectionTitle from "../components/SectionTitle";
import { DEMO_VIDEO_ID, LINKS } from "../config/links";
import styles from "./Showcase.module.css";

const thumbnailUrl = (quality) => `https://i.ytimg.com/vi/${DEMO_VIDEO_ID}/${quality}.jpg`;

// Not every video has a maxres thumbnail; hqdefault always exists.
function fallbackToHqThumbnail(event) {
  event.currentTarget.onerror = null;
  event.currentTarget.src = thumbnailUrl("hqdefault");
}

export default function Showcase() {
  const [isPlaying, setIsPlaying] = useState(false);

  return (
    <section id="showcase" className={`container ${styles.section}`}>
      <div className={styles.copy}>
        <SectionTitle eyebrow="A closer look">
          See what’s
          <br />
          behind the wheel.
        </SectionTitle>
        <p className={styles.text}>A look inside Owlin: the interface, the tools and the details that make it yours.</p>
        <a className={styles.link} href={LINKS.discord} target="_blank" rel="noopener noreferrer">
          Get the latest from our Discord ↗
        </a>
      </div>

      <div className={styles.video}>
        {isPlaying ? (
          <iframe
            src={`https://www.youtube-nocookie.com/embed/${DEMO_VIDEO_ID}?autoplay=1`}
            title="Owlin demo"
            allow="autoplay; encrypted-media; picture-in-picture"
            allowFullScreen
          />
        ) : (
          <VideoPreview canPlay={Boolean(DEMO_VIDEO_ID)} onPlay={() => setIsPlaying(true)} />
        )}
      </div>
    </section>
  );
}

// Static YouTube thumbnail first: the player itself loads only after a click.
function VideoPreview({ canPlay, onPlay }) {
  return (
    <>
      {canPlay && (
        <img
          className={styles.poster}
          src={thumbnailUrl("maxresdefault")}
          onError={fallbackToHqThumbnail}
          alt=""
          loading="lazy"
        />
      )}
      <div className={styles.center}>
        <button
          type="button"
          className={styles.play}
          onClick={onPlay}
          disabled={!canPlay}
          aria-label="Play the Owlin demo video"
        >
          <PlayIcon />
        </button>
        <span>Owlin in action</span>
      </div>
      {!canPlay && <span className={styles.note}>YouTube demo · coming to this space</span>}
    </>
  );
}
