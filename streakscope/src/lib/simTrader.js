import { isWinClosed, computeTraderStats } from "./sports.js";

export const DEFAULT_SIM_CONFIG = {
  stopLossUsd: 50,
  profitTargetUsd: 40,
  minBetsForSuccess: 10,
  maxTrials: 25,
  stakeUsd: 10,
};

export const DEFAULT_STRATEGY = {
  generation: 1,
  minStreak: 3,
  minHitRate: 0.52,
  minEntryPrice: 0.2,
  maxEntryPrice: 0.72,
  requireConsensus: false,
  minConsensus: 2,
  pickMode: "top_streak",
  stakeUsd: 10,
};

function parseTs(position) {
  if (position.endDate) return new Date(position.endDate).getTime();
  if (position.timestamp) return position.timestamp < 1e12 ? position.timestamp * 1000 : position.timestamp;
  return 0;
}

function betKey(p) {
  return `${p.conditionId}:${p.outcomeIndex ?? p.outcome}`;
}

function simPnl(stake, avgPrice, win) {
  const price = Math.max(avgPrice, 0.01);
  if (win) return stake * ((1 - price) / price);
  return -stake;
}

export function buildBetTimeline(traders) {
  const closedByWallet = new Map();
  for (const t of traders) {
    const rows = (t.closedSports || [])
      .map((p) => ({ ...p, wallet: t.wallet, traderName: t.name }))
      .filter((p) => parseTs(p) > 0);
    closedByWallet.set(t.wallet, rows);
  }

  const events = [];
  for (const t of traders) {
    for (const p of t.closedSports || []) {
      const ts = parseTs(p);
      if (!ts) continue;
      events.push({
        ts,
        wallet: t.wallet,
        name: t.name,
        position: p,
      });
    }
  }
  events.sort((a, b) => a.ts - b.ts);
  return { events, closedByWallet };
}

function statsAtTime(closedByWallet, wallet, ts, ignoreFavorites) {
  const closed = (closedByWallet.get(wallet) || []).filter((p) => parseTs(p) < ts);
  return computeTraderStats([], closed, ignoreFavorites);
}

function consensusCount(events, idx, windowMs = 14 * 86400000) {
  const e = events[idx];
  const key = betKey(e.position);
  const wallets = new Set();
  for (let j = 0; j < idx; j++) {
    const other = events[j];
    if (other.ts < e.ts - windowMs) continue;
    if (betKey(other.position) !== key) continue;
    wallets.add(other.wallet);
  }
  return wallets.size;
}

function pickScore(strategy, stats, position, consensus) {
  if (stats.streakType !== "W" || stats.streak < strategy.minStreak) return -1;
  if (stats.hitRate < strategy.minHitRate) return -1;
  const price = position.avgPrice ?? 0;
  if (price < strategy.minEntryPrice || price > strategy.maxEntryPrice) return -1;
  if (strategy.requireConsensus && consensus < strategy.minConsensus) return -1;

  const edge = 1 - price;
  switch (strategy.pickMode) {
    case "high_hit":
      return stats.hitRate * 100 + stats.streak;
    case "value":
      return edge * 100 + stats.streak * 0.5;
    case "consensus":
      return consensus * 20 + stats.streak;
    case "top_streak":
    default:
      return stats.streak * 10 + stats.hitRate * 50;
  }
}

