import { useCallback, useState } from "react";
import PageState from "../components/PageState";
import SegmentedControl from "../components/SegmentedControl";
import { useRemote } from "../hooks/useRemote";
import {
  approveClaim,
  approveOrder,
  listAdminClaims,
  listAdminOrders,
  rejectClaim,
  rejectOrder,
} from "../lib/api";
import OrderCard from "../sections/admin/OrderCard";
import VideoCard from "../sections/admin/VideoCard";
import styles from "./Admin.module.css";

const SECTIONS = [
  { id: "payments", label: "Payments" },
  { id: "videos", label: "Promo videos" },
];

const STATUS_FILTERS = [
  { id: "review", label: "Under review" },
  { id: "approved", label: "Approved" },
  { id: "rejected", label: "Rejected" },
  { id: "all", label: "All" },
];

export default function Admin() {
  const [section, setSection] = useState("payments");
  const [filter, setFilter] = useState("review");

  // The result remembers what it was loaded for, so a stale list is never drawn with the wrong cards.
  const load = useCallback(async () => {
    const items = section === "payments" ? await listAdminOrders(filter) : await listAdminClaims(filter);
    return { section, filter, items };
  }, [section, filter]);
  const { data, error, reload } = useRemote(load);

  // After a decision the card leaves the queue, so the list is loaded again.
  const decide = (action) => async () => {
    await action();
    await reload();
  };

  const isCurrent = data?.section === section && data?.filter === filter;

  return (
    <div className={`container ${styles.page}`}>
      <div className={styles.head}>
        <h1>Review</h1>
        <SegmentedControl label="Section" options={SECTIONS} value={section} onChange={setSection} />
      </div>
      <div className={styles.filters}>
        <SegmentedControl label="Filter by status" options={STATUS_FILTERS} value={filter} onChange={setFilter} />
      </div>

      {error ? (
        <PageState error={error} onRetry={reload} />
      ) : !isCurrent ? (
        <PageState isLoading />
      ) : data.items.length === 0 ? (
        <p className={styles.empty}>Nothing here.</p>
      ) : (
        <div className={styles.list}>
          {section === "payments"
            ? data.items.map((order) => (
                <OrderCard
                  key={order.id}
                  order={order}
                  onApprove={(receivedCents) => decide(() => approveOrder(order.id, receivedCents))()}
                  onReject={(reason) => decide(() => rejectOrder(order.id, reason))()}
                />
              ))
            : data.items.map((claim) => (
                <VideoCard
                  key={claim.id}
                  video={claim}
                  onApprove={(views) => decide(() => approveClaim(claim.id, views))()}
                  onReject={(reason) => decide(() => rejectClaim(claim.id, reason))()}
                />
              ))}
        </div>
      )}
    </div>
  );
}
