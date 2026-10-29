import styles from "./Spinner.module.css";

// A small ring that turns while something loads. `size` is in pixels. It takes the
// text color around it for the ring's base, so it works on buttons and on plain pages.
export default function Spinner({ size = 18, className = "" }) {
  return <span className={`${styles.spinner} ${className}`} style={{ width: size, height: size }} aria-hidden="true" />;
}
