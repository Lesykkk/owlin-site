import { useEffect, useRef } from "react";
import { Outlet, useLocation } from "react-router-dom";
import FreeNowBanner from "../components/FreeNowBanner";
import Header from "../components/Header";
import Footer from "../components/Footer";
import styles from "./MainLayout.module.css";

export default function MainLayout() {
  const { pathname, hash } = useLocation();
  const scrollRef = useRef(null);

  // Scroll to the linked section ("/#showcase"), or to the top on a plain page change.
  useEffect(() => {
    const target = hash && document.getElementById(hash.slice(1));
    if (target) target.scrollIntoView();
    else scrollRef.current?.scrollTo(0, 0);
  }, [pathname, hash]);

  return (
    <div className={styles.layout}>
      <FreeNowBanner />
      <div ref={scrollRef} className={styles.scroll}>
        <Header />
        <main className={styles.content}>
          <Outlet />
        </main>
        <Footer />
      </div>
    </div>
  );
}
