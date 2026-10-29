import CopyButton from "../../components/CopyButton";
import { paymentRows } from "../../lib/payments";
import styles from "./PaymentDetails.module.css";

export default function PaymentDetails({ option, priceCents }) {
  return (
    <>
      <p className={styles.hint}>{option.hint}</p>
      <dl className={styles.rows}>
        {paymentRows(option, priceCents).map((row) => {
          const copyValue = "copyValue" in row ? row.copyValue : row.value;
          return (
            <div key={row.label} className={styles.row}>
              <dt>{row.label}</dt>
              <dd>
                {row.href ? (
                  <a href={row.href} target="_blank" rel="noopener noreferrer">
                    {row.value}
                  </a>
                ) : (
                  <span>{row.value}</span>
                )}
                {copyValue && <CopyButton value={copyValue} />}
              </dd>
            </div>
          );
        })}
      </dl>
    </>
  );
}
