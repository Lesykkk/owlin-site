import { SUPPORT_CONTACTS } from "../config/links";
import styles from "./SupportNote.module.css";

// A short "write to us" line with the Discord profiles to message.
export default function SupportNote({ className = "" }) {
  return (
    <p className={`${styles.note} ${className}`}>
      Have troubles? Send a direct message on Discord:
      {SUPPORT_CONTACTS.map((contact) => (
        <a key={contact.href} href={contact.href} target="_blank" rel="noopener noreferrer">
          {contact.label} ↗
        </a>
      ))}
    </p>
  );
}
