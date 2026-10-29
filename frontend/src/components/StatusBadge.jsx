import styles from "./StatusBadge.module.css";

const STATUS_LABELS = { review: "Under review", approved: "Approved", rejected: "Rejected", expired: "Expired" };

export default function StatusBadge({ status }) {
  return <span className={`${styles.badge} ${styles[status]}`}>{STATUS_LABELS[status]}</span>;
}
