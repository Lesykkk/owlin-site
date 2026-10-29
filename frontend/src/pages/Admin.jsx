import { useState } from "react";
import PageState from "../components/PageState";
import SegmentedControl from "../components/SegmentedControl";
import { useAdminDecision, useAdminList } from "../hooks/queries";
import { approveClaim, approveOrder, rejectClaim, rejectOrder } from "../lib/api";
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

  // Each section and filter has its own cached list, so switching back is instant.
  const list = useAdminList(section, filter);
  const { mutateAsync: decide } = useAdminDecision();

  return (
    <div className={`container ${styles.page}`}>
      <div className={styles.head}>
        <h1>Review</h1>
        <SegmentedControl label="Section" options={SECTIONS} value={section} onChange={setSection} />
      </div>
      <div className={styles.filters}>
        <SegmentedControl label="Filter by status" options={STATUS_FILTERS} value={filter} onChange={setFilter} />
      </div>

      {list.error ? (
        <PageState error={list.error} onRetry={list.refetch} />
      ) : list.isPending ? (
        <PageState isLoading />
      ) : list.data.length === 0 ? (
        <p className={styles.empty}>Nothing here.</p>
      ) : (
        <div className={styles.list}>
          {section === "payments"
            ? list.data.map((order) => (
                <OrderCard
                  key={order.id}
                  order={order}
                  onApprove={(receivedCents) => decide(() => approveOrder(order.id, receivedCents))}
                  onReject={(reason) => decide(() => rejectOrder(order.id, reason))}
                />
              ))
            : list.data.map((claim) => (
                <VideoCard
                  key={claim.id}
                  video={claim}
                  onApprove={(views) => decide(() => approveClaim(claim.id, views))}
                  onReject={(reason) => decide(() => rejectClaim(claim.id, reason))}
                />
              ))}
        </div>
      )}
    </div>
  );
}
