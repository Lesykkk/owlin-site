import { useState } from "react";
import TextField from "../../components/TextField";
import { formatPrice } from "../../lib/format";
import { methodLabel, periodLabel, productName, proofLabel } from "../../lib/labels";
import ReviewActions from "./ReviewActions";
import ReviewCard, { Details } from "./ReviewCard";
import styles from "./OrderCard.module.css";

// `onApprove(receivedCents)` and `onReject(reason)` return promises.
export default function OrderCard({ order, onApprove, onReject }) {
  const [received, setReceived] = useState((order.amountCents / 100).toFixed(2));

  const receivedCents = Math.round(Number(received.replace(",", ".")) * 100);
  const isReceivedValid = Number.isFinite(receivedCents) && receivedCents >= order.amountCents;
  const extraCents = isReceivedValid ? receivedCents - order.amountCents : 0;

  const details = [
    { label: "Plan", value: `${productName(order.product)} · ${periodLabel(order.period)}` },
    { label: "Method", value: methodLabel(order.method, order.coin) },
    { label: "Amount", value: formatPrice(order.amountCents) },
    order.proofText && { label: proofLabel(order.method, order.coin), value: order.proofText },
    order.note && { label: "Note", value: order.note },
  ].filter(Boolean);

  let hint = "Matches the order amount.";
  if (!isReceivedValid) hint = "Less than the order amount: reject it, or enter what was actually received.";
  else if (extraCents > 0) hint = `${formatPrice(extraCents)} extra goes to the user's balance.`;

  return (
    <ReviewCard user={order.user} createdAt={order.createdAt} status={order.status}>
      <Details items={details} />

      {order.screenshots.length === 0 ? (
        <p className={styles.note}>No screenshots.</p>
      ) : (
        <ul className={styles.screenshots}>
          {order.screenshots.map((shot, index) => (
            <li key={shot.url ?? index}>
              {shot.url ? (
                <a href={shot.url} target="_blank" rel="noopener noreferrer" aria-label={`Open screenshot ${index + 1}`}>
                  <img src={shot.url} alt={`Payment screenshot ${index + 1}`} />
                </a>
              ) : (
                <span className={styles.missing}>Link unavailable</span>
              )}
            </li>
          ))}
        </ul>
      )}

      {order.rejectReason && <p className={styles.reason}>Rejected: {order.rejectReason}</p>}
      {order.status === "approved" && order.receivedCents != null && (
        <p className={styles.note}>
          Received {formatPrice(order.receivedCents)}
          {order.balanceAddedCents > 0 && ` · ${formatPrice(order.balanceAddedCents)} added to the user's balance`}
        </p>
      )}

      {order.status === "review" && (
        <ReviewActions
          canApprove={isReceivedValid}
          hint={hint}
          hintIsError={!isReceivedValid}
          onApprove={() => onApprove(receivedCents)}
          onReject={onReject}
        >
          <div className={styles.amountField}>
            <TextField label="Received (€)" value={received} onChange={setReceived} placeholder={(order.amountCents / 100).toFixed(2)} />
          </div>
        </ReviewActions>
      )}
    </ReviewCard>
  );
}
