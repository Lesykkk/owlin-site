import { useLocation } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import LoginPrompt from "./LoginPrompt";

// Renders the page for signed-in users; guests get a login prompt that returns here afterwards.
export default function RequireAuth({ children }) {
  const { user, isLoading, login } = useAuth();
  const { pathname, search } = useLocation();

  if (isLoading) return null;
  if (!user) return <LoginPrompt onLogin={() => login(pathname + search)} />;
  return children;
}
