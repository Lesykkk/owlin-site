import { createClient } from "@supabase/supabase-js";

// The publishable key is meant for browsers: access is limited by Row Level Security.
export const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY,
  { auth: { flowType: "pkce" } },
);
