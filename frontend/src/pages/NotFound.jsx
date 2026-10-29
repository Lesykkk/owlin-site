import Button from "../components/Button";
import Eyebrow from "../components/Eyebrow";
import styles from "./NotFound.module.css";

export default function NotFound() {
  return (
    <section className={`container ${styles.page}`}>
      <Eyebrow className={styles.eyebrow}>404</Eyebrow>
      <h1 className={styles.title}>Wrong turn.</h1>
      <p className={styles.text}>This page doesn’t exist. Let’s get you back on the road.</p>
      <Button href="/" variant="primary">
        Back to home
      </Button>
    </section>
  );
}
