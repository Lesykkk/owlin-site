import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { LINKS } from "../config/links";
import { CloseIcon, MenuIcon } from "./Icons";
import UserMenu from "./UserMenu";
import styles from "./Header.module.css";

const NAV_ITEMS = [
  { label: "Home", href: "/" },
  { label: "Features", href: "/#features" },
  { label: "Showcase", href: "/#showcase" },
  { label: "Pricing", href: "/pricing" },
  { label: "Promo", href: "/promo", badge: "Free" },
];

function NavLinks({ onNavigate }) {
  return (
    <>
      {NAV_ITEMS.map((item) => (
        <Link key={item.href} to={item.href} onClick={onNavigate}>
          {item.label}
          {item.badge && <span className={styles.badge}>{item.badge}</span>}
        </Link>
      ))}
      <a href={LINKS.discord} target="_blank" rel="noopener noreferrer" onClick={onNavigate}>
        Community ↗
      </a>
    </>
  );
}

export default function Header() {
  const [isOpen, setIsOpen] = useState(false);
  const close = () => setIsOpen(false);

  useEffect(() => {
    if (!isOpen) return undefined;

    const closeOnEscape = (event) => event.key === "Escape" && setIsOpen(false);
    document.addEventListener("keydown", closeOnEscape);
    return () => document.removeEventListener("keydown", closeOnEscape);
  }, [isOpen]);

  return (
    <header className={`container ${styles.header}`}>
      <Link to="/" className={styles.brand} aria-label="Owlin home" onClick={close}>
        <img src="/owl.png" alt="" />
        Owlin
      </Link>

      <nav className={styles.nav} aria-label="Main navigation">
        <NavLinks />
      </nav>

      <div className={styles.account}>
        <UserMenu />
      </div>

      <button
        type="button"
        className={styles.toggle}
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
        aria-controls="mobile-menu"
        aria-label={isOpen ? "Close menu" : "Open menu"}
      >
        {isOpen ? <CloseIcon /> : <MenuIcon />}
      </button>

      {isOpen && (
        <div id="mobile-menu" className={styles.panel}>
          <nav className={styles.panelNav} aria-label="Mobile navigation">
            <NavLinks onNavigate={close} />
          </nav>
          <div className={styles.panelAccount}>
            <UserMenu />
          </div>
        </div>
      )}
    </header>
  );
}
