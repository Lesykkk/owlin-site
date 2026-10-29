import Button from "./Button";
import Eyebrow from "./Eyebrow";
import { DiscordIcon } from "./Icons";
import styles from "./LoginPrompt.module.css";

export default function LoginPrompt({ onLogin }) {
  return (
    <section className={`container ${styles.prompt}`}>
      <Eyebrow className={styles.eyebrow}>Members only</Eyebrow>
      <h1 className={styles.title}>Sign in to continue.</h1>
      <p className={styles.text}>Log in with Discord to see your subscriptions, orders and stats.</p>
      <Button variant="primary" onClick={onLogin}>
        <DiscordIcon />
        Login with Discord
      </Button>
    </section>
  );
}
