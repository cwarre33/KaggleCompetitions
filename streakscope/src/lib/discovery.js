import {
  DATA_API,
  BATCH_SIZE,
  TRADES_LIMIT,
  WHALE_MIN_CASH,
  INITIAL_ENRICH,
  MAX_ENRICH,
  LEADERBOARD_PAGE,
} from "./constants.js";
import {
  fetchJson,
  fetchGammaMarkets,
  fetchProfile,
  fetchValue,
  fetchTradedCount,
} from "./api.js";
import {
  isSportsPosition,
  isSportsTrade,
  isResolved,
  isLiveBet,
  computeTraderStats,
} from "./sports.js";

function seedEntry(wallet, meta = {}) {
  return {
    wallet: wallet?.toLowerCase(),
    name: meta.name || meta.userName || "",
    pnl: meta.pnl ?? null,
    dayPnl: meta.dayPnl ?? null,
    vol: meta.vol ?? null,
    profileImage: meta.profileImage || "",
    source: meta.source || "unknown",
    rank: meta.rank ?? null,
    recentTrade: meta.recentTrade ?? null,
    whaleTrade: meta.whaleTrade ?? null,
  };
}

function mergeSeed(map, entry) {
  const w = entry.wallet;
  if (!w) return;
  const prev = map.get(w);
  if (!prev) {
    map.set(w, entry);
    return;
  }
  map.set(w, {
    ...prev,
    name: prev.name || entry.name,
    pnl: entry.pnl ?? prev.pnl,
    dayPnl: entry.dayPnl ?? prev.dayPnl,
    vol: entry.vol ?? prev.vol,
    profileImage: prev.profileImage || entry.profileImage,
    source: prev.source === entry.source ? prev.source : `${prev.source}+${entry.source}`,
    rank: prev.rank ?? entry.rank,
    recentTrade: pickNewerTrade(prev.recentTrade, entry.recentTrade),
    whaleTrade: prev.whaleTrade || entry.whaleTrade,
  });
}

function pickNewerTrade(a, b) {
  if (!a) return b;
  if (!b) return a;
  return (a.timestamp ?? 0) >= (b.timestamp ?? 0) ? a : b;
}

function scoreSeed(entry) {
  let s = 0;
  if (entry.dayPnl != null) s += Math.min(Math.abs(entry.dayPnl) / 5000, 50);
  if (entry.pnl != null) s += Math.min(Math.abs(entry.pnl) / 20000, 20);
  if (entry.recentTrade) s += 15;
  if (entry.whaleTrade) s += 25;
  if (entry.rank != null && entry.rank <= 50) s += 30 - entry.rank * 0.3;
  if (entry.source?.includes("market-positions")) s += 20;
  return s;
}

