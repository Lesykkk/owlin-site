import { MOCK_PROFILE } from "../mocks/profile";
import { useAuth } from "../hooks/useAuth";
import Orders from "../sections/profile/Orders";
import PromoHistory from "../sections/profile/PromoHistory";
import ProfileHeader from "../sections/profile/ProfileHeader";
import Stats from "../sections/profile/Stats";
import Subscriptions from "../sections/profile/Subscriptions";
import styles from "./Profile.module.css";

export default function Profile() {
  const { user } = useAuth();
  // Mock data until the backend provides subscriptions, stats and orders.
  const profile = MOCK_PROFILE;

  return (
    <div className={`container ${styles.page}`}>
      <ProfileHeader user={user} balanceCents={profile.balanceCents} />
      <Subscriptions subscriptions={profile.subscriptions} />
      <Stats stats={profile.stats} />
      <Orders orders={profile.orders} />
      <PromoHistory claims={profile.promoClaims} />
      <p className={styles.note}>Demo data: real subscriptions, stats, orders and promo videos will appear here once payments go live.</p>
    </div>
  );
}
