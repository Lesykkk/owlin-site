import styles from "./Panel.module.css";

export default function Panel({ title, required = false, action, className = "", children }) {
  return (
    <section className={`${styles.panel} ${className}`}>
      <div className={styles.header}>
        <h2 className={styles.title}>
          {title}
          {required && (
            <>
              <span className={styles.required} aria-hidden="true">
                *
              </span>
              <span className={styles.srOnly}> (required)</span>
            </>
          )}
        </h2>
        {action}
      </div>
      {children}
    </section>
  );
}
