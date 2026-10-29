import { LINKS } from "../config/links";
import styles from "./Footer.module.css";

export default function Footer() {
  return (
    <footer className={`container ${styles.footer}`}>
      <span>Owlin © {new Date().getFullYear()} · Independent community software.</span>
      <div className={styles.links}>
        <a href="/privacy">Privacy policy</a>
        <a href="/terms">Terms of service</a>
        <a href={LINKS.discord} target="_blank" rel="noopener noreferrer">
          Discord ↗
        </a>
      </div>
    </footer>
  );
}
