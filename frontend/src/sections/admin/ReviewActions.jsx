import { useState } from "react";
import Button from "../../components/Button";
import TextField from "../../components/TextField";
import styles from "./ReviewActions.module.css";

// Approve / Reject controls for a card under review. `children` holds the card's own
// approve inputs (for example the received amount); `hint` explains the current input.
// `onApprove()` and `onReject(reason)` return promises; a failure is shown under the buttons.
export default function ReviewActions({ children, canApprove, hint, hintIsError = false, onApprove, onReject }) {
  const [isRejecting, setIsRejecting] = useState(false);
  const [reason, setReason] = useState("");
  const [isBusy, setIsBusy] = useState(false);
  const [error, setError] = useState("");

  async function run(action) {
    setIsBusy(true);
    setError("");
    try {
      await action();
      // On success the list reloads and this card changes or leaves, so it stays busy until then.
    } catch (actionError) {
      setError(actionError.message);
      setIsBusy(false);
    }
  }

  const errorMessage = error && <p className={`${styles.hint} ${styles.error}`}>{error}</p>;

  if (isRejecting) {
    return (
      <div className={styles.actions}>
        <div className={styles.reasonField}>
          <TextField label="Reason (shown to the user)" value={reason} onChange={setReason} placeholder="Does not meet the requirements." />
        </div>
        <Button variant="primary" disabled={isBusy || !reason.trim()} onClick={() => run(() => onReject(reason.trim()))}>
          Confirm reject
        </Button>
        <Button disabled={isBusy} onClick={() => setIsRejecting(false)}>
          Cancel
        </Button>
        {errorMessage}
      </div>
    );
  }

  return (
    <div className={styles.actions}>
      {children}
      <Button variant="primary" disabled={isBusy || !canApprove} onClick={() => run(onApprove)}>
        Approve
      </Button>
      <Button disabled={isBusy} onClick={() => setIsRejecting(true)}>
        Reject
      </Button>
      {hint && <p className={`${styles.hint} ${hintIsError ? styles.error : ""}`}>{hint}</p>}
      {errorMessage}
    </div>
  );
}
