import Panel from "../../components/Panel";
import styles from "./OrderSummary.module.css";

export default function OrderSummary({ productName, periodLabel, totalLabel, features }) {
  return (
    <Panel title="Order summary" className={styles.summary}>
      <p className={styles.product}>{productName}</p>
      {periodLabel && <p className={styles.period}>{periodLabel}</p>}

      <ul className={styles.features}>
        {features.map((feature) => (
          <li key={feature}>{feature}</li>
        ))}
      </ul>

      <div className={styles.total}>
        <span>To pay</span>
        <strong>{totalLabel}</strong>
      </div>
    </Panel>
  );
}