export async function discoverWalletSeeds(logDiag, onProgress) {
  const map = new Map();
  onProgress?.("Scanning global trade feed…");

  const [trades, whaleTrades, lbDay, lbWeek, lbMonth, lbVol] = await Promise.all([
    fetchJson(`${DATA_API}/trades?limit=${TRADES_LIMIT}&takerOnly=false`, logDiag),
    fetchJson(
      `${DATA_API}/trades?limit=100&filterType=CASH&filterAmount=${WHALE_MIN_CASH}&takerOnly=false`,
      logDiag,
    ),
    fetchJson(
      `${DATA_API}/v1/leaderboard?category=SPORTS&timePeriod=DAY&orderBy=PNL&limit=${LEADERBOARD_PAGE}`,
      logDiag,
    ),
    fetchJson(
      `${DATA_API}/v1/leaderboard?category=SPORTS&timePeriod=WEEK&orderBy=PNL&limit=${LEADERBOARD_PAGE}`,
      logDiag,
    ),
    fetchJson(
      `${DATA_API}/v1/leaderboard?category=SPORTS&timePeriod=MONTH&orderBy=PNL&limit=${LEADERBOARD_PAGE}`,
      logDiag,
    ),
    fetchJson(
      `${DATA_API}/v1/leaderboard?category=SPORTS&timePeriod=DAY&orderBy=VOL&limit=${LEADERBOARD_PAGE}`,
      logDiag,
    ),
  ]);

  for (const t of (trades || []).filter(isSportsTrade)) {
    mergeSeed(map, seedEntry(t.proxyWallet, {
      name: t.name || t.pseudonym,
      profileImage: t.profileImage,
      source: "trades",
      recentTrade: t,
    }));
  }

  for (const t of (whaleTrades || []).filter(isSportsTrade)) {
    mergeSeed(map, seedEntry(t.proxyWallet, {
      name: t.name || t.pseudonym,
      profileImage: t.profileImage,
      source: "whale",
      whaleTrade: t,
      recentTrade: t,
    }));
  }

  for (const [list, label, pnlKey] of [
    [lbDay, "lb-day", "dayPnl"],
    [lbWeek, "lb-week", "pnl"],
    [lbMonth, "lb-month", "pnl"],
    [lbVol, "lb-vol", "pnl"],
  ]) {
    for (const t of list || []) {
      mergeSeed(map, seedEntry(t.proxyWallet, {
        name: t.userName,
        pnl: t.pnl,
        [pnlKey]: t.pnl,
        vol: t.vol,
        profileImage: t.profileImage,
        source: label,
        rank: Number(t.rank),
      }));
    }
  }

  onProgress?.(`Found ${map.size} unique wallets — scanning hot markets…`);

  const hotMarkets = new Map();
  for (const t of (trades || []).filter(isSportsTrade)) {
    if (!t.conditionId) continue;
    const prev = hotMarkets.get(t.conditionId) || { count: 0, title: t.title, eventSlug: t.eventSlug };
    hotMarkets.set(t.conditionId, { ...prev, count: prev.count + 1 });
  }

  const topMarkets = [...hotMarkets.entries()]
    .sort((a, b) => b[1].count - a[1].count)
    .slice(0, 12)
    .map(([id]) => id);

  for (const cid of topMarkets) {
    const data = await fetchJson(
      `${DATA_API}/v1/market-positions?market=${cid}&status=OPEN&sortBy=CASH_PNL&limit=50`,
      logDiag,
    );
    if (!Array.isArray(data)) continue;
    for (const tokenGroup of data) {
      for (const pos of tokenGroup.positions || []) {
        mergeSeed(map, seedEntry(pos.proxyWallet, {
          name: pos.name,
          profileImage: pos.profileImage,
          source: "market-positions",
        }));
      }
    }
  }

  const ranked = [...map.values()]
    .map((s) => ({ ...s, priority: scoreSeed(s) }))
    .sort((a, b) => b.priority - a.priority);

  return { seeds: ranked, hotMarkets: topMarkets, tradeCount: (trades || []).filter(isSportsTrade).length };
}

export async function enrichTrader(seed, logDiag, ignoreFavorites) {
  const wallet = seed.wallet;
  const [openRaw, closedRaw, profile, portfolioValue, tradedCount] = await Promise.all([
    fetchJson(`${DATA_API}/positions?user=${wallet}&limit=200&sortBy=CASHPNL`, logDiag),
    fetchJson(`${DATA_API}/closed-positions?user=${wallet}&limit=200&sortBy=REALIZEDPNL`, logDiag),
    fetchProfile(wallet, logDiag),
    fetchValue(wallet, logDiag),
    fetchTradedCount(wallet, logDiag),
  ]);

  const openAll = Array.isArray(openRaw) ? openRaw : [];
  const closedAll = Array.isArray(closedRaw) ? closedRaw : [];
  const openSports = openAll.filter(isSportsPosition);
  const closedSports = closedAll.filter(isSportsPosition);
  const activeSports = openSports.filter((p) => !isResolved(p));

  const condIds = [...new Set(activeSports.map((p) => p.conditionId).filter(Boolean))];
  const now = Date.now();
  const gammaMarkets = condIds.length ? await fetchGammaMarkets(condIds, logDiag) : [];
  const gammaById = new Map();
  condIds.forEach((id, idx) => gammaById.set(id, gammaMarkets[idx]));

  const activeBets = activeSports.map((p) => {
    const gm = gammaById.get(p.conditionId);
    const usdSize = (p.size ?? 0) * (p.avgPrice ?? 0);
    return {
      ...p,
      gameStartTime: gm?.gameStartTime ?? null,
      sportsMarketType: gm?.sportsMarketType ?? null,
      live: isLiveBet(p, gm, now),
      usdSize,
      polymarketUrl: p.eventSlug
        ? `https://polymarket.com/event/${p.eventSlug}`
        : p.slug
          ? `https://polymarket.com/event/${p.slug}`
          : null,
    };
  });
  activeBets.sort((a, b) => (b.live ? 1 : 0) - (a.live ? 1 : 0) || (b.cashPnl ?? 0) - (a.cashPnl ?? 0));

  const stats = computeTraderStats(openSports, closedSports, ignoreFavorites);
  const openExposure = openSports.reduce((s, p) => s + (p.currentValue ?? 0), 0);
  const unrealizedPnl = openSports.reduce((s, p) => s + (p.cashPnl ?? 0), 0);

  return {
    ...seed,
    name: profile?.name || seed.name || profile?.pseudonym || wallet.slice(0, 8),
    pseudonym: profile?.pseudonym || "",
    bio: profile?.bio || "",
    xUsername: profile?.xUsername || "",
    verifiedBadge: profile?.verifiedBadge || false,
    createdAt: profile?.createdAt || null,
    takerTier: profile?.takerTier ?? null,
    portfolioValue,
    tradedCount,
    openSports,
    closedSports,
    activeBets,
    liveCount: activeBets.filter((b) => b.live).length,
    openExposure,
    unrealizedPnl,
    ...stats,
    profileUrl: `https://polymarket.com/profile/${wallet}`,
  };
}

