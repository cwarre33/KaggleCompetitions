import { useState, useEffect, useCallback, useRef, useMemo } from "react";
import { COLORS } from "./lib/constants.js";
import { fmtPrice, fmtUsd, fmtPct, fmtSize, shortWallet, streakColor, profileUrl, marketUrl } from "./lib/format.js";
import { createLogger, clearGammaCache } from "./lib/api.js";
import {
  discoverWalletSeeds,
  enrichTradersProgressive,
  lookupWallet,
  enrichTrader,
  INITIAL_ENRICH,
  buildGameBoard,
} from "./lib/discovery.js";
import { computeTraderStats } from "./lib/sports.js";
import { useStreakerAlerts } from "./hooks/useStreakerAlerts.js";
import { useSimFeed } from "./hooks/useSimFeed.js";
import { trialMetrics, fmtStrategy } from "./lib/simTrader.js";
import { ALERT_WINDOW_MS } from "./lib/alerts.js";

const PAGES = [
  { id: "live", label: "Live" },
  { id: "games", label: "Games" },
  { id: "streaks", label: "Streaks" },
  { id: "sim", label: "Sim" },
  { id: "alerts", label: "Alerts" },
  { id: "search", label: "Search" },
];

// ─── shared UI ───────────────────────────────────────────────

function WLStrip({ last20 }) {
  if (!last20?.length) return <span style={{ color: COLORS.muted, fontSize: 11 }}>—</span>;
  return (
    <div style={{ display: "flex", gap: 2 }}>
      {last20.map((r, i) => (
        <div
          key={i}
          title={`${r.win ? "W" : "L"} — ${r.title}`}
          style={{
            width: 10, height: 10, borderRadius: 2,
            background: r.win ? COLORS.win : COLORS.loss,
            opacity: 0.35 + (i / Math.max(last20.length - 1, 1)) * 0.65,
          }}
        />
      ))}
    </div>
  );
}

function LiveBadge({ reducedMotion, small }) {
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 4, fontSize: small ? 9 : 10, fontWeight: 700, color: COLORS.live, fontFamily: "monospace" }}>
      <span style={{ width: small ? 5 : 6, height: small ? 5 : 6, borderRadius: "50%", background: COLORS.live, animation: reducedMotion ? "none" : "pulse 1.4s ease-in-out infinite" }} />
      LIVE
    </span>
  );
}

function PageHeader({ title, desc, children }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <h2 style={{ margin: 0, fontSize: 18, fontWeight: 700 }}>{title}</h2>
      {desc && <p style={{ margin: "4px 0 0", fontSize: 13, color: COLORS.muted }}>{desc}</p>}
      {children && <div style={{ marginTop: 12 }}>{children}</div>}
    </div>
  );
}

function Empty({ children }) {
  return <div style={{ padding: 32, textAlign: "center", color: COLORS.muted, fontSize: 14 }}>{children}</div>;
}

function BetCard({ bet, trader, reducedMotion }) {
  const url = bet.polymarketUrl || marketUrl(bet);
  const pnl = bet.cashPnl ?? 0;

  return (
    <div style={{ background: COLORS.bg, border: `1px solid ${bet.live ? COLORS.live : COLORS.border}`, borderRadius: 8, padding: 10, marginBottom: 8 }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
        <div style={{ minWidth: 0 }}>
          <div style={{ display: "flex", gap: 6, alignItems: "center", marginBottom: 4 }}>
            {bet.live && <LiveBadge reducedMotion={reducedMotion} />}
            <span style={{ fontSize: 10, padding: "1px 6px", borderRadius: 4, background: "rgba(108,140,255,0.15)", color: COLORS.accent }}>{bet.outcome}</span>
          </div>
          {url ? (
            <a href={url} target="_blank" rel="noopener noreferrer" style={{ color: COLORS.text, fontWeight: 600, fontSize: 13, textDecoration: "none" }}>{bet.title}</a>
          ) : (
            <div style={{ fontWeight: 600, fontSize: 13 }}>{bet.title}</div>
          )}
        </div>
        <div style={{ fontFamily: "monospace", textAlign: "right", color: pnl >= 0 ? COLORS.win : COLORS.loss, fontWeight: 700 }}>{fmtUsd(pnl)}</div>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8, marginTop: 8, fontSize: 11, fontFamily: "monospace", color: COLORS.muted }}>
        <span>{fmtPrice(bet.avgPrice)} → {fmtPrice(bet.curPrice)}</span>
        <span>{fmtSize(bet.size)} sh · {fmtUsd(bet.currentValue)}</span>
        <a href={profileUrl(trader.wallet)} target="_blank" rel="noopener noreferrer" style={{ color: COLORS.accent, textDecoration: "none", textAlign: "right" }}>{trader.name}</a>
      </div>
    </div>
  );
}

