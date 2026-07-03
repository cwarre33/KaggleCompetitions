import { useState, useEffect, useCallback } from "react";

const STATE_URL = `${import.meta.env.BASE_URL}data/sim-state.json`;
const LOG_URL = `${import.meta.env.BASE_URL}data/sim-log.md`;
const POLL_MS = 60_000;

export function useSimFeed() {
  const [state, setState] = useState(null);
  const [logMd, setLogMd] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    try {
      const bust = `t=${Date.now()}`;
      const [stateRes, logRes] = await Promise.all([
        fetch(`${STATE_URL}?${bust}`),
        fetch(`${LOG_URL}?${bust}`),
      ]);
      if (!stateRes.ok) throw new Error(`sim-state ${stateRes.status}`);
      setState(await stateRes.json());
      if (logRes.ok) setLogMd(await logRes.text());
      setError(null);
    } catch (e) {
      setError(e.message || "Failed to load sim feed");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, POLL_MS);
    return () => clearInterval(id);
  }, [refresh]);

  return { state, logMd, loading, error, refresh };
}
