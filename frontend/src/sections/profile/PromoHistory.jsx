import { Link } from "react-router-dom";
import Panel from "../../components/Panel";
import PlatformIcon from "../../components/PlatformIcon";
import StatusBadge from "../../components/StatusBadge";
import { PROMO_DAYS, PROMO_PLATFORMS, PROMO_REWARDS } from "../../config/promo";
import { daysLeft, formatDateTime } from "../../lib/format";
import styles from "./HistoryTable.module.css";

// An approved claim whose free days have run out reads as "expired".
function displayStatus(claim) {
  return claim.status === "approved" && new Date(claim.expiresAt) <= Date.now() ? "expired" : claim.status;
}

export default function PromoHistory({ claims, slots }) {
  const slotsLabel = `${slots.used} of ${slots.max} slots in use`;

  return (
    <Panel title="Promo videos" action={<span className={styles.slots}>{slotsLabel}</span>}>
      {claims.length === 0 ? (
        <p className={styles.empty}>
          No videos yet. <Link to="/promo">Make a video and get {PROMO_DAYS} days free.</Link>
        </p>
      ) : (
        <div className={styles.scroll}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Submitted</th>
                <th>Video</th>
                <th>Reward</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {claims.map((claim) => {
                const platform = PROMO_PLATFORMS.find((item) => item.id === claim.platform);
                const reward = PROMO_REWARDS.find((item) => item.id === claim.rewardProduct);
                const status = displayStatus(claim);

                return (
                  <tr key={claim.id}>
                    <td className={styles.date}>{formatDateTime(claim.createdAt)}</td>
                    <td>
                      <a href={claim.url} target="_blank" rel="noopener noreferrer" className={styles.video}>
                        <PlatformIcon platformId={claim.platform} />
                        {platform?.label ?? claim.platform}
                      </a>
                    </td>
                    <td>
                      {reward?.label ?? claim.rewardProduct} · {PROMO_DAYS} days
                    </td>
                    <td>
                      <StatusBadge status={status} />
                      {status === "approved" && (
                        <span className={styles.reason}>{daysLeft(claim.expiresAt)} days left</span>
                      )}
                      {claim.rejectReason && <span className={styles.reason}>{claim.rejectReason}</span>}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </Panel>
  );
}
