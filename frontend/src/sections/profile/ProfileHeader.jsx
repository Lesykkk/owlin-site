import { formatDate, formatPrice } from "../../lib/format";
import styles from "./ProfileHeader.module.css";

export default function ProfileHeader({ user, balanceCents }) {
  return (
    <div className={styles.header}>
      <div className={styles.identity}>
        {user.avatarUrl ? (
          <img className={styles.avatar} src={user.avatarUrl} alt="" width="72" height="72" />
        ) : (
          <span className={styles.avatar} aria-hidden="true" />
        )}
        <div>
          <h1 className={styles.name}>{user.username}</h1>
          <p className={styles.meta}>
            {user.discordId && <span>Discord ID {user.discordId}</span>}
            <span>Member since {formatDate(user.createdAt)}</span>
            {user.lastSeenAt && <span>Last launch {formatDate(user.lastSeenAt)}</span>}
          </p>
        </div>
      </div>

      <div className={styles.balance}>
        <span className={styles.balanceLabel}>Balance</span>
        <span className={styles.balanceValue}>{formatPrice(balanceCents)}</span>
      </div>
    </div>
  );
}
