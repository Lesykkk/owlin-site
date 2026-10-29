import { useEffect, useRef, useState } from "react";
import { MAX_SCREENSHOTS, MAX_SIZE_MB, pickScreenshots } from "../../lib/screenshots";
import styles from "./ScreenshotUpload.module.css";

// `items` is a list of { id, file, url }. Previews use object URLs, released when removed.
export default function ScreenshotUpload({ items, onChange }) {
  const inputRef = useRef(null);
  const itemsRef = useRef(items);
  const [errors, setErrors] = useState([]);
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    itemsRef.current = items;
  }, [items]);

  // Release any remaining preview URLs when the form goes away.
  useEffect(() => () => itemsRef.current.forEach((item) => URL.revokeObjectURL(item.url)), []);

  function addFiles(fileList) {
    const { accepted, errors: pickErrors } = pickScreenshots(items.length, Array.from(fileList));
    setErrors(pickErrors);
    if (accepted.length === 0) return;

    const added = accepted.map((file) => ({ id: crypto.randomUUID(), file, url: URL.createObjectURL(file) }));
    onChange([...items, ...added]);
  }

  function remove(id) {
    const removed = items.find((item) => item.id === id);
    URL.revokeObjectURL(removed.url);
    onChange(items.filter((item) => item.id !== id));
  }

  function handleDrop(event) {
    event.preventDefault();
    setIsDragging(false);
    addFiles(event.dataTransfer.files);
  }

  return (
    <div>
      <div
        className={`${styles.drop} ${isDragging ? styles.dragging : ""}`}
        onDragOver={(event) => {
          event.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
      >
        <span>Drop screenshots here or</span>
        <button type="button" className={styles.pick} onClick={() => inputRef.current.click()}>
          Choose files
        </button>
        <span className={styles.limits}>PNG, JPG or WebP · up to {MAX_SIZE_MB} MB each · max {MAX_SCREENSHOTS}</span>
        <input
          ref={inputRef}
          type="file"
          accept="image/png,image/jpeg,image/webp"
          multiple
          hidden
          onChange={(event) => {
            addFiles(event.target.files);
            event.target.value = "";
          }}
        />
      </div>

      {errors.length > 0 && (
        <ul className={styles.errors} role="alert">
          {errors.map((error) => (
            <li key={error}>{error}</li>
          ))}
        </ul>
      )}

      {items.length > 0 && (
        <ul className={styles.previews}>
          {items.map((item) => (
            <li key={item.id} className={styles.preview}>
              <img src={item.url} alt={item.file.name} />
              <button type="button" onClick={() => remove(item.id)} aria-label={`Remove ${item.file.name}`}>
                ×
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
