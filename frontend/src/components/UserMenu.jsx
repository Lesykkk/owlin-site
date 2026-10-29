import { Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import Button from "./Button";
import { DiscordIcon } from "./Icons";
import styles from "./UserMenu.module.css";

// Account area of the header: login button for guests, avatar and logout for signed-in users.
export default function UserMenu() {
  const { user, isLoading, login, logout } = useAuth();

  if (isLoading) return <div className={styles.placeholder} aria-hidden="true" />;

  if (!user) {
    return (
      <Button variant="outline" size="sm" onClick={() => login()}>
        <DiscordIcon />
        Login with Discord
      </Button>
    );
  }

  return (
    <div className={styles.menu}>
      <Link to="/profile" className={styles.user}>
        {user.avatarUrl && <img src={user.avatarUrl} alt="" width="32" height="32" />}
        {user.username}
      </Link>
      <Button variant="outline" size="sm" onClick={logout}>
        Log out
      </Button>
    </div>
  );
}
