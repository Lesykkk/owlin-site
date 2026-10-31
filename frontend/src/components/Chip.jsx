import styles from "./Chip.module.css";

// A rounded label with an icon, used for payment methods and promo platforms.
export function ChipList({ className = "", children }) {
  return <ul className={`${styles.list} ${className}`}>{children}</ul>;
}

export function Chip({ children }) {
  return <li className={styles.chip}>{children}</li>;
}
