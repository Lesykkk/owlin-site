import { Link } from "react-router-dom";
import styles from "./Button.module.css";

// Renders a router link for internal paths ("/pricing"), a plain link for the rest,
// and a <button> when there is no href (use `type="submit"` inside forms).
export default function Button({
  href,
  onClick,
  type = "button",
  variant = "secondary",
  external = false,
  size = "md",
  disabled = false,
  className = "",
  children,
}) {
  const classes = [styles.button, styles[variant], styles[size], className].filter(Boolean).join(" ");

  if (href === undefined) {
    return (
      <button type={type} className={classes} onClick={onClick} disabled={disabled}>
        {children}
      </button>
    );
  }

  if (!external && href.startsWith("/")) {
    return (
      <Link to={href} className={classes}>
        {children}
      </Link>
    );
  }

  const externalProps = external ? { target: "_blank", rel: "noopener noreferrer" } : {};
  return (
    <a href={href} className={classes} {...externalProps}>
      {children}
    </a>
  );
}