function TraderRow({ t, expanded, onToggle, betsFilter, reducedMotion, compact }) {
  const isOpen = expanded === t.wallet;
  const streakActive = t.streakType === "W" && t.streak > 0;
  const bets = (t.activeBets || []).filter(betsFilter || (() => true));

  return (
    <div style={{ background: COLORS.card, border: `1px solid ${COLORS.border}`, borderRadius: 10, overflow: "hidden" }}>
      <button
        type="button"
        onClick={() => onToggle(isOpen ? null : t.wallet)}
        style={{ width: "100%", display: "grid", gridTemplateColumns: "auto 1fr auto", gap: 12, padding: "12px 14px", background: "transparent", border: "none", color: COLORS.text, cursor: "pointer", textAlign: "left" }}
      >
        <div style={{ fontFamily: "monospace", fontSize: 20, fontWeight: 700, color: streakActive ? streakColor(t.streak, COLORS) : COLORS.muted, minWidth: 40, textAlign: "center" }}>
          {streakActive ? `${t.streak}W` : t.streakType === "L" ? `${t.streak}L` : "—"}
        </div>
        <div style={{ minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontWeight: 600, fontSize: 14 }}>{t.name}</span>
            {t.liveCount > 0 && <LiveBadge reducedMotion={reducedMotion} />}
          </div>
          {!compact && <div style={{ marginTop: 6 }}><WLStrip last20={t.last20} /></div>}
          <div style={{ marginTop: 4, fontSize: 11, color: COLORS.muted, fontFamily: "monospace" }}>
            {fmtPct(t.hitRate)} hit · {t.resolvedCount} bets · avg {fmtPrice(t.avgEntry)}
            {t.dayPnl != null && <> · today <span style={{ color: t.dayPnl >= 0 ? COLORS.win : COLORS.loss }}>{fmtUsd(t.dayPnl)}</span></>}
          </div>
        </div>
        <span style={{ color: COLORS.muted }}>{isOpen ? "▾" : "▸"}</span>
      </button>
      {isOpen && (
        <div style={{ borderTop: `1px solid ${COLORS.border}`, padding: "8px 12px 12px" }}>
          <div style={{ fontSize: 10, color: COLORS.muted, fontFamily: "monospace", marginBottom: 8 }}>
            <a href={profileUrl(t.wallet)} target="_blank" rel="noopener noreferrer" style={{ color: COLORS.accent }}>{shortWallet(t.wallet)}</a>
            {t.portfolioValue != null && <> · portfolio {fmtUsd(t.portfolioValue)}</>}
          </div>
          {bets.length === 0 ? (
            <p style={{ fontSize: 12, color: COLORS.muted, margin: 0 }}>No bets here</p>
          ) : (
            bets.map((b, i) => <BetCard key={i} bet={b} trader={t} reducedMotion={reducedMotion} />)
          )}
        </div>
      )}
    </div>
  );
}

