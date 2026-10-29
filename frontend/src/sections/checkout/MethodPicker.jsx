import MethodIcon from "../../components/MethodIcon";
import SegmentedControl from "../../components/SegmentedControl";
import styles from "./MethodPicker.module.css";

// Step 1: pick PayPal, Crypto or Steam Gift Card; crypto asks for the coin right below.
export default function MethodPicker({ methods, methodId, onMethodChange, coinId, onCoinChange }) {
  const method = methods.find((item) => item.id === methodId);

  return (
    <>
      <div className={styles.grid} role="radiogroup" aria-label="Payment method">
        {methods.map((item) => {
          const isActive = item.id === methodId;
          return (
            <button
              key={item.id}
              type="button"
              role="radio"
              aria-checked={isActive}
              className={`${styles.option} ${isActive ? styles.active : ""}`}
              onClick={() => onMethodChange(item.id)}
            >
              <MethodIcon methodId={item.id} className={styles.icon} />
              <span className={styles.label}>{item.label}</span>
              <span className={styles.summary}>{item.summary}</span>
            </button>
          );
        })}
      </div>

      {method.coins && (
        <div className={styles.coins}>
          <p>Choose a coin and network</p>
          <SegmentedControl label="Coin" options={method.coins} value={coinId} onChange={onCoinChange} />
        </div>
      )}
    </>
  );
}
