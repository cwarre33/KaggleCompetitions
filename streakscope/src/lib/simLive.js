import {
  DEFAULT_SIM_CONFIG,
  DEFAULT_STRATEGY,
  evaluatePick,
  mutateStrategy,
  simPnl,
  trialMetrics,
} from "./simTrader.js";
import { isSportsTrade, isResolved, isWinResolved } from "./sports.js";
import { fetchGammaMarkets } from "./api.js";

export const CONSENSUS_WINDOW_MS = 14 * 86400000;
export const MAX_SEEN_TRADES = 2500;
export const MAX_ARCHIVED_TRIALS = 40;

export function createNewTrial(trialNum, strategy) {
  return {
    trialNum,
    strategy: { ...strategy },
    status: "active",
    startedAt: new Date().toISOString(),
    endedAt: null,
    realizedPnl: 0,
    unrealizedPnl: 0,
    peak: 0,
    openPicks: [],
    closedPicks: [],
    seenTradeKeys: [],
    endReason: null,
    sustained: false,
  };
}

export function createInitialState() {
  const strategy = { ...DEFAULT_STRATEGY, stakeUsd: DEFAULT_SIM_CONFIG.stakeUsd };
  return {
    version: 1,
    updatedAt: new Date().toISOString(),
    heartbeatCount: 0,
    lastTradePollAt: null,
    config: { ...DEFAULT_SIM_CONFIG },
    ignoreFavorites: true,
    currentTrial: createNewTrial(1, strategy),
    archivedTrials: [],
    winner: null,
    recentConsensus: [],
    lastHeartbeatNote: "Initialized",
  };
}

function tradeKey(t) {
  return `${t.transactionHash || "na"}:${t.proxyWallet}:${t.conditionId}:${t.timestamp}`;
}

function tradeTs(t) {
  const ts = t.timestamp;
  if (ts == null) return Date.now();
  return ts < 1e12 ? ts * 1000 : ts;
}

function betKey(conditionId, outcomeIndex) {
  return `${conditionId}:${outcomeIndex}`;
}

function pruneConsensus(entries, now) {
  const cutoff = now - CONSENSUS_WINDOW_MS;
  return entries.filter((e) => e.ts >= cutoff).slice(-500);
}

function consensusCount(entries, conditionId, outcomeIndex, now) {
  const cutoff = now - CONSENSUS_WINDOW_MS;
  const wallets = new Set();
  for (const e of entries) {
    if (e.ts < cutoff) continue;
    if (e.conditionId !== conditionId || e.outcomeIndex !== outcomeIndex) continue;
    wallets.add(e.wallet);
  }
  return wallets.size;
}

function unrealizedPnl(stake, entry, curPrice) {
  const e = Math.max(entry, 0.01);
  const cur = Math.max(curPrice ?? e, 0);
  return (stake / e) * cur - stake;
}

function parseOutcomePrices(market) {
  if (!market) return null;
  if (Array.isArray(market.outcomePrices)) return market.outcomePrices.map(Number);
  if (typeof market.outcomePrices === "string") {
    try {
      return JSON.parse(market.outcomePrices).map(Number);
    } catch {
      return null;
    }
  }
  return null;
}

function marketPrice(market, outcomeIndex) {
  const prices = parseOutcomePrices(market);
  if (prices && prices[outcomeIndex] != null) return prices[outcomeIndex];
  if (market?.bestBid != null && market?.bestAsk != null) {
    return (Number(market.bestBid) + Number(market.bestAsk)) / 2;
  }
  return null;
}

function archiveTrial(trial, endReason, sustained) {
  const m = trialMetrics(trial);
  return {
    ...trial,
    status: sustained ? "sustained" : "archived",
    endedAt: new Date().toISOString(),
    endReason,
    sustained,
    metrics: m,
    picks: trial.closedPicks,
  };
}

function checkTrialEnd(trial, config) {
  const m = trialMetrics(trial);
  if (m.totalPnl <= -config.stopLossUsd) {
    return { end: true, reason: "stop_loss", sustained: false };
  }
  if (
    trial.closedPicks.length >= config.minBetsForSuccess
    && m.realizedPnl >= config.profitTargetUsd
    && m.winRate >= 0.5
  ) {
    return { end: true, reason: "profit_target", sustained: true };
  }
  return { end: false };
}

function startNextTrial(state, lastTrial, endReason) {
  const archived = archiveTrial(state.currentTrial, endReason, false);
  state.archivedTrials.push(archived);
  if (state.archivedTrials.length > MAX_ARCHIVED_TRIALS) {
    state.archivedTrials = state.archivedTrials.slice(-MAX_ARCHIVED_TRIALS);
  }

  const nextNum = archived.trialNum + 1;
  const nextStrategy = mutateStrategy(state.currentTrial.strategy, {
    endReason,
    metrics: trialMetrics(state.currentTrial),
    sustained: false,
  });
  nextStrategy.stakeUsd = state.config.stakeUsd;
  state.currentTrial = createNewTrial(nextNum, nextStrategy);
  state.lastHeartbeatNote = `Trial ${archived.trialNum} ended (${endReason}) → trial ${nextNum}`;
}

