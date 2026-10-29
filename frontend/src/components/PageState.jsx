import Button from "./Button";
import styles from "./PageState.module.css";

// Shown instead of a page's content while it loads, or when loading it failed.
export default function PageState({ isLoading, error, onRetry }) {
  if (isLoading) {
    return (
      <p className={`container ${styles.state}`} role="status">
        Loading…
      </p>
    );
  }

  return (
    <div className={`container ${styles.state}`} role="alert">
      <p>{error?.message ?? "Something went wrong."}</p>
      {onRetry && <Button onClick={onRetry}>Try again</Button>}
    </div>
  );
}
