import Panel from "../../components/Panel";
import SubscriptionCard from "../../components/SubscriptionCard";
import { PRODUCTS } from "../../config/plans";
import { useActivePromotions } from "../../hooks/queries";
import { freeUntilByModule } from "../../lib/freeNow";
import styles from "./Subscriptions.module.css";

// Bundles are a pricing option, not a module: the profile shows the modules themselves.
const MODULES = PRODUCTS.filter((product) => !product.includes);

export default function Subscriptions({ subscriptions }) {
  const { data } = useActivePromotions();
  const freeUntil = freeUntilByModule(data?.promotions);

  return (
    <Panel title="Subscriptions">
      <div className={styles.grid}>
        {MODULES.map((module) => (
          <SubscriptionCard
            key={module.id}
            product={module}
            subscription={subscriptions[module.id]?.active ? subscriptions[module.id] : null}
            freeUntil={freeUntil[module.id]}
          />
        ))}
      </div>
    </Panel>
  );
}
