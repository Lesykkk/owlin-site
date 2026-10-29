import { useState } from "react";
import styles from "./CopyButton.module.css";

export default function CopyButton({ value }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard access can be blocked; the value stays selectable on screen.
    }
  }

  return (
    <button type="button" className={styles.copy} onClick={copy} aria-label={`Copy ${value}`}>
      {copied ? "Copied" : "Copy"}
    </button>
  );
}
