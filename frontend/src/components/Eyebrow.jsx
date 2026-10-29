import styles from "./Eyebrow.module.css";

export default function Eyebrow({ withDot = false, className = "", children }) {
  return (
    <div className={`${styles.eyebrow} ${className}`}>
      {withDot && <span className={styles.dot} aria-hidden="true" />}
      {children}
    </div>
  );
}
