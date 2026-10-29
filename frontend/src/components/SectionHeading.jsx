import Eyebrow from "./Eyebrow";
import styles from "./SectionHeading.module.css";

export default function SectionHeading({ eyebrow, title, aside }) {
  return (
    <div className={styles.heading}>
      <div>
        <Eyebrow>{eyebrow}</Eyebrow>
        <h2 className={styles.title}>{title}</h2>
      </div>
      {aside && <p className={styles.aside}>{aside}</p>}
    </div>
  );
}
