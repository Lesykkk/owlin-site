import Button from "../../components/Button";
import Eyebrow from "../../components/Eyebrow";
import styles from "./Submitted.module.css";

export default function Submitted({ children }) {
  return (
    <section className={`container ${styles.done}`}>
      <Eyebrow className={styles.eyebrow}>Under review</Eyebrow>
      <h1 className={styles.title}>Thanks, we got it.</h1>
      <p className={styles.text}>{children}</p>
      <Button href="/profile" variant="primary">
        Go to profile
      </Button>
    </section>
  );
}
