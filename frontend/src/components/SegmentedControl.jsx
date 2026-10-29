import styles from "./SegmentedControl.module.css";

// A row of mutually exclusive options. Each option needs an `id` and a `label`, and may have an `icon` element.
export default function SegmentedControl({ label, options, value, onChange }) {
  return (
    <div className={styles.switch} role="radiogroup" aria-label={label}>
      {options.map((option) => {
        const isActive = option.id === value;
        return (
          <button
            key={option.id}
            type="button"
            role="radio"
            aria-checked={isActive}
            className={`${styles.option} ${isActive ? styles.active : ""}`}
            onClick={() => onChange(option.id)}
          >
            {option.icon}
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
