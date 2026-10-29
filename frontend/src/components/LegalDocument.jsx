import styles from "./LegalDocument.module.css";

// The frame of a long legal text: a title, the date it was last updated, then the text itself.
// Plain headings, paragraphs, lists and tables inside `children` are styled here.
export default function LegalDocument({ title, updated, children }) {
  return (
    <article className={`container ${styles.page}`}>
      <div className={styles.card}>
        <h1 className={styles.title}>{title}</h1>
        <p className={styles.updated}>Last updated: {updated}</p>
        <div className={styles.text}>{children}</div>
      </div>
    </article>
  );
}
