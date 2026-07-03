import { useEffect, useRef, useCallback, useState, useMemo } from "react";
import {
  ALERT_POLL_MS,
  buildStreakerIndex,
  createAlertEngine,
  pollRecentTrades,
  notifyBrowser,
  requestNotificationPermission,
} from "../lib/alerts.js";

export function useStreakerAlerts({ traders, logDiag, enabled, browserNotify }) {
  const [alerts, setAlerts] = useState([]);
  const [unread, setUnread] = useState(0);
  const [lastPoll, setLastPoll] = useState(null);
  const engineRef = useRef(null);
  const tradersRef = useRef(traders);

  if (!engineRef.current) engineRef.current = createAlertEngine();
  tradersRef.current = traders;

  const streakers = useMemo(() => buildStreakerIndex(traders), [traders]);
  const watching = streakers.size;

  const markRead = useCallback(() => setUnread(0), []);

  const dismissAlert = useCallback((id) => {
    setAlerts((prev) => prev.filter((a) => a.id !== id));
  }, []);

  const clearAlerts = useCallback(() => {
    setAlerts([]);
    setUnread(0);
  }, []);

  useEffect(() => {
    if (!enabled || watching === 0) return;

    let cancelled = false;

    const tick = async () => {
      if (cancelled) return;
      const index = buildStreakerIndex(tradersRef.current);
      if (index.size === 0) return;

      const trades = await pollRecentTrades(logDiag);
      if (cancelled || !trades) return;
      setLastPoll(Date.now());

      const fresh = engineRef.current.processTrades(trades, index);
      if (fresh.length === 0) return;

      setAlerts((prev) => [...fresh, ...prev].slice(0, 50));
      setUnread((n) => n + fresh.length);
      if (browserNotify) {
        for (const a of fresh) notifyBrowser(a);
      }
    };

    tick();
    const id = setInterval(tick, ALERT_POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [enabled, browserNotify, logDiag, watching]);

  useEffect(() => {
    if (!enabled) engineRef.current.reset();
  }, [enabled]);

  return {
    alerts,
    unread,
    watching,
    lastPoll,
    markRead,
    dismissAlert,
    clearAlerts,
    requestPermission: requestNotificationPermission,
  };
}
