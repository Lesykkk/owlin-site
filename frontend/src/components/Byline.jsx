import { LINKS } from "../config/links";
import authorAvatar from "../assets/pedro.webp";
import styles from "./Byline.module.css";

export default function Byline() {
  return (
    <a href={LINKS.author} className={styles.byline} target="_blank" rel="noopener noreferrer">
      <span>by Pedro</span>
      <img src={authorAvatar} alt="Pedro" width="44" height="44" />
    </a>
  );
}
