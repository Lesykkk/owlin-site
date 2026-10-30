import { useLayoutEffect, useRef } from "react";
import styles from "./SegmentedControl.module.css";

// A row of mutually exclusive options. Each option needs an `id` and a `label`, and may have an `icon` element.
// A highlight slides from the old option to the new one.
export default function SegmentedControl({ label, options, value, onChange }) {
  const switchRef = useRef(null);
  const indicatorRef = useRef(null);

  // Puts the highlight under the chosen option, and keeps it there when the row changes size or wraps.
  useLayoutEffect(() => {
    const row = switchRef.current;
    const indicator = indicatorRef.current;
    const chosen = row?.querySelector('[aria-checked="true"]');
    if (!row || !indicator || !chosen) return undefined;

    const place = () => {
      indicator.style.width = `${chosen.offsetWidth}px`;
      indicator.style.height = `${chosen.offsetHeight}px`;
      indicator.style.transform = `translate(${chosen.offsetLeft}px, ${chosen.offsetTop}px)`;
    };
    place();

    // The first placement jumps into position; only later moves slide.
    const frame = requestAnimationFrame(() => {
      indicator.dataset.ready = "true";
    });
    const observer = new ResizeObserver(place);
    observer.observe(row);
    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
    };
  }, [value, options]);

  return (
    <div ref={switchRef} className={styles.switch} role="radiogroup" aria-label={label}>
      <span ref={indicatorRef} className={styles.indicator} aria-hidden="true" />
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
