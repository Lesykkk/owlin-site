import Button from "../components/Button";
import Eyebrow from "../components/Eyebrow";
import { DownloadIcon } from "../components/Icons";
import { LINKS } from "../config/links";
import styles from "./BottomCta.module.css";

export default function BottomCta() {
  return (
    <section className={`container ${styles.section}`}>
      <Eyebrow className={styles.eyebrow}>The road is yours</Eyebrow>
      <h2 className={styles.title}>Make your next drive an Owlin drive.</h2>
      <p className={styles.text}>Download the loader and find your own way to play.</p>
      <Button href={LINKS.download} variant="primary" external>
        <DownloadIcon />
        Download Owlin
      </Button>
    </section>
  );
}