export function runTrial(strategy, traders, config, ignoreFavorites) {
  const { events, closedByWallet } = buildBetTimeline(traders);
  const stake = strategy.stakeUsd ?? config.stakeUsd;
  const picks = [];
  let bankroll = 0;
  let peak = 0;
  let maxDrawdown = 0;
  let endReason = "completed";
  const taken = new Set();

  for (let i = 0; i < events.length; i++) {
    const e = events[i];
    const key = `${e.wallet}:${betKey(e.position)}:${e.ts}`;
    if (taken.has(key)) continue;

    const stats = statsAtTime(closedByWallet, e.wallet, e.ts, ignoreFavorites);
    const consensus = consensusCount(events, i);
    const score = pickScore(strategy, stats, e.position, consensus);
    if (score < 0) continue;

    const win = isWinClosed(e.position);
    const pnl = simPnl(stake, e.position.avgPrice ?? 0.5, win);
    bankroll += pnl;
    peak = Math.max(peak, bankroll);
    maxDrawdown = Math.min(maxDrawdown, bankroll - peak);
    taken.add(key);

    picks.push({
      ts: e.ts,
      title: e.position.title || "Unknown",
      outcome: e.position.outcome,
      trader: e.name,
      wallet: e.wallet,
      streak: stats.streak,
      hitRate: stats.hitRate,
      entry: e.position.avgPrice,
      consensus,
      score,
      win,
      pnl,
      bankroll,
    });

    if (bankroll <= -config.stopLossUsd) {
      endReason = "stop_loss";
      break;
    }
    if (bankroll >= config.profitTargetUsd && picks.length >= config.minBetsForSuccess) {
      endReason = "profit_target";
      break;
    }
  }

  const wins = picks.filter((p) => p.win).length;
  const losses = picks.length - wins;
  const totalPnl = picks.reduce((s, p) => s + p.pnl, 0);
  const avgEntry = picks.length
    ? picks.reduce((s, p) => s + (p.entry ?? 0), 0) / picks.length
    : 0;
  const maxDrawdownFinal = maxDrawdown;

  const sustained =
    endReason === "profit_target"
    || (picks.length >= config.minBetsForSuccess
      && totalPnl >= config.profitTargetUsd
      && wins / Math.max(picks.length, 1) >= 0.5
      && endReason !== "stop_loss");

  return {
    strategy: { ...strategy },
    picks,
    endReason,
    sustained,
    metrics: {
      bets: picks.length,
      wins,
      losses,
      winRate: picks.length ? wins / picks.length : 0,
      totalPnl,
      peak,
      maxDrawdown: maxDrawdownFinal,
      avgEntry,
      finalBankroll: bankroll,
    },
  };
}

export function mutateStrategy(strategy, trial) {
  const next = {
    ...strategy,
    generation: (strategy.generation || 1) + 1,
    stakeUsd: strategy.stakeUsd ?? DEFAULT_STRATEGY.stakeUsd,
  };
  const m = trial.metrics;

  if (trial.endReason === "stop_loss") {
    next.stakeUsd = Math.max(5, next.stakeUsd - 2);
    next.minStreak = Math.min(8, next.minStreak + 1);
    next.requireConsensus = true;
    next.minConsensus = Math.max(2, next.minConsensus);
  }

  if (m.winRate < 0.48 && m.bets >= 5) {
    next.minHitRate = Math.min(0.75, +(next.minHitRate + 0.04).toFixed(2));
    next.maxEntryPrice = Math.max(0.5, +(next.maxEntryPrice - 0.05).toFixed(2));
  }

  if (m.avgEntry > 0.68) {
    next.maxEntryPrice = Math.max(0.45, +(next.maxEntryPrice - 0.08).toFixed(2));
  }

  if (m.bets < 5) {
    next.minStreak = Math.max(2, next.minStreak - 1);
    next.minHitRate = Math.max(0.45, +(next.minHitRate - 0.03).toFixed(2));
    next.requireConsensus = false;
    next.maxEntryPrice = Math.min(0.85, +(next.maxEntryPrice + 0.05).toFixed(2));
  }

  const modes = ["top_streak", "high_hit", "value", "consensus"];
  const idx = modes.indexOf(next.pickMode);
  next.pickMode = modes[(idx + 1) % modes.length];

  if (next.pickMode === "consensus") next.requireConsensus = true;

  return next;
}

export function runSimLoop(traders, config = DEFAULT_SIM_CONFIG, ignoreFavorites = true) {
  const trials = [];
  let strategy = { ...DEFAULT_STRATEGY, stakeUsd: config.stakeUsd };
  let winner = null;

  for (let i = 0; i < config.maxTrials; i++) {
    const trial = runTrial(strategy, traders, config, ignoreFavorites);
    trial.trialNum = i + 1;
    trials.push(trial);

    if (trial.sustained) {
      winner = trial;
      break;
    }
    strategy = mutateStrategy(strategy, trial);
  }

  return { trials, winner, finalStrategy: strategy };
}

