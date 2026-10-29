import { useState } from "react";
import TextField from "../../components/TextField";
import { formatPrice } from "../../lib/format";
import ReviewActions from "./ReviewActions";
import ReviewCard, { Details } from "./ReviewCard";
import styles from "./OrderCard.module.css";

export default function OrderCard({ order, onApprove, onReject }) {
  const [received, setReceived] = useState((order.amountCents / 100).toFixed(2));

  const receivedCents = Math.round(Number(received.replace(",", ".")) * 100);
  const isReceivedValid = Number.isFinite(receivedCents) && receivedCents >= order.amountCents;
  const extraCents = isReceivedValid ? receivedCents - order.amountCents : 0;

  const details = [
    { label: "Plan", value: `${order.product} · ${order.period}` },
    { label: "Method", value: order.method },
    { label: "Amount", value: formatPrice(order.amountCents) },
    order.proof && { label: order.proof.label, value: order.proof.value },
  ].filter(Boolean);

  let hint = "Matches the order amount.";
  if (!isReceivedValid) hint = "Less than the order amount: reject it, or enter what was actually received.";
  else if (extraCents > 0) hint = `${formatPrice(extraCents)} extra goes to the user's balance.`;

  return (
    <ReviewCard user={order.user} createdAt={order.createdAt} status={order.status}>
      <Details items={details} />

      <ul className={styles.screenshots}>
        {order.screenshots.map((url, index) => (
          <li key={`${url}-${index}`}>
            <a href={url} target="_blank" rel="noopener noreferrer" aria-label={`Open screenshot ${index + 1}`}>
              <img src={url} alt={`Payment screenshot ${index + 1}`} />
            </a>
          </li>
        ))}
      </ul>

      {order.reason && <p className={styles.reason}>Rejected: {order.reason}</p>}
      {order.status === "approved" && order.receivedCents !== undefined && (
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
          onApprove={() => onApprove(order.id, receivedCents)}
          onReject={(reason) => onReject(order.id, reason)}
        >
          <div className={styles.amountField}>
            <TextField label="Received (€)" value={received} onChange={setReceived} placeholder={(order.amountCents / 100).toFixed(2)} />
          </div>
        </ReviewActions>
      )}
    </ReviewCard>
  );
}
