import PageState from "../components/PageState";
import { useMe, useMyOrders, useMyPromo } from "../hooks/queries";
import Orders from "../sections/profile/Orders";
import ProfileHeader from "../sections/profile/ProfileHeader";
import PromoHistory from "../sections/profile/PromoHistory";
import Subscriptions from "../sections/profile/Subscriptions";
import styles from "./Profile.module.css";

export default function Profile() {
  // Usually already in the cache, so the page opens at once and refreshes quietly behind it.
  const queries = [useMe(), useMyOrders(), useMyPromo()];
  const [me, orders, promo] = queries;

  // A failed background refresh must not hide data that is already on screen.
  const error = queries.find((query) => query.error && query.data === undefined)?.error;
  if (error || queries.some((query) => query.isPending)) {
    return <PageState isLoading={!error} error={error} onRetry={() => queries.forEach((query) => query.refetch())} />;
  }

  return (
    <div className={`container ${styles.page}`}>
      <ProfileHeader user={me.data} balanceCents={me.data.balanceCents} />
      <Subscriptions subscriptions={me.data.subscriptions} />
      <Orders orders={orders.data} />
      <PromoHistory claims={promo.data.claims} slots={promo.data.slots} />
    </div>
  );
}
