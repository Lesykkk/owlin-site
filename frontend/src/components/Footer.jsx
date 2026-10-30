import { Link } from "react-router-dom";
import SocialLinks from "./SocialLinks";
import styles from "./Footer.module.css";

export default function Footer() {
  return (
    <footer className={`container ${styles.footer}`}>
      <span>Owlin © {new Date().getFullYear()} · Independent community software.</span>
      <div className={styles.links}>
        <Link to="/privacy">Privacy policy</Link>
        <Link to="/terms">Terms of service</Link>
        <SocialLinks />
      </div>
    </footer>
  );
}
