import StatusBadge from "../../components/StatusBadge";
import { formatDateTime } from "../../lib/format";
import styles from "./ReviewCard.module.css";

// Shared frame of an admin card: who submitted it, when, its status, then the card's own content.
export default function ReviewCard({ user, createdAt, status, children }) {
  return (
    <article className={styles.card}>
      <header className={styles.header}>
        <div>
          <h3 className={styles.user}>{user.username}</h3>
          <p className={styles.meta}>
            Discord {user.discordId} · {formatDateTime(createdAt)}
          </p>
        </div>
        <StatusBadge status={status} />
      </header>
      {children}
    </article>
  );
}

// `items` is a list of { label, value } where value is text or an element.
export function Details({ items }) {
  return (
    <dl className={styles.details}>
      {items.map((item) => (
        <div key={item.label}>
          <dt>{item.label}</dt>
          <dd>{item.value}</dd>
        </div>
      ))}
    </dl>
  );
}
