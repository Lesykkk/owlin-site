import { useCallback, useEffect, useState } from "react";

// Loads data with `load()` and tracks its loading and error state. `reload()` loads it again;
// the previous data stays available meanwhile. `load` must be stable (declared outside the
// component or wrapped in useCallback), and loading again happens whenever it changes.
export function useRemote(load) {
  const [version, setVersion] = useState(0);
  const [result, setResult] = useState({ load: null, version: -1, data: null, error: null });

  useEffect(() => {
    let isCancelled = false;
    load().then(
      (data) => !isCancelled && setResult({ load, version, data, error: null }),
      (error) => !isCancelled && setResult({ load, version, data: null, error }),
    );
    return () => {
      isCancelled = true;
    };
  }, [load, version]);

  const reload = useCallback(() => setVersion((current) => current + 1), []);

  return {
    data: result.data,
    error: result.error,
    isLoading: result.load !== load || result.version !== version,
    reload,
  };
}