export async function enrichTradersProgressive(seeds, logDiag, ignoreFavorites, onBatch, abort) {
  const limit = Math.min(seeds.length, MAX_ENRICH);
  const toProcess = seeds.slice(0, limit);

  for (let i = 0; i < toProcess.length; i += BATCH_SIZE) {
    if (abort?.aborted) return;
    const batch = toProcess.slice(i, i + BATCH_SIZE);
    const results = await Promise.allSettled(
      batch.map((s) => enrichTrader(s, logDiag, ignoreFavorites)),
    );
    const traders = results.filter((r) => r.status === "fulfilled").map((r) => r.value);
    onBatch(traders, i + batch.length, limit);
  }
}

export function computeKpis(traders, meta = {}) {
  const liveTraders = traders.filter((t) => t.liveCount > 0);
  const liveBets = traders.reduce((s, t) => s + (t.liveCount ?? 0), 0);
  const totalExposure = traders.reduce((s, t) => s + (t.openExposure ?? 0), 0);

  const hotStreaks = traders
    .filter((t) => t.streakType === "W" && t.streak >= 3)
    .sort((a, b) => b.streak - a.streak || (b.liveCount ?? 0) - (a.liveCount ?? 0))
    .slice(0, 10);

  const bigMovers = [...traders]
    .filter((t) => t.dayPnl != null || t.unrealizedPnl != null)
    .sort((a, b) => Math.abs(b.dayPnl ?? b.unrealizedPnl ?? 0) - Math.abs(a.dayPnl ?? a.unrealizedPnl ?? 0))
    .slice(0, 10);

  const betIndex = new Map();
  for (const t of traders) {
    for (const b of t.activeBets || []) {
      if (!b.conditionId) continue;
      const key = `${b.conditionId}:${b.outcomeIndex}`;
      const row = betIndex.get(key) || {
        conditionId: b.conditionId,
        title: b.title,
        outcome: b.outcome,
        eventSlug: b.eventSlug,
        live: false,
        wallets: [],
      };
      row.live = row.live || b.live;
      row.wallets.push({
        wallet: t.wallet,
        name: t.name,
        side: b.outcome,
        entry: b.avgPrice,
        now: b.curPrice,
        pnl: b.cashPnl,
        value: b.currentValue,
        live: b.live,
        streak: t.streakType === "W" ? t.streak : 0,
      });
      betIndex.set(key, row);
    }
  }

  const samePlay = [...betIndex.values()]
    .filter((g) => g.wallets.length >= 2)
    .sort((a, b) => (b.live ? 1 : 0) - (a.live ? 1 : 0) || b.wallets.length - a.wallets.length)
    .slice(0, 8);

  const whales = traders
    .filter((t) => t.whaleTrade)
    .sort((a, b) => (b.whaleTrade?.size ?? 0) - (a.whaleTrade?.size ?? 0))
    .slice(0, 8);

  return {
    walletsDiscovered: meta.seedCount ?? traders.length,
    walletsEnriched: traders.length,
    sportsTradesScanned: meta.tradeCount ?? 0,
    liveTraders: liveTraders.length,
    liveBets,
    totalExposure,
    hotStreaks,
    bigMovers,
    samePlay,
    whales,
  };
}

export async function lookupWallet(query, logDiag) {
  const q = query.trim();
  if (!q) return null;
  if (q.startsWith("0x") && q.length >= 10) {
    return seedEntry(q, { source: "search" });
  }
  const byName = await fetchJson(
    `${DATA_API}/v1/leaderboard?category=SPORTS&timePeriod=ALL&userName=${encodeURIComponent(q)}`,
    logDiag,
  );
  if (Array.isArray(byName) && byName[0]) {
    const t = byName[0];
    return seedEntry(t.proxyWallet, {
      name: t.userName,
      pnl: t.pnl,
      vol: t.vol,
      profileImage: t.profileImage,
      source: "search",
      rank: Number(t.rank),
    });
  }
  return null;
}

export { INITIAL_ENRICH };
