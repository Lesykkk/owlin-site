import { useEffect, useRef } from "react";
import Button from "../components/Button";
import Byline from "../components/Byline";
import Eyebrow from "../components/Eyebrow";
import { DownloadIcon, PlayIcon } from "../components/Icons";
import SocialLinks from "../components/SocialLinks";
import { GAMES } from "../config/features";
import { LINKS } from "../config/links";
import loaderWelcome from "../assets/loader-welcome.webp";
import styles from "./Hero.module.css";

// The window starts slightly turned; following the pointer shifts it by up to this many degrees.
const TILT_Y = 5;
const TILT_X = 4;

// Turns the loader window towards the pointer. Skipped for touch screens and reduced motion.
function useFollowPointer(ref) {
  useEffect(() => {
    const canHover = window.matchMedia("(hover: hover) and (prefers-reduced-motion: no-preference)");
    const element = ref.current;
    if (!canHover.matches || !element) return undefined;

    const onMove = (event) => {
      const rect = element.getBoundingClientRect();
      const x = (event.clientX - (rect.left + rect.width / 2)) / (window.innerWidth / 2);
      const y = (event.clientY - (rect.top + rect.height / 2)) / (window.innerHeight / 2);
      const clamp = (value) => Math.max(-1, Math.min(1, value));
      element.style.setProperty("--tilt-y", `${-7 + clamp(x) * TILT_Y}deg`);
      element.style.setProperty("--tilt-x", `${3 - clamp(y) * TILT_X}deg`);
    };
    const onLeave = () => {
      element.style.removeProperty("--tilt-y");
      element.style.removeProperty("--tilt-x");
    };

    window.addEventListener("mousemove", onMove);
    document.documentElement.addEventListener("mouseleave", onLeave);
    return () => {
      window.removeEventListener("mousemove", onMove);
      document.documentElement.removeEventListener("mouseleave", onLeave);
    };
  }, [ref]);
}

export default function Hero() {
  const windowRef = useRef(null);
  useFollowPointer(windowRef);

  return (
    <section className={`container ${styles.hero}`}>
      <div className={styles.grid}>
        <div>
          <Eyebrow withDot>Made for ETS2 &amp; ATS</Eyebrow>
          <h1 className={styles.title}>
            <span className={styles.lead}>Drive with</span>
            <br />
            <span className={styles.brand}>
              <span className={styles.accent}>Owlin</span> Mod Menu
            </span>
          </h1>
          <p className={styles.intro}>
            Your roads. Your rules. The Owlin mod menu brings more possibilities to every drive in Euro Truck
            Simulator 2 and American Truck Simulator.
          </p>
          <div className={styles.actions}>
            <Button href={LINKS.download} variant="primary" external>
              <DownloadIcon />
              Download Owlin
            </Button>
            <Button href="#showcase">
              <PlayIcon />
              Watch the demo
            </Button>
            <Byline />
          </div>
          <p className={styles.fine}>Free features included. Premium when you want more.</p>
          <div className={styles.social}>
            <SocialLinks />
          </div>
        </div>

        <div className={styles.art}>
          <div ref={windowRef} className={styles.window}>
            <img
              src={loaderWelcome}
              alt="Owlin loader start screen"
              width="1440"
              height="900"
              fetchPriority="high"
            />
          </div>
          <p className={styles.caption}>A familiar interface. More possibilities.</p>
        </div>
      </div>

      <div className={styles.games}>
        <span className={styles.gamesLabel}>Two games. One Owlin.</span>
        {GAMES.map((game) => (
          <span key={game}>{game}</span>
        ))}
      </div>
    </section>
  );
}
