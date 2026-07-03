import { SPORTS_RE } from "./constants.js";

export function isSportsText(...parts) {
  const hay = parts.filter(Boolean).join(" ").replace(/-/g, " ");
  return SPORTS_RE.test(hay);
}

export function isSportsPosition(p) {
  return isSportsText(p.title, p.slug, p.eventSlug);
}

export function isSportsTrade(t) {
  return isSportsText(t.title, t.slug, t.eventSlug);
}

export function isResolved(p) {
  return (
    p.redeemable === true ||
    (p.curPrice != null && (p.curPrice >= 0.999 || p.curPrice <= 0.001))
  );
}

export function isWinResolved(p) {
  return p.redeemable === true || (p.curPrice != null && p.curPrice >= 0.999);
}

export function isWinClosed(p) {
  return (p.realizedPnl ?? 0) > 0;
}

export function hedgeExcludedIds(positions) {
  const byCond = new Map();
  for (const p of positions) {
    if (!p.conditionId) continue;
    const set = byCond.get(p.conditionId) ?? new Set();
    set.add(p.outcomeIndex);
    byCond.set(p.conditionId, set);
  }
  const excluded = new Set();
  for (const [cid, indices] of byCond) {
    if (indices.size > 1) excluded.add(cid);
  }
  return excluded;
}

function sortByDateDesc(a, b) {
  const da = new Date(a.endDate || (a.timestamp ? a.timestamp * 1000 : 0) || 0).getTime();
  const db = new Date(b.endDate || (b.timestamp ? b.timestamp * 1000 : 0) || 0).getTime();
  return db - da;
}

export function buildResolvedList(closedSports, openSports, excluded) {
  const closedFiltered = closedSports
    .filter((p) => !excluded.has(p.conditionId))
    .map((p) => ({ ...p, streakSource: "realized" }))
    .sort(sortByDateDesc);

  if (closedFiltered.length > 0) return closedFiltered;

  return openSports
    .filter((p) => !excluded.has(p.conditionId) && isResolved(p))
    .map((p) => ({ ...p, streakSource: "inferred" }))
    .sort(sortByDateDesc);
}

export function computeStreak(resolved, ignoreFavorites) {
  const rows = [];
  for (const p of resolved) {
    const win = p.streakSource === "realized" ? isWinClosed(p) : isWinResolved(p);
    if (ignoreFavorites && win && (p.avgPrice ?? 0) > 0.95) continue;
    rows.push({
      win,
      title: p.title || p.slug || "Unknown",
      avgPrice: p.avgPrice ?? 0,
      endDate: p.endDate,
    });
  }

  if (rows.length === 0) {
    return {
      streak: 0,
      streakType: null,
      hitRate: 0,
      resolvedCount: 0,
      avgEntry: 0,
      last20: [],
      streakSource: resolved[0]?.streakSource ?? "inferred",
    };
  }

  const firstType = rows[0].win ? "W" : "L";
  let streak = 0;
  for (const r of rows) {
    const t = r.win ? "W" : "L";
    if (t === firstType) streak++;
    else break;
  }

  const wins = rows.filter((r) => r.win).length;
  return {
    streak,
    streakType: firstType,
    hitRate: rows.length ? wins / rows.length : 0,
    resolvedCount: rows.length,
    avgEntry: rows.reduce((s, r) => s + r.avgPrice, 0) / rows.length,
    last20: rows.slice(0, 20).reverse(),
    streakSource: rows[0]?.streakSource ?? resolved[0]?.streakSource ?? "inferred",
  };
}

export function isLiveBet(position, gammaMarket, now) {
  if (isResolved(position)) return false;
  const gst = gammaMarket?.gameStartTime;
  if (!gst) return false;
  const start = new Date(gst).getTime();
  return !Number.isNaN(start) && start <= now;
}

export function computeTraderStats(openSports, closedSports, ignoreFavorites) {
  const allForHedge = [...openSports, ...closedSports];
  const excluded = hedgeExcludedIds(allForHedge);
  const resolved = buildResolvedList(closedSports, openSports, excluded);
  return computeStreak(resolved, ignoreFavorites);
}
