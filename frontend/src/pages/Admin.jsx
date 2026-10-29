import { useState } from "react";
import SegmentedControl from "../components/SegmentedControl";
import { MOCK_ADMIN_ORDERS, MOCK_ADMIN_VIDEOS } from "../mocks/admin";
import OrderCard from "../sections/admin/OrderCard";
import VideoCard from "../sections/admin/VideoCard";
import styles from "./Admin.module.css";

const STATUS_FILTERS = [
  { id: "review", label: "Under review" },
  { id: "approved", label: "Approved" },
  { id: "rejected", label: "Rejected" },
  { id: "all", label: "All" },
];

const withChanges = (items, id, changes) => items.map((item) => (item.id === id ? { ...item, ...changes } : item));
const countPending = (items) => items.filter((item) => item.status === "review").length;

export default function Admin() {
  // Mock data until the backend provides it; decisions only live in this page's state.
  const [orders, setOrders] = useState(MOCK_ADMIN_ORDERS);
  const [videos, setVideos] = useState(MOCK_ADMIN_VIDEOS);
  const [section, setSection] = useState("payments");
  const [filter, setFilter] = useState("review");

  const sections = [
    { id: "payments", label: `Payments (${countPending(orders)})` },
    { id: "videos", label: `Promo videos (${countPending(videos)})` },
  ];

  const matchesFilter = (item) => filter === "all" || item.status === filter;
  const visibleOrders = section === "payments" ? orders.filter(matchesFilter) : [];
  const visibleVideos = section === "videos" ? videos.filter(matchesFilter) : [];
  const isEmpty = visibleOrders.length + visibleVideos.length === 0;

  return (
    <div className={`container ${styles.page}`}>
      <div className={styles.head}>
        <h1>Review</h1>
        <SegmentedControl label="Section" options={sections} value={section} onChange={setSection} />
      </div>
      <div className={styles.filters}>
        <SegmentedControl label="Filter by status" options={STATUS_FILTERS} value={filter} onChange={setFilter} />
      </div>

      {isEmpty ? (
        <p className={styles.empty}>Nothing here.</p>
      ) : (
        <div className={styles.list}>
          {visibleOrders.map((order) => (
            <OrderCard
              key={order.id}
              order={order}
              onApprove={(id, receivedCents) =>
                setOrders(
                  withChanges(orders, id, {
                    status: "approved",
                    receivedCents,
                    balanceAddedCents: receivedCents - order.amountCents,
                  }),
                )
              }
              onReject={(id, reason) => setOrders(withChanges(orders, id, { status: "rejected", reason }))}
            />
          ))}
          {visibleVideos.map((video) => (
            <VideoCard
              key={video.id}
              video={video}
              onApprove={(id, views) => setVideos(withChanges(videos, id, { status: "approved", views }))}
              onReject={(id, reason) => setVideos(withChanges(videos, id, { status: "rejected", reason }))}
            />
          ))}
        </div>
      )}

      <p className={styles.note}>Demo data: decisions are not saved yet.</p>
    </div>
  );
}