function AlertCard({ alert, onDismiss, reducedMotion }) {
  const url = alert.eventSlug ? `https://polymarket.com/event/${alert.eventSlug}` : null;
  const spanMin = Math.round(ALERT_WINDOW_MS / 60000);

  return (
    <div style={{ background: COLORS.card, border: `1px solid ${COLORS.streakHigh}`, borderRadius: 10, padding: 12, marginBottom: 8, animation: reducedMotion ? "none" : "alertPop 0.3s ease-out" }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
        <div>
          <div style={{ fontSize: 10, color: COLORS.streakHigh, fontWeight: 700, marginBottom: 4 }}>SAME PLAY · {spanMin} MIN</div>
          {url ? (
            <a href={url} target="_blank" rel="noopener noreferrer" style={{ color: COLORS.text, fontWeight: 600, fontSize: 14, textDecoration: "none" }}>{alert.title}</a>
          ) : (
            <div style={{ fontWeight: 600, fontSize: 14 }}>{alert.title}</div>
          )}
          <div style={{ fontSize: 12, color: COLORS.accent, marginTop: 2 }}>{alert.outcome}</div>
        </div>
        <button type="button" onClick={() => onDismiss(alert.id)} style={{ background: "none", border: "none", color: COLORS.muted, cursor: "pointer", fontSize: 18 }}>×</button>
      </div>
      <div style={{ marginTop: 10, display: "flex", flexDirection: "column", gap: 4 }}>
        {alert.traders.map((tr) => (
          <div key={tr.wallet} style={{ display: "flex", justifyContent: "space-between", fontSize: 11, fontFamily: "monospace" }}>
            <a href={profileUrl(tr.wallet)} target="_blank" rel="noopener noreferrer" style={{ color: COLORS.text, textDecoration: "none" }}>
              <span style={{ color: streakColor(tr.streak, COLORS) }}>{tr.streak}W</span> {tr.name || shortWallet(tr.wallet)}
            </a>
            <span style={{ color: COLORS.muted }}>{new Date(tr.at).toLocaleTimeString()} · {fmtPrice(tr.price)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── pages ─────────────────────────────────────────────────

function GamesPage({ games, expanded, onToggle, reducedMotion, loading, liveOnly, setLiveOnly }) {
  const list = liveOnly ? games.filter((g) => g.live) : games;
  const btn = (on, label, fn) => (
    <button type="button" onClick={fn} style={{ padding: "6px 12px", borderRadius: 6, border: `1px solid ${on ? COLORS.live : COLORS.border}`, background: on ? "rgba(61,220,151,0.1)" : "transparent", color: on ? COLORS.live : COLORS.muted, fontSize: 12, cursor: "pointer" }}>
      {label}
    </button>
  );

  return (
    <>
      <PageHeader title="Games" desc={`${list.length} games · streakers' positions grouped by matchup`}>
        {games.length > 0 && btn(liveOnly, "Live games only", () => setLiveOnly(!liveOnly))}
      </PageHeader>
      {loading && <Empty>Loading games…</Empty>}
      {!loading && list.length === 0 && <Empty>No streaker positions on active games.</Empty>}
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {list.map((g) => {
          const open = expanded === g.eventKey;
          const url = g.eventSlug ? `https://polymarket.com/event/${g.eventSlug}` : null;
          return (
            <div key={g.eventKey} style={{ background: COLORS.card, border: `1px solid ${g.live ? COLORS.live : COLORS.border}`, borderRadius: 10, overflow: "hidden" }}>
              <button
                type="button"
                onClick={() => onToggle(open ? null : g.eventKey)}
                style={{ width: "100%", display: "grid", gridTemplateColumns: "1fr auto", gap: 8, padding: "12px 14px", background: "transparent", border: "none", color: COLORS.text, cursor: "pointer", textAlign: "left" }}
              >
                <div>
                  <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
                    {g.live && <LiveBadge reducedMotion={reducedMotion} />}
                    {url ? (
                      <a href={url} target="_blank" rel="noopener noreferrer" onClick={(e) => e.stopPropagation()} style={{ fontWeight: 600, fontSize: 14, color: COLORS.text, textDecoration: "none" }}>
                        {g.title}
                      </a>
                    ) : (
                      <span style={{ fontWeight: 600, fontSize: 14 }}>{g.title}</span>
                    )}
                  </div>
                  <div style={{ marginTop: 4, fontSize: 11, color: COLORS.muted, fontFamily: "monospace" }}>
                    {g.streakerCount} streakers · {g.positionCount} markets
                    {g.gameStartTime && <> · {new Date(g.gameStartTime).toLocaleString()}</>}
                  </div>
                </div>
                <span style={{ color: COLORS.muted, alignSelf: "center" }}>{open ? "▾" : "▸"}</span>
              </button>
              {open && (
                <div style={{ borderTop: `1px solid ${COLORS.border}`, padding: "8px 12px 12px" }}>
                  {g.positions.map((pos) => (
                    <div key={pos.conditionId + pos.outcome} style={{ marginBottom: 12 }}>
                      <div style={{ display: "flex", gap: 6, alignItems: "center", marginBottom: 6 }}>
                        {pos.live && <LiveBadge reducedMotion={reducedMotion} small />}
                        <span style={{ fontSize: 10, padding: "1px 6px", borderRadius: 4, background: "rgba(108,140,255,0.15)", color: COLORS.accent }}>{pos.outcome}</span>
                        {pos.sportsMarketType && <span style={{ fontSize: 10, color: COLORS.muted }}>{pos.sportsMarketType}</span>}
                      </div>
                      {pos.polymarketUrl ? (
                        <a href={pos.polymarketUrl} target="_blank" rel="noopener noreferrer" style={{ fontSize: 12, fontWeight: 600, color: COLORS.text, textDecoration: "none" }}>{pos.title}</a>
                      ) : (
                        <div style={{ fontSize: 12, fontWeight: 600 }}>{pos.title}</div>
                      )}
                      <div style={{ marginTop: 6, display: "flex", flexDirection: "column", gap: 4 }}>
                        {pos.traders.map((tr) => (
                          <div key={tr.wallet} style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 8, fontSize: 11, fontFamily: "monospace", padding: "6px 8px", background: COLORS.bg, borderRadius: 6 }}>
                            <a href={profileUrl(tr.wallet)} target="_blank" rel="noopener noreferrer" style={{ color: COLORS.text, textDecoration: "none" }}>
                              <span style={{ color: streakColor(tr.streak, COLORS), fontWeight: 700 }}>{tr.streak}W</span> {tr.name}
                            </a>
                            <span style={{ color: COLORS.muted, textAlign: "right" }}>
                              {fmtPrice(tr.entry)} → {fmtPrice(tr.now)} · <span style={{ color: (tr.pnl ?? 0) >= 0 ? COLORS.win : COLORS.loss }}>{fmtUsd(tr.pnl)}</span>
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </>
  );
}

function LivePage({ traders, expanded, onToggle, reducedMotion, loading }) {
  const live = traders.filter((t) => t.liveCount > 0).sort((a, b) => b.liveCount - a.liveCount);
  const liveBets = live.reduce((s, t) => s + t.liveCount, 0);

  return (
    <>
      <PageHeader title="Live" desc={`${live.length} traders · ${liveBets} in-game bets right now`} />
      {loading && <Empty>Scanning…</Empty>}
      {!loading && live.length === 0 && <Empty>No live game bets right now. Check back during game time.</Empty>}
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {live.map((t) => (
          <TraderRow
            key={t.wallet}
            t={t}
            expanded={expanded}
            onToggle={onToggle}
            betsFilter={(b) => b.live}
            reducedMotion={reducedMotion}
            compact
          />
        ))}
      </div>
    </>
  );
}

function StreaksPage({ traders, expanded, onToggle, reducedMotion, loading, ignoreFavorites, setIgnoreFavorites, winOnly, setWinOnly }) {
  let list = [...traders];
  if (winOnly) list = list.filter((t) => t.streakType === "W" && t.streak > 0);
  list.sort((a, b) => {
    const as = a.streakType === "W" ? a.streak : 0;
    const bs = b.streakType === "W" ? b.streak : 0;
    if (bs !== as) return bs - as;
    return (b.pnl ?? 0) - (a.pnl ?? 0);
  });

  const btn = (on, label, fn) => (
    <button type="button" onClick={fn} style={{ padding: "6px 12px", borderRadius: 6, border: `1px solid ${on ? COLORS.win : COLORS.border}`, background: on ? "rgba(61,220,151,0.1)" : "transparent", color: on ? COLORS.win : COLORS.muted, fontSize: 12, cursor: "pointer" }}>
      {label}
    </button>
  );

  return (
    <>
      <PageHeader title="Streaks" desc="Sports traders ranked by current win streak">
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {btn(winOnly, "Win streaks only", () => setWinOnly(!winOnly))}
          {btn(ignoreFavorites, "Skip 95¢ favorites", () => setIgnoreFavorites(!ignoreFavorites))}
        </div>
      </PageHeader>
      {loading && <Empty>Loading traders…</Empty>}
      {!loading && list.length === 0 && <Empty>No streak data yet.</Empty>}
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {list.map((t) => (
          <TraderRow key={t.wallet} t={t} expanded={expanded} onToggle={onToggle} reducedMotion={reducedMotion} />
        ))}
      </div>
    </>
  );
}

function AlertsPage({
  alerts, watching, alertsEnabled, setAlertsEnabled, browserNotify, enableBrowserNotify, setBrowserNotify,
  dismissAlert, clearAlerts, reducedMotion, loading,
}) {
  const btn = (on, label, fn) => (
    <button type="button" onClick={fn} style={{ padding: "6px 12px", borderRadius: 6, border: `1px solid ${on ? COLORS.win : COLORS.border}`, background: on ? "rgba(61,220,151,0.1)" : "transparent", color: on ? COLORS.win : COLORS.muted, fontSize: 12, cursor: "pointer" }}>
      {label}
    </button>
  );

  return (
    <>
      <PageHeader title="Alerts" desc="When 2+ streakers (3W+) buy the same side within 5 minutes">
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {btn(alertsEnabled, alertsEnabled ? "Monitoring on" : "Monitoring off", () => setAlertsEnabled(!alertsEnabled))}
          {btn(browserNotify, browserNotify ? "Push on" : "Enable push", browserNotify ? () => setBrowserNotify(false) : enableBrowserNotify)}
          {alerts.length > 0 && btn(false, "Clear all", clearAlerts)}
        </div>
        {alertsEnabled && !loading && (
          <p style={{ fontSize: 11, color: COLORS.muted, margin: "8px 0 0", fontFamily: "monospace" }}>
            Watching {watching} streakers · polls every 30s
          </p>
        )}
      </PageHeader>
      {loading && <Empty>Waiting for trader scan…</Empty>}
      {!loading && alerts.length === 0 && <Empty>No alerts yet. Keep this page open during games.</Empty>}
      {alerts.map((a) => <AlertCard key={a.id} alert={a} onDismiss={dismissAlert} reducedMotion={reducedMotion} />)}
    </>
  );
}

function SimTrialCard({ trial, isWinner, isActive }) {
  const m = trial.metrics || trialMetrics(trial);
  const label = isActive
    ? "LIVE"
    : trial.sustained
      ? "SUSTAINED"
      : trial.endReason === "stop_loss"
        ? "STOP LOSS"
        : "ENDED";
  const border = isActive ? COLORS.live : isWinner ? COLORS.win : trial.endReason === "stop_loss" ? COLORS.loss : COLORS.border;

  return (
    <div style={{ background: COLORS.card, border: `1px solid ${border}`, borderRadius: 10, padding: 12, marginBottom: 8 }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 8, marginBottom: 6 }}>
        <span style={{ fontSize: 10, fontWeight: 700, color: isActive ? COLORS.live : isWinner ? COLORS.win : trial.endReason === "stop_loss" ? COLORS.loss : COLORS.muted }}>
          TRIAL {trial.trialNum} · {label}
        </span>
        <span style={{ fontFamily: "monospace", fontWeight: 700, color: m.totalPnl >= 0 ? COLORS.win : COLORS.loss }}>
          {m.totalPnl >= 0 ? "+" : ""}{fmtUsd(m.totalPnl)}
        </span>
      </div>
      <div style={{ fontSize: 11, color: COLORS.muted, fontFamily: "monospace", marginBottom: 8 }}>
        {fmtStrategy(trial.strategy)}
      </div>
      <div style={{ fontSize: 11, fontFamily: "monospace", color: COLORS.text }}>
        {m.closed} closed · {m.open} open · {m.wins}W–{m.losses}L ({fmtPct(m.winRate)})
        {m.unrealizedPnl !== 0 && <> · open {fmtUsd(m.unrealizedPnl)}</>}
      </div>
      {(trial.openPicks?.length > 0) && (
        <div style={{ marginTop: 8, fontSize: 10, color: COLORS.muted }}>
          Open: {trial.openPicks.slice(0, 3).map((p) => `${p.outcome} ${(p.title || "").slice(0, 24)}`).join(" · ")}
        </div>
      )}
      {(trial.closedPicks?.length > 0 || trial.picks?.length > 0) && (
        <div style={{ marginTop: 8, fontSize: 10, color: COLORS.muted }}>
          Last: {(trial.closedPicks || trial.picks).slice(-3).map((p) => `${p.win ? "W" : "L"} ${(p.title || "").slice(0, 28)}`).join(" · ")}
        </div>
      )}
    </div>
  );
}

function SimPage({ simLoading, simError, state, logMd, onRefresh }) {
  const active = state?.currentTrial;
  const archived = [...(state?.archivedTrials || [])].reverse();

  return (
    <>
      <PageHeader
        title="Sim Trader"
        desc="GitHub Actions heartbeat follows live streaker trades, paper-bets, and rotates strategies on stop-loss."
      />
      {simLoading && <Empty>Loading sim feed…</Empty>}
      {simError && !state && <Empty>Sim feed unavailable — {simError}</Empty>}
      {state && (
        <>
          <div style={{ display: "flex", gap: 8, marginBottom: 12, flexWrap: "wrap", alignItems: "center" }}>
            <button type="button" onClick={onRefresh}
              style={{ padding: "8px 12px", borderRadius: 6, border: `1px solid ${COLORS.border}`, background: COLORS.card, color: COLORS.text, fontSize: 12, cursor: "pointer" }}>
              Refresh
            </button>
            <span style={{ fontSize: 11, color: COLORS.muted, fontFamily: "monospace" }}>
              ♥ {state.heartbeatCount} · updated {new Date(state.updatedAt).toLocaleString()}
            </span>
          </div>
          <p style={{ fontSize: 11, color: COLORS.muted, margin: "0 0 12px", fontFamily: "monospace" }}>
            {state.lastHeartbeatNote} · stop ${state.config.stopLossUsd} / target ${state.config.profitTargetUsd} / ${state.config.stakeUsd} per bet
          </p>
          {state.winner && (
            <div style={{ padding: 12, marginBottom: 12, borderRadius: 8, border: `1px solid ${COLORS.win}`, background: "rgba(61,220,151,0.08)" }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: COLORS.win }}>Champion — Trial {state.winner.trialNum}</div>
              <div style={{ fontSize: 11, marginTop: 4, fontFamily: "monospace", color: COLORS.muted }}>
                {fmtStrategy(state.winner.strategy)}
              </div>
            </div>
          )}
          {active?.status === "active" && (
            <>
              <div style={{ fontSize: 12, fontWeight: 700, color: COLORS.live, marginBottom: 8 }}>Active strategy</div>
              <SimTrialCard trial={active} isActive />
            </>
          )}
          {archived.length > 0 && (
            <>
              <div style={{ fontSize: 12, fontWeight: 700, color: COLORS.muted, margin: "16px 0 8px" }}>Past strategies</div>
              {archived.map((t) => (
                <SimTrialCard key={`${t.trialNum}-${t.endedAt}`} trial={t} isWinner={state.winner?.trialNum === t.trialNum} />
              ))}
            </>
          )}
          {logMd && (
            <details style={{ marginTop: 12 }}>
              <summary style={{ fontSize: 12, color: COLORS.muted, cursor: "pointer" }}>Repo log (sim-log.md)</summary>
              <pre style={{ marginTop: 8, padding: 12, background: COLORS.card, borderRadius: 8, fontSize: 10, overflow: "auto", maxHeight: 280, color: COLORS.muted, whiteSpace: "pre-wrap" }}>
                {logMd}
              </pre>
            </details>
          )}
        </>
      )}
    </>
  );
}

function SearchPage({ searchQuery, setSearchQuery, onSearch, searchResult, expanded, onToggle, reducedMotion }) {
  return (
    <>
      <PageHeader title="Search" desc="Look up any wallet or Polymarket username" />
      <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
        <input
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && onSearch()}
          placeholder="0x… or username"
          style={{ flex: 1, padding: "10px 12px", borderRadius: 8, border: `1px solid ${COLORS.border}`, background: COLORS.card, color: COLORS.text, fontSize: 14 }}
        />
        <button type="button" onClick={onSearch} style={{ padding: "10px 16px", borderRadius: 8, border: `1px solid ${COLORS.win}`, background: "rgba(61,220,151,0.1)", color: COLORS.win, fontSize: 14, cursor: "pointer" }}>
          Go
        </button>
      </div>
      {searchResult?.error && <p style={{ color: COLORS.loss }}>{searchResult.error}</p>}
      {searchResult && !searchResult.error && (
        <TraderRow t={searchResult} expanded={expanded} onToggle={onToggle} reducedMotion={reducedMotion} />
      )}
    </>
  );
}

// ─── app shell ─────────────────────────────────────────────

export default function StreakScopeSports() {
  const [rawTraders, setRawTraders] = useState([]);
  const [page, setPage] = useState("live");
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(null);
  const [ignoreFavorites, setIgnoreFavorites] = useState(true);
  const [winOnly, setWinOnly] = useState(false);
  const [gamesLiveOnly, setGamesLiveOnly] = useState(false);
  const [diagOpen, setDiagOpen] = useState(false);
  const [diagnostics, setDiagnostics] = useState([]);
  const [scanProgress, setScanProgress] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResult, setSearchResult] = useState(null);
  const [alertsEnabled, setAlertsEnabled] = useState(true);
  const [browserNotify, setBrowserNotify] = useState(false);
  const abortRef = useRef(null);
  const metaRef = useRef({});

  const reducedMotion = useMemo(
    () => typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches,
    [],
  );

  const logDiag = useCallback(createLogger(setDiagnostics), []);

  const loadData = useCallback(async () => {
    if (abortRef.current) abortRef.current.aborted = true;
    const abort = { aborted: false };
    abortRef.current = abort;
    setLoading(true);
    setRawTraders([]);
    setDiagnostics([]);
    clearGammaCache();
    setScanProgress("Scanning…");

    const { seeds, tradeCount } = await discoverWalletSeeds(logDiag, setScanProgress);
    if (abort.aborted) return;
    metaRef.current = { seedCount: seeds.length, tradeCount };

    await enrichTradersProgressive(seeds, logDiag, ignoreFavorites, (batch, done, total) => {
      if (abort.aborted) return;
      setRawTraders((prev) => {
        const m = new Map(prev.map((t) => [t.wallet, t]));
        for (const t of batch) m.set(t.wallet, t);
        return [...m.values()];
      });
      setScanProgress(`${done}/${total}`);
    }, abort);

    if (!abort.aborted) { setScanProgress(""); setLoading(false); }
  }, [logDiag, ignoreFavorites]);

  useEffect(() => {
    loadData();
    return () => { if (abortRef.current) abortRef.current.aborted = true; };
  }, [loadData]);

  const traders = useMemo(() => rawTraders.map((t) => ({
    ...t,
    ...computeTraderStats(t.openSports, t.closedSports, ignoreFavorites),
  })), [rawTraders, ignoreFavorites]);

  const { alerts, unread, watching, dismissAlert, clearAlerts, requestPermission, markRead } = useStreakerAlerts({
    traders, logDiag, enabled: alertsEnabled && !loading, browserNotify,
  });

  const sim = useSimFeed();

  const goPage = (id) => {
    setPage(id);
    if (id === "alerts") markRead();
  };

  const enableBrowserNotify = async () => {
    setBrowserNotify((await requestPermission()) === "granted");
  };

  const handleSearch = async () => {
    setSearchResult(null);
    const seed = await lookupWallet(searchQuery, logDiag);
    if (!seed) { setSearchResult({ error: "Not found" }); return; }
    const trader = await enrichTrader(seed, logDiag, ignoreFavorites);
    setSearchResult(trader);
    setRawTraders((prev) => {
      const m = new Map(prev.map((t) => [t.wallet, t]));
      m.set(trader.wallet, trader);
      return [...m.values()];
    });
  };

  const liveCount = traders.filter((t) => t.liveCount > 0).length;

  const games = useMemo(() => buildGameBoard(traders), [traders]);
  const liveGameCount = games.filter((g) => g.live).length;

  return (
    <div style={{ minHeight: "100vh", background: COLORS.bg, color: COLORS.text, fontFamily: "system-ui, sans-serif", maxWidth: 720, margin: "0 auto" }}>
      <style>{`
        @keyframes pulse { 50% { opacity: 0.4; } }
        @keyframes alertPop { from { opacity: 0; transform: translateY(-4px); } }
        * { box-sizing: border-box; }
        a:hover { text-decoration: underline !important; }
      `}</style>

      {/* top bar */}
      <header style={{ position: "sticky", top: 0, zIndex: 50, background: COLORS.bg, borderBottom: `1px solid ${COLORS.border}`, padding: "12px 16px 0" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
          <div>
            <div style={{ fontSize: 18, fontWeight: 700 }}>StreakScope</div>
            <div style={{ fontSize: 11, color: COLORS.muted }}>
              {loading ? scanProgress || "loading…" : `${traders.length} traders · ${liveCount} live`}
            </div>
          </div>
          <button type="button" onClick={loadData} disabled={loading} style={{ padding: "6px 12px", borderRadius: 6, border: `1px solid ${COLORS.border}`, background: COLORS.card, color: COLORS.text, fontSize: 12, cursor: "pointer", opacity: loading ? 0.5 : 1 }}>
            Refresh
          </button>
        </div>

        <nav style={{ display: "flex", gap: 0 }}>
          {PAGES.map((p) => {
            const active = page === p.id;
            const badge =
              p.id === "alerts" && unread > 0 ? unread
              : p.id === "live" && liveCount > 0 ? liveCount
              : p.id === "games" && liveGameCount > 0 ? liveGameCount
              : 0;
            return (
              <button
                key={p.id}
                type="button"
                onClick={() => goPage(p.id)}
                style={{
                  flex: 1, padding: "10px 4px", border: "none", background: "transparent",
                  borderBottom: active ? `2px solid ${COLORS.win}` : "2px solid transparent",
                  color: active ? COLORS.text : COLORS.muted,
                  fontWeight: active ? 700 : 400, fontSize: 13, cursor: "pointer",
                }}
              >
                {p.label}
                {badge > 0 && (
                  <span style={{ marginLeft: 4, fontSize: 10, padding: "1px 5px", borderRadius: 8, background: p.id === "alerts" ? COLORS.streakHigh : COLORS.live, color: COLORS.bg, fontWeight: 700 }}>
                    {badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </header>

      {/* page content */}
      <main style={{ padding: "16px 16px 72px" }}>
        {page === "live" && <LivePage traders={traders} expanded={expanded} onToggle={setExpanded} reducedMotion={reducedMotion} loading={loading} />}
        {page === "games" && (
          <GamesPage
            games={games}
            expanded={expanded}
            onToggle={setExpanded}
            reducedMotion={reducedMotion}
            loading={loading}
            liveOnly={gamesLiveOnly}
            setLiveOnly={setGamesLiveOnly}
          />
        )}
        {page === "streaks" && (
          <StreaksPage
            traders={traders} expanded={expanded} onToggle={setExpanded} reducedMotion={reducedMotion} loading={loading}
            ignoreFavorites={ignoreFavorites} setIgnoreFavorites={setIgnoreFavorites}
            winOnly={winOnly} setWinOnly={setWinOnly}
          />
        )}
        {page === "sim" && (
          <SimPage
            simLoading={sim.loading}
            simError={sim.error}
            state={sim.state}
            logMd={sim.logMd}
            onRefresh={sim.refresh}
          />
        )}
        {page === "alerts" && (
          <AlertsPage
            alerts={alerts} watching={watching} alertsEnabled={alertsEnabled} setAlertsEnabled={setAlertsEnabled}
            browserNotify={browserNotify} enableBrowserNotify={enableBrowserNotify} setBrowserNotify={setBrowserNotify}
            dismissAlert={dismissAlert} clearAlerts={clearAlerts} reducedMotion={reducedMotion} loading={loading}
          />
        )}
        {page === "search" && (
          <SearchPage
            searchQuery={searchQuery} setSearchQuery={setSearchQuery} onSearch={handleSearch}
            searchResult={searchResult} expanded={expanded} onToggle={setExpanded} reducedMotion={reducedMotion}
          />
        )}
      </main>

      {/* diagnostics — tucked away */}
      <footer style={{ position: "fixed", bottom: 0, left: 0, right: 0, background: COLORS.card, borderTop: `1px solid ${COLORS.border}` }}>
        <button type="button" onClick={() => setDiagOpen((v) => !v)} style={{ width: "100%", maxWidth: 720, margin: "0 auto", display: "block", padding: "8px 16px", background: "transparent", border: "none", color: COLORS.muted, fontSize: 11, cursor: "pointer", textAlign: "left", fontFamily: "monospace" }}>
          {diagOpen ? "▾" : "▸"} API log ({diagnostics.length})
        </button>
        {diagOpen && (
          <div style={{ maxWidth: 720, margin: "0 auto", maxHeight: 140, overflowY: "auto", padding: "0 16px 8px", fontFamily: "monospace", fontSize: 10 }}>
            {diagnostics.map((d, i) => (
              <div key={i} style={{ color: d.ok ? COLORS.muted : COLORS.loss }}>
                {d.ts} {d.ok ? "✓" : "✗"} ×{d.count} {d.url}
              </div>
            ))}
          </div>
        )}
      </footer>
    </div>
  );
}
