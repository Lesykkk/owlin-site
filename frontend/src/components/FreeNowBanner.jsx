import { useEffect, useRef, useState } from "react";
import { useActivePromotions } from "../hooks/queries";
import { formatDate } from "../lib/format";
import { CloseIcon } from "./Icons";
import styles from "./FreeNowBanner.module.css";

// Space kept free at each side of the strip (the close button needs it), and how fast a long text
// runs past (px per second).
const SIDE_PADDING = 48;
const SCROLL_SPEED = 60;
// Remembers which promotions the visitor closed, so the strip does not come back on every page.
const DISMISSED_KEY = "owlin:dismissed-promotions";

function readDismissed() {
  try {
    return localStorage.getItem(DISMISSED_KEY);
  } catch {
    return null;
  }
}

// A strip above the header with the promotions that are open for everyone right now, named as they
// are in the database. When the text is wider than the strip it runs from right to left instead of
// wrapping. Shows nothing when there is no promotion or the visitor closed it. A new or changed
// promotion shows the strip again.
export default function FreeNowBanner() {
  const { data } = useActivePromotions();
  const promotions = data?.promotions ?? [];
  const text = ["FREE NOW", ...promotions.map((item) => `${item.name} · until ${formatDate(item.endsAt)}`)].join(" · ");

  // What was closed is identified by the promotions themselves, so a different promotion is not hidden.
  const promotionsKey = promotions.map((item) => `${item.name}|${item.endsAt}`).join(";");
  const [dismissedKey, setDismissedKey] = useState(readDismissed);

  function dismiss() {
    setDismissedKey(promotionsKey);
    try {
      localStorage.setItem(DISMISSED_KEY, promotionsKey);
    } catch {
      // The strip is closed for this visit even when nothing can be stored.
    }
  }

  const stripRef = useRef(null);
  const measureRef = useRef(null);
  const [scroll, setScroll] = useState({ isOn: false, seconds: 0 });

  // Compares the width of the text with the strip, now and whenever either changes.
  useEffect(() => {
    const strip = stripRef.current;
    const measure = measureRef.current;
    if (!strip || !measure) return undefined;

    const update = () => {
      const textWidth = measure.offsetWidth;
      const isOn = textWidth > strip.clientWidth - SIDE_PADDING * 2;
      const seconds = Math.round((textWidth + SIDE_PADDING * 2) / SCROLL_SPEED);
      setScroll((current) => (current.isOn === isOn && current.seconds === seconds ? current : { isOn, seconds }));
    };

    const observer = new ResizeObserver(update);
    observer.observe(strip);
    observer.observe(measure);
    return () => observer.disconnect();
  }, [text]);

  if (promotions.length === 0 || dismissedKey === promotionsKey) return null;

  return (
    <div ref={stripRef} className={`${styles.strip} ${scroll.isOn ? styles.scrolling : ""}`}>
      <span ref={measureRef} className={styles.measure} aria-hidden="true">
        {text}
      </span>
      {scroll.isOn ? (
        <>
          <span className={styles.screenReader}>{text}</span>
          <div className={styles.track} style={{ "--seconds": `${scroll.seconds}s` }} aria-hidden="true">
            <span className={styles.item}>{text}</span>
            <span className={styles.item}>{text}</span>
          </div>
        </>
      ) : (
        text
      )}
      <button type="button" className={styles.close} onClick={dismiss} aria-label="Close announcement">
        <CloseIcon strokeWidth="2.6" strokeLinecap="butt" />
      </button>
    </div>
  );
}
