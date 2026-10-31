import Eyebrow from "./Eyebrow";
import styles from "./SectionTitle.module.css";

// The eyebrow and the big title of a section. Used on its own and inside SectionHeading.
export default function SectionTitle({ eyebrow, children }) {
  return (
    <>
      <Eyebrow>{eyebrow}</Eyebrow>
      <h2 className={styles.title}>{children}</h2>
    </>
  );
}
