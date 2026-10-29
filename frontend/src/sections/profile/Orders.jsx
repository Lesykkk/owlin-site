import Panel from "../../components/Panel";
import StatusBadge from "../../components/StatusBadge";
import { formatDateTime, formatPrice } from "../../lib/format";
import styles from "./HistoryTable.module.css";

export default function Orders({ orders }) {
  return (
    <Panel title="Orders">
      <div className={styles.scroll}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Submitted</th>
              <th>Plan</th>
              <th>Method</th>
              <th>Amount</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((order) => (
              <tr key={order.id}>
                <td className={styles.date}>{formatDateTime(order.createdAt)}</td>
                <td>
                  {order.product} · {order.period}
                </td>
                <td>{order.method}</td>
                <td>{formatPrice(order.amountCents)}</td>
                <td>
                  <StatusBadge status={order.status} />
                  {order.reason && <span className={styles.reason}>{order.reason}</span>}
                  {order.balanceAddedCents > 0 && (
                    <span className={styles.reason}>+{formatPrice(order.balanceAddedCents)} added to balance</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}
