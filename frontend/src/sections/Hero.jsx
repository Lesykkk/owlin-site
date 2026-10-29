import Button from "../components/Button";
import Byline from "../components/Byline";
import Eyebrow from "../components/Eyebrow";
import { DownloadIcon, PlayIcon } from "../components/Icons";
import { GAMES } from "../config/features";
import { LINKS } from "../config/links";
import loaderWelcome from "../assets/loader-welcome.webp";
import styles from "./Hero.module.css";

export default function Hero() {
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
        </div>

        <div className={styles.art}>
          <div className={styles.window}>
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
