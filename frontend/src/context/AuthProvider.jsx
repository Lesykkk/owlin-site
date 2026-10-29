import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { supabase } from "../lib/supabase";
import { AuthContext } from "./authContext";

const RETURN_KEY = "owlin:returnTo";

// Maps the Supabase user to the few fields the UI needs from the Discord profile.
function toProfile(user) {
  if (!user) return null;

  const meta = user.user_metadata ?? {};
  return {
    id: user.id,
    username: meta.custom_claims?.global_name ?? meta.full_name ?? meta.name ?? "User",
    avatarUrl: meta.avatar_url ?? null,
    discordId: meta.provider_id ?? meta.sub ?? null,
    createdAt: user.created_at,
  };
}

export default function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      setUser(toProfile(data.session?.user));
      setIsLoading(false);
    });

    const { data } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(toProfile(session?.user));

      // Right after Discord login, continue where the user started (e.g. a checkout).
      const returnTo = session && localStorage.getItem(RETURN_KEY);
      if (returnTo) {
        localStorage.removeItem(RETURN_KEY);
        navigate(returnTo, { replace: true });
      }
    });
    return () => data.subscription.unsubscribe();
  }, [navigate]);

  // Supabase always returns to the site root, which keeps the allowed redirect URL simple.
  // `returnTo` (path and query) is remembered here and restored after sign-in.
  const login = useCallback((returnTo = window.location.pathname + window.location.search) => {
    localStorage.setItem(RETURN_KEY, returnTo);
    return supabase.auth.signInWithOAuth({
      provider: "discord",
      options: { redirectTo: `${window.location.origin}/` },
    });
  }, []);

  const logout = useCallback(() => supabase.auth.signOut(), []);

  const value = useMemo(() => ({ user, isLoading, login, logout }), [user, isLoading, login, logout]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
