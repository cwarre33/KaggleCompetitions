import { DATA_API } from "./constants.js";
import { fetchJson } from "./api.js";
import { isSportsTrade } from "./sports.js";

export const ALERT_WINDOW_MS = 5 * 60 * 1000;
export const ALERT_POLL_MS = 30 * 1000;
export const ALERT_COOLDOWN_MS = 10 * 60 * 1000;
export const MIN_STREAK = 3;
export const TRADES_POLL_LIMIT = 150;

function tradeKey(t) {
  return `${t.transactionHash || "na"}:${t.proxyWallet}:${t.conditionId}:${t.timestamp}`;
}

function betKey(t) {
  return `${t.conditionId}:${t.outcomeIndex}`;
}

function tradeTs(t) {
  const ts = t.timestamp;
  if (ts == null) return Date.now();
  return ts < 1e12 ? ts * 1000 : ts;
}

export function buildStreakerIndex(traders, minStreak = MIN_STREAK) {
  const index = new Map();
  for (const t of traders) {
    if (t.streakType === "W" && t.streak >= minStreak) {
      index.set(t.wallet?.toLowerCase(), {
        wallet: t.wallet?.toLowerCase(),
        name: t.name,
        streak: t.streak,
        profileUrl: t.profileUrl,
      });
    }
  }
  return index;
}

export function createAlertEngine() {
  const seenTrades = new Set();
  const recentEntries = [];
  const firedAlerts = new Map();

  function prune(now) {
    const cutoff = now - ALERT_WINDOW_MS;
    while (recentEntries.length && recentEntries[0].ts < cutoff) {
      recentEntries.shift();
    }
    for (const [k, at] of firedAlerts) {
      if (now - at > ALERT_COOLDOWN_MS) firedAlerts.delete(k);
    }
  }

  function processTrades(trades, streakers, now = Date.now()) {
    prune(now);
    const newAlerts = [];

    for (const t of trades || []) {
      if (!isSportsTrade(t)) continue;
      if (t.side && t.side !== "BUY") continue;
      if (!t.conditionId || t.outcomeIndex == null) continue;

      const key = tradeKey(t);
      if (seenTrades.has(key)) continue;
      seenTrades.add(key);
      if (seenTrades.size > 5000) {
        const arr = [...seenTrades];
        seenTrades.clear();
        arr.slice(-2500).forEach((k) => seenTrades.add(k));
      }

      const wallet = t.proxyWallet?.toLowerCase();
      const streaker = streakers.get(wallet);
      if (!streaker) continue;

      const entry = {
        ts: tradeTs(t),
        wallet,
        name: streaker.name || t.name || t.pseudonym,
        streak: streaker.streak,
        conditionId: t.conditionId,
        outcomeIndex: t.outcomeIndex,
        outcome: t.outcome,
        title: t.title,
        eventSlug: t.eventSlug,
        slug: t.slug,
        price: t.price,
        size: t.size,
        cash: (t.size ?? 0) * (t.price ?? 0),
        trade: t,
      };
      recentEntries.push(entry);

      const groupKey = betKey(t);
      const windowStart = now - ALERT_WINDOW_MS;
      const inWindow = recentEntries.filter(
        (e) => e.conditionId === t.conditionId && e.outcomeIndex === t.outcomeIndex && e.ts >= windowStart,
      );
      const uniqueWallets = [...new Set(inWindow.map((e) => e.wallet))];
      if (uniqueWallets.length < 2) continue;

      const alertId = `${groupKey}:${uniqueWallets.sort().join(",")}`;
      if (firedAlerts.has(alertId)) continue;
      firedAlerts.set(alertId, now);

      newAlerts.push({
        id: `${alertId}:${now}`,
        at: now,
        conditionId: t.conditionId,
        outcome: t.outcome,
        title: t.title || t.slug || "Unknown market",
        eventSlug: t.eventSlug,
        traders: inWindow
          .filter((e, i, arr) => arr.findIndex((x) => x.wallet === e.wallet) === i)
          .sort((a, b) => a.ts - b.ts)
          .map((e) => ({
            wallet: e.wallet,
            name: e.name,
            streak: e.streak,
            price: e.price,
            size: e.size,
            cash: e.cash,
            at: e.ts,
          })),
      });
    }

    return newAlerts;
  }

  return { processTrades, reset() {
    seenTrades.clear();
    recentEntries.length = 0;
    firedAlerts.clear();
  }};
}

export async function pollRecentTrades(logDiag) {
  return fetchJson(
    `${DATA_API}/trades?limit=${TRADES_POLL_LIMIT}&takerOnly=false`,
    logDiag,
  );
}

export function notifyBrowser(alert) {
  if (typeof Notification === "undefined" || Notification.permission !== "granted") return;
  const names = alert.traders.map((t) => `${t.name} (${t.streak}W)`).join(", ");
  const body = `${alert.traders.length} streakers on ${alert.outcome} within 5 min: ${names}`;
  try {
    new Notification("StreakScope — Same Play Alert", {
      body: `${alert.title}\n${body}`,
      tag: alert.id,
    });
  } catch {
    /* ignore */
  }
}

export async function requestNotificationPermission() {
  if (typeof Notification === "undefined") return "unsupported";
  if (Notification.permission === "granted") return "granted";
  if (Notification.permission === "denied") return "denied";
  return Notification.requestPermission();
}
