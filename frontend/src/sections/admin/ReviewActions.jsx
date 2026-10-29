import { useState } from "react";
import Button from "../../components/Button";
import TextField from "../../components/TextField";
import styles from "./ReviewActions.module.css";

// Approve / Reject controls for a card under review. `children` holds the card's own
// approve inputs (for example the received amount); `hint` explains the current input.
export default function ReviewActions({ children, canApprove, hint, hintIsError = false, onApprove, onReject }) {
  const [isRejecting, setIsRejecting] = useState(false);
  const [reason, setReason] = useState("");

  if (isRejecting) {
    return (
      <div className={styles.actions}>
        <div className={styles.reasonField}>
          <TextField label="Reason (shown to the user)" value={reason} onChange={setReason} placeholder="Does not meet the requirements." />
        </div>
        <Button variant="primary" onClick={() => onReject(reason.trim())}>
          Confirm reject
        </Button>
        <Button onClick={() => setIsRejecting(false)}>Cancel</Button>
      </div>
    );
  }

  return (
    <div className={styles.actions}>
      {children}
      <Button variant="primary" disabled={!canApprove} onClick={onApprove}>
        Approve
      </Button>
      <Button onClick={() => setIsRejecting(true)}>Reject</Button>
      {hint && <p className={`${styles.hint} ${hintIsError ? styles.error : ""}`}>{hint}</p>}
    </div>
  );
}
