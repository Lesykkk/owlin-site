import PageState from "../components/PageState";
import { useRemote } from "../hooks/useRemote";
import { getMe, getMyOrders, getMyPromo } from "../lib/api";
import Orders from "../sections/profile/Orders";
import ProfileHeader from "../sections/profile/ProfileHeader";
import PromoHistory from "../sections/profile/PromoHistory";
import Subscriptions from "../sections/profile/Subscriptions";
import styles from "./Profile.module.css";

const loadProfile = async () => {
  const [me, orders, promo] = await Promise.all([getMe(), getMyOrders(), getMyPromo()]);
  return { me, orders, promo };
};

export default function Profile() {
  const { data, error, isLoading, reload } = useRemote(loadProfile);

  if (isLoading || error) return <PageState isLoading={isLoading} error={error} onRetry={reload} />;

  const { me, orders, promo } = data;
  return (
    <div className={`container ${styles.page}`}>
      <ProfileHeader user={me} balanceCents={me.balanceCents} />
      <Subscriptions subscriptions={me.subscriptions} />
      <Orders orders={orders} />
      <PromoHistory claims={promo.claims} slots={promo.slots} />
    </div>
  );
}
