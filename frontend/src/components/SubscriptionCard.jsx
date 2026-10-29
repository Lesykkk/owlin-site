import { daysLeft, formatDate } from "../lib/format";
import Button from "./Button";
import styles from "./SubscriptionCard.module.css";

function remainingShare(subscription) {
  const total = new Date(subscription.expiresAt) - new Date(subscription.startedAt);
  const left = new Date(subscription.expiresAt) - Date.now();
  return Math.min(100, Math.max(0, (left / total) * 100));
}

export default function SubscriptionCard({ product, subscription }) {
  const isActive = Boolean(subscription);

  return (
    <div className={styles.card}>
      <div className={styles.top}>
        <span className={styles.name}>{product.name}</span>
        <span className={`${styles.status} ${isActive ? styles.active : ""}`}>{isActive ? "Active" : "Not active"}</span>
      </div>

      {isActive ? (
        <>
          <p className={styles.expires}>
            Expires {formatDate(subscription.expiresAt)} · {daysLeft(subscription.expiresAt)} days left
          </p>
          <div className={styles.bar} role="presentation">
            <div className={styles.fill} style={{ width: `${remainingShare(subscription)}%` }} />
          </div>
          <Button href="/pricing" size="sm" className={styles.action}>
            Extend
          </Button>
        </>
      ) : (
        <>
          <p className={styles.expires}>Get {product.name} to unlock it in the menu.</p>
          <Button href="/pricing" variant="primary" size="sm" className={styles.action}>
            Get {product.name}
          </Button>
        </>
      )}
    </div>
  );
}
