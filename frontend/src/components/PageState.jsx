import Button from "./Button";
import Spinner from "./Spinner";
import styles from "./PageState.module.css";

// Shown instead of a page's content while it loads, or when loading it failed.
export default function PageState({ isLoading, error, onRetry }) {
  if (isLoading) {
    return (
      <div className={`container ${styles.state} ${styles.loading}`} role="status" aria-live="polite">
        <Spinner size={34} />
        <p>Loading…</p>
      </div>
    );
  }

  return (
    <div className={`container ${styles.state} ${styles.failed}`} role="alert">
      <p>{error?.message ?? "Something went wrong."}</p>
      {onRetry && <Button onClick={onRetry}>Try again</Button>}
    </div>
  );
}