function fmtStrategy(s) {
  return [
    `gen ${s.generation}`,
    `mode=${s.pickMode}`,
    `streak≥${s.minStreak}`,
    `hit≥${(s.minHitRate * 100).toFixed(0)}%`,
    `entry ${(s.minEntryPrice * 100).toFixed(0)}–${(s.maxEntryPrice * 100).toFixed(0)}¢`,
    s.requireConsensus ? `consensus≥${s.minConsensus}` : "solo ok",
    `$${s.stakeUsd}/bet`,
  ].join(" · ");
}

function endLabel(trial) {
  if (trial.sustained) return "SUSTAINED PROFIT";
  if (trial.endReason === "stop_loss") return "STOP LOSS";
  if (trial.endReason === "profit_target") return "PROFIT TARGET";
  return "COMPLETED";
}

export function formatSimMarkdown(result, config) {
  const lines = [
    "# StreakScope Sim Trader Log",
    "",
    `Generated: ${new Date().toISOString()}`,
    `Stop loss: $${config.stopLossUsd} · Profit target: $${config.profitTargetUsd} · Min bets: ${config.minBetsForSuccess}`,
    "",
  ];

  for (const trial of result.trials) {
    const m = trial.metrics;
    lines.push(`## Trial ${trial.trialNum} — ${endLabel(trial)} (${m.totalPnl >= 0 ? "+" : ""}$${m.totalPnl.toFixed(2)})`);
    lines.push("");
    lines.push(`**Strategy:** ${fmtStrategy(trial.strategy)}`);
    lines.push("");
    lines.push(`| Metric | Value |`);
    lines.push(`|--------|-------|`);
    lines.push(`| Bets | ${m.bets} |`);
    lines.push(`| Record | ${m.wins}W–${m.losses}L (${(m.winRate * 100).toFixed(0)}%) |`);
    lines.push(`| PnL | $${m.totalPnl.toFixed(2)} |`);
    lines.push(`| Peak | $${m.peak.toFixed(2)} |`);
    lines.push(`| Max drawdown | $${m.maxDrawdown.toFixed(2)} |`);
    lines.push(`| Avg entry | ${((m.avgEntry || 0) * 100).toFixed(1)}¢ |`);
    lines.push(`| End reason | ${trial.endReason} |`);
    lines.push("");

    if (trial.picks.length) {
      lines.push("<details><summary>Last picks</summary>");
      lines.push("");
      for (const p of trial.picks.slice(-8)) {
        lines.push(
          `- ${p.win ? "W" : "L"} ${p.title?.slice(0, 50)} @ ${((p.entry || 0) * 100).toFixed(0)}¢ · ${p.trader} (${p.streak}W, ${(p.hitRate * 100).toFixed(0)}% hit) → ${p.pnl >= 0 ? "+" : ""}$${p.pnl.toFixed(2)}`,
        );
      }
      lines.push("");
      lines.push("</details>");
      lines.push("");
    }

    if (trial.trialNum < result.trials.length) {
      const next = result.trials[trial.trialNum];
      if (next) {
        lines.push(`**Next tweak:** ${fmtStrategy(next.strategy)}`);
        lines.push("");
      }
    }
  }

  if (result.winner) {
    lines.push("---");
    lines.push("");
    lines.push(`## Winner — Trial ${result.winner.trialNum}`);
    lines.push("");
    lines.push(fmtStrategy(result.winner.strategy));
    lines.push("");
    lines.push(`Sustained PnL: +$${result.winner.metrics.totalPnl.toFixed(2)} over ${result.winner.metrics.bets} bets.`);
  } else {
    lines.push("---");
    lines.push("");
    lines.push(`No sustained-profit strategy found in ${result.trials.length} trials. Last attempt:`);
    lines.push("");
    lines.push(fmtStrategy(result.finalStrategy));
  }

  return lines.join("\n");
}

export function downloadMarkdown(content, filename = "streakscope-sim-log.md") {
  const blob = new Blob([content], { type: "text/markdown" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