export async function runLiveHeartbeat(state, traders, trades, logDiag, now = Date.now()) {
  const traderMap = new Map(traders.map((t) => [t.wallet?.toLowerCase(), t]));
  const trial = state.currentTrial;
  const strategy = trial.strategy;
  let newPicks = 0;

  state.recentConsensus = pruneConsensus(state.recentConsensus, now);

  for (const t of trades || []) {
    if (!isSportsTrade(t)) continue;
    if (t.side && t.side !== "BUY") continue;
    if (!t.conditionId || t.outcomeIndex == null) continue;

    const key = tradeKey(t);
    if (trial.seenTradeKeys.includes(key)) continue;
    trial.seenTradeKeys.push(key);
    if (trial.seenTradeKeys.length > MAX_SEEN_TRADES) {
      trial.seenTradeKeys = trial.seenTradeKeys.slice(-MAX_SEEN_TRADES);
    }

    const wallet = t.proxyWallet?.toLowerCase();
    const ts = tradeTs(t);
    state.recentConsensus.push({
      ts,
      conditionId: t.conditionId,
      outcomeIndex: t.outcomeIndex,
      wallet,
    });

    const trader = traderMap.get(wallet);
    if (!trader) continue;

    const price = t.price ?? 0;
    const consensus = consensusCount(state.recentConsensus, t.conditionId, t.outcomeIndex, now);
    if (evaluatePick(strategy, trader, price, consensus) < 0) continue;

    const dup =
      trial.openPicks.some((p) => betKey(p.conditionId, p.outcomeIndex) === betKey(t.conditionId, t.outcomeIndex))
      || trial.closedPicks.some((p) => betKey(p.conditionId, p.outcomeIndex) === betKey(t.conditionId, t.outcomeIndex));
    if (dup) continue;

    const stake = strategy.stakeUsd ?? state.config.stakeUsd;
    trial.openPicks.push({
      id: key,
      openedAt: new Date(ts).toISOString(),
      title: t.title || t.slug || "Unknown",
      outcome: t.outcome,
      conditionId: t.conditionId,
      outcomeIndex: t.outcomeIndex,
      eventSlug: t.eventSlug,
      trader: trader.name,
      wallet,
      streak: trader.streak,
      hitRate: trader.hitRate,
      entry: price,
      stake,
      curPrice: price,
      unrealizedPnl: 0,
    });
    newPicks++;
  }

  const condIds = [...new Set(trial.openPicks.map((p) => p.conditionId).filter(Boolean))];
  const markets = condIds.length ? await fetchGammaMarkets(condIds, logDiag) : [];
  const marketById = new Map(condIds.map((id, i) => [id, markets[i]]));

  let settled = 0;
  const stillOpen = [];

  for (const pick of trial.openPicks) {
    const market = marketById.get(pick.conditionId);
    const cur = marketPrice(market, pick.outcomeIndex) ?? pick.curPrice ?? pick.entry;
    pick.curPrice = cur;

    const resolved = cur >= 0.995 || cur <= 0.005 || isResolved({ curPrice: cur, redeemable: market?.closed });
    if (!resolved) {
      pick.unrealizedPnl = unrealizedPnl(pick.stake, pick.entry, cur);
      stillOpen.push(pick);
      continue;
    }

    const win = cur >= 0.995 || isWinResolved({ curPrice: cur });
    const pnl = simPnl(pick.stake, pick.entry, win);
    trial.realizedPnl += pnl;
    trial.closedPicks.push({
      ...pick,
      closedAt: new Date(now).toISOString(),
      win,
      pnl,
      bankroll: trial.realizedPnl,
    });
    settled++;
  }

  trial.openPicks = stillOpen;
  trial.unrealizedPnl = stillOpen.reduce((s, p) => s + (p.unrealizedPnl ?? 0), 0);
  const totalPnl = trial.realizedPnl + trial.unrealizedPnl;
  trial.peak = Math.max(trial.peak ?? 0, totalPnl);

  const endCheck = checkTrialEnd(trial, state.config);
  if (endCheck.end) {
    if (endCheck.sustained) {
      const winner = archiveTrial(trial, endCheck.reason, true);
      state.archivedTrials.push(winner);
      state.winner = winner;
      const nextStrategy = { ...trial.strategy };
      state.currentTrial = createNewTrial(trial.trialNum + 1, nextStrategy);
      state.lastHeartbeatNote = `Trial ${trial.trialNum} sustained profit — champion logged, continuing`;
    } else {
      startNextTrial(state, trial, endCheck.reason);
    }
  } else if (newPicks || settled) {
    state.lastHeartbeatNote = `${newPicks} new picks · ${settled} settled · PnL ${totalPnl >= 0 ? "+" : ""}$${totalPnl.toFixed(2)}`;
  }

  state.heartbeatCount += 1;
  state.updatedAt = new Date(now).toISOString();
  state.lastTradePollAt = new Date(now).toISOString();

  return {
    newPicks,
    settled,
    totalPnl,
    tradersScanned: traders.length,
  };
}

export function loadState(raw) {
  if (!raw || typeof raw !== "object") return createInitialState();
  const base = createInitialState();
  return {
    ...base,
    ...raw,
    config: { ...base.config, ...(raw.config || {}) },
    currentTrial: { ...base.currentTrial, ...(raw.currentTrial || {}) },
    archivedTrials: raw.archivedTrials || [],
    recentConsensus: raw.recentConsensus || [],
  };
}
