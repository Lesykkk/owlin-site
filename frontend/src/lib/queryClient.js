import { QueryClient } from "@tanstack/react-query";

// One cache for the whole app. Fetched data is kept for a while and shown at once on the next
// visit; when it is older than `staleTime` it is refreshed quietly in the background (also when
// the tab becomes active again).
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      // Data nobody is looking at is dropped after this long.
      gcTime: 30 * 60_000,
      // Retry only what may fix itself: network failures (status 0) and server errors.
      retry: (failureCount, error) => failureCount < 2 && (!error.status || error.status >= 500),
    },
  },
});
