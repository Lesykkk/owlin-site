import { daysLeft, formatDate } from "../lib/format";
import Button from "./Button";
import styles from "./SubscriptionCard.module.css";

// Share of the current stretch of access that is still left. Unknown without a start date.
function remainingShare(subscription) {
  if (!subscription.startedAt) return null;

  const total = new Date(subscription.expiresAt) - new Date(subscription.startedAt);
  const left = new Date(subscription.expiresAt) - Date.now();
  return Math.min(100, Math.max(0, (left / total) * 100));
}

export default function SubscriptionCard({ product, subscription, freeUntil }) {
  const isActive = Boolean(subscription);
  const share = isActive && !subscription.lifetime ? remainingShare(subscription) : null;

  return (
    <div className={styles.card}>
      <div className={styles.top}>
        <span className={styles.name}>{product.name}</span>
        <span className={`${styles.status} ${isActive || freeUntil ? styles.active : ""}`}>
          {isActive ? "Active" : freeUntil ? "Free now" : "Not active"}
        </span>
      </div>

      {isActive ? (
        <>
          <p className={styles.expires}>
            {subscription.lifetime
              ? "Lifetime access"
              : `Expires ${formatDate(subscription.expiresAt)} · ${daysLeft(subscription.expiresAt)} days left`}
          </p>
          {share !== null && (
            <div className={styles.bar} role="presentation">
              <div className={styles.fill} style={{ width: `${share}%` }} />
            </div>
          )}
          {!subscription.lifetime && (
            <Button href="/pricing" size="sm" className={styles.action}>
              Extend
            </Button>
          )}
        </>
      ) : (
        <>
          <p className={styles.expires}>
            {freeUntil
              ? `Free for everyone until ${formatDate(freeUntil)}.`
              : `Get ${product.name} to unlock it in the menu.`}
          </p>
          {!freeUntil && (
            <Button href="/pricing" variant="primary" size="sm" className={styles.action}>
              Get {product.name}
            </Button>
          )}
        </>
      )}
    </div>
  );
}
