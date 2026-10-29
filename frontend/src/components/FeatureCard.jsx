import styles from "./FeatureCard.module.css";

const TIER_LABELS = { free: "Free", premium: "Premium" };

export default function FeatureCard({ label, tier, title, description }) {
  return (
    <article className={`${styles.card} ${styles[tier]}`}>
      <div className={styles.top}>
        <span className={styles.label}>{label}</span>
        <span className={styles.badge}>{TIER_LABELS[tier]}</span>
      </div>
      <h3 className={styles.title}>{title}</h3>
      <p className={styles.description}>{description}</p>
    </article>
  );
}
