import { useId } from "react";
import styles from "./TextField.module.css";

export default function TextField({ label, value, onChange, placeholder }) {
  const id = useId();

  return (
    <div className={styles.field}>
      <label htmlFor={id}>{label}</label>
      <input id={id} type="text" value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} />
    </div>
  );
}
