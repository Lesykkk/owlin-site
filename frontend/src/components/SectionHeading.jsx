import SectionTitle from "./SectionTitle";
import styles from "./SectionHeading.module.css";

export default function SectionHeading({ eyebrow, title, aside }) {
  return (
    <div className={styles.heading}>
      <div>
        <SectionTitle eyebrow={eyebrow}>{title}</SectionTitle>
      </div>
      {aside && <p className={styles.aside}>{aside}</p>}
    </div>
  );
}
