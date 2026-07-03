import { useState, useEffect, useCallback, useRef, useMemo } from "react";
import { COLORS } from "./lib/constants.js";
import { fmtPrice, fmtUsd, fmtPct, fmtSize, shortWallet, streakColor, profileUrl, marketUrl } from "./lib/format.js";
import { createLogger, clearGammaCache } from "./lib/api.js";
import {
  discoverWalletSeeds,
  enrichTradersProgressive,
  computeKpis,
  lookupWallet,
  enrichTrader,
  INITIAL_ENRICH,
} from "./lib/discovery.js";
import { computeTraderStats } from "./lib/sports.js";

function WLStrip({ last20 }) {
  if (!last20?.length) return <span style={{ color: COLORS.muted, fontSize: 11 }}>no data</span>;
  return (
    <div style={{ display: "flex", gap: 2, flexWrap: "wrap" }}>
      {last20.map((r, i) => {
        const opacity = 0.35 + (i / Math.max(last20.length - 1, 1)) * 0.65;
        return (
          <div
            key={i}
            title={`${r.win ? "W" : "L"} — ${r.title}`}
            style={{
              width: 10,
              height: 10,
              borderRadius: 2,
              background: r.win ? COLORS.win : COLORS.loss,
              opacity,
            }}
          />
        );
      })}
    </div>
  );
}

function LiveBadge({ reducedMotion, small }) {
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 4, fontSize: small ? 9 : 10, fontWeight: 700, letterSpacing: "0.06em", color: COLORS.live, fontFamily: "monospace" }}>
      <span style={{ width: small ? 5 : 6, height: small ? 5 : 6, borderRadius: "50%", background: COLORS.live, animation: reducedMotion ? "none" : "pulse 1.4s ease-in-out infinite" }} />
      LIVE
    </span>
  );
}

function KpiBar({ kpis }) {
  const items = [
    { label: "discovered", value: kpis.walletsDiscovered },
    { label: "enriched", value: kpis.walletsEnriched },
    { label: "live traders", value: kpis.liveTraders, highlight: true },
    { label: "live bets", value: kpis.liveBets, highlight: true },
    { label: "trades scanned", value: kpis.sportsTradesScanned },
    { label: "open exposure", value: fmtUsd(kpis.totalExposure) },
  ];
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(100px, 1fr))", gap: 8, marginBottom: 12 }}>
      {items.map((k) => (
        <div key={k.label} style={{ background: COLORS.card, border: `1px solid ${COLORS.border}`, borderRadius: 8, padding: "8px 10px" }}>
          <div style={{ fontSize: 10, color: COLORS.muted, textTransform: "uppercase", letterSpacing: "0.05em" }}>{k.label}</div>
          <div style={{ fontFamily: "monospace", fontSize: 16, fontWeight: 700, color: k.highlight ? COLORS.live : COLORS.text, marginTop: 2 }}>{k.value}</div>
        </div>
      ))}
    </div>
  );
}

function BetCard({ bet, trader, reducedMotion }) {
  const url = bet.polymarketUrl || marketUrl(bet);
  const pnl = bet.cashPnl ?? 0;
  const pnlPct = bet.percentPnl ?? ((bet.curPrice - bet.avgPrice) / (bet.avgPrice || 1)) * 100;

  return (
    <div style={{ background: "rgba(15,21,35,0.6)", border: `1px solid ${bet.live ? COLORS.live : COLORS.border}`, borderRadius: 8, padding: 10, marginBottom: 8 }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 8, alignItems: "flex-start" }}>
        <div style={{ minWidth: 0, flex: 1 }}>
          <div style={{ display: "flex", gap: 6, alignItems: "center", flexWrap: "wrap", marginBottom: 4 }}>
            {bet.live && <LiveBadge reducedMotion={reducedMotion} small />}
            <span style={{ fontSize: 10, padding: "1px 6px", borderRadius: 4, background: "rgba(108,140,255,0.15)", color: COLORS.accent, fontFamily: "monospace" }}>
              {bet.outcome}
            </span>
            {bet.sportsMarketType && (
              <span style={{ fontSize: 10, color: COLORS.muted }}>{bet.sportsMarketType}</span>
            )}
          </div>
          {url ? (
            <a href={url} target="_blank" rel="noopener noreferrer" style={{ color: COLORS.text, textDecoration: "none", fontSize: 13, fontWeight: 600, lineHeight: 1.3 }}>
              {bet.title}
            </a>
          ) : (
            <div style={{ fontSize: 13, fontWeight: 600 }}>{bet.title}</div>
          )}
        </div>
        <div style={{ textAlign: "right", fontFamily: "monospace", flexShrink: 0 }}>
          <div style={{ color: pnl >= 0 ? COLORS.win : COLORS.loss, fontWeight: 700 }}>{fmtUsd(pnl)}</div>
          <div style={{ fontSize: 10, color: COLORS.muted }}>{typeof pnlPct === "number" ? `${pnlPct >= 0 ? "+" : ""}${pnlPct.toFixed(1)}%` : ""}</div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8, marginTop: 10, fontFamily: "monospace", fontSize: 11 }}>
        <div>
          <div style={{ color: COLORS.muted, fontSize: 9 }}>ENTRY → NOW</div>
          <div>{fmtPrice(bet.avgPrice)} → {fmtPrice(bet.curPrice)}</div>
        </div>
        <div>
          <div style={{ color: COLORS.muted, fontSize: 9 }}>SIZE</div>
          <div>{fmtSize(bet.size)} shares</div>
        </div>
        <div>
          <div style={{ color: COLORS.muted, fontSize: 9 }}>VALUE</div>
          <div>{fmtUsd(bet.currentValue)}</div>
        </div>
        <div>
          <div style={{ color: COLORS.muted, fontSize: 9 }}>TRADER</div>
          <a href={profileUrl(trader.wallet)} target="_blank" rel="noopener noreferrer" style={{ color: COLORS.accent, textDecoration: "none" }}>
            {trader.name || shortWallet(trader.wallet)}
          </a>
        </div>
      </div>

      {bet.gameStartTime && (
        <div style={{ marginTop: 6, fontSize: 10, color: COLORS.muted }}>
          Game: {new Date(bet.gameStartTime).toLocaleString()}
        </div>
      )}
    </div>
  );
}

function TraderMeta({ t }) {
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 8, fontSize: 10, color: COLORS.muted, fontFamily: "monospace", marginTop: 4 }}>
      {t.portfolioValue != null && <span>portfolio {fmtUsd(t.portfolioValue)}</span>}
      {t.openExposure > 0 && <span>open {fmtUsd(t.openExposure)}</span>}
      {t.unrealizedPnl != null && (
        <span style={{ color: t.unrealizedPnl >= 0 ? COLORS.win : COLORS.loss }}>
          unrealized {fmtUsd(t.unrealizedPnl)}
        </span>
      )}
      {t.dayPnl != null && (
        <span style={{ color: t.dayPnl >= 0 ? COLORS.win : COLORS.loss }}>today {fmtUsd(t.dayPnl)}</span>
      )}
      {t.tradedCount != null && <span>{t.tradedCount} mkts</span>}
      {t.takerTier != null && <span>tier {t.takerTier}</span>}
      {t.xUsername && <span>@{t.xUsername}</span>}
      {t.verifiedBadge && <span style={{ color: COLORS.win }}>✓ verified</span>}
      {t.source && <span style={{ opacity: 0.7 }}>via {t.source}</span>}
    </div>
  );
}

function TraderRow({ t, expanded, onToggle, liveOnly, reducedMotion }) {
  const isOpen = expanded === t.wallet;
  const streakActive = t.streakType === "W" && t.streak > 0;
  const glow = streakActive && t.streak >= 6;
  const bets = liveOnly ? (t.activeBets || []).filter((b) => b.live) : (t.activeBets || []);

  return (
    <div style={{ background: COLORS.card, border: `1px solid ${COLORS.border}`, borderRadius: 10, overflow: "hidden", boxShadow: glow ? `0 0 20px ${streakColor(t.streak, COLORS)}44` : "none" }}>
      <button
        type="button"
        onClick={() => onToggle(isOpen ? null : t.wallet)}
        style={{ width: "100%", display: "grid", gridTemplateColumns: "auto 1fr auto", gap: 12, alignItems: "center", padding: "12px 14px", background: "transparent", border: "none", color: COLORS.text, cursor: "pointer", textAlign: "left" }}
      >
        <div style={{ fontFamily: "monospace", fontSize: 22, fontWeight: 700, color: streakActive ? streakColor(t.streak, COLORS) : COLORS.muted, minWidth: 44, textAlign: "center" }}>
          {streakActive ? `${t.streak}W` : t.streakType === "L" ? `${t.streak}L` : "—"}
        </div>
        <div style={{ minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
            <a href={t.profileUrl || profileUrl(t.wallet)} target="_blank" rel="noopener noreferrer" onClick={(e) => e.stopPropagation()} style={{ fontWeight: 600, fontSize: 14, color: COLORS.text, textDecoration: "none" }}>
              {t.name}
            </a>
            {t.streakSource === "inferred" && (
              <span style={{ fontSize: 10, padding: "1px 6px", borderRadius: 4, background: "rgba(217,164,65,0.15)", color: COLORS.streakLow }}>held-only</span>
            )}
            {t.liveCount > 0 && <LiveBadge reducedMotion={reducedMotion} />}
            {t.whaleTrade && (
              <span style={{ fontSize: 10, padding: "1px 6px", borderRadius: 4, background: "rgba(199,125,255,0.15)", color: COLORS.whale }}>🐋 whale</span>
            )}
          </div>
          {t.bio && <div style={{ fontSize: 11, color: COLORS.muted, marginTop: 2 }}>{t.bio}</div>}
          <div style={{ marginTop: 6 }}><WLStrip last20={t.last20} /></div>
          <div style={{ marginTop: 6, fontSize: 11, color: COLORS.muted, fontFamily: "monospace", display: "flex", gap: 12, flexWrap: "wrap" }}>
            <span>hit {fmtPct(t.hitRate)}</span>
            <span>{t.resolvedCount} resolved</span>
            <span>avg entry {fmtPrice(t.avgEntry)}</span>
            {t.pnl != null && <span>pnl {fmtUsd(t.pnl)}</span>}
          </div>
          <TraderMeta t={t} />
        </div>
        <span style={{ color: COLORS.muted, fontSize: 18 }}>{isOpen ? "▾" : "▸"}</span>
      </button>
      {isOpen && (
        <div style={{ borderTop: `1px solid ${COLORS.border}`, padding: "8px 12px 12px" }}>
          <div style={{ fontSize: 10, color: COLORS.muted, fontFamily: "monospace", marginBottom: 8 }}>
            {shortWallet(t.wallet)}
            {t.createdAt && ` · joined ${new Date(t.createdAt).toLocaleDateString()}`}
          </div>
          {bets.length === 0 ? (
            <p style={{ fontSize: 12, color: COLORS.muted }}>No active bets{liveOnly ? " (live)" : ""}</p>
          ) : (
            bets.map((b, i) => <BetCard key={i} bet={b} trader={t} reducedMotion={reducedMotion} />)
          )}
        </div>
      )}
    </div>
  );
}

function SamePlaySection({ groups }) {
  if (!groups?.length) return null;
  return (
    <section style={{ marginBottom: 16 }}>
      <h2 style={{ fontSize: 14, margin: "0 0 8px", color: COLORS.accent }}>👥 Same Play — streakers on the same side</h2>
      {groups.map((g, i) => (
        <div key={i} style={{ background: COLORS.card, border: `1px solid ${g.live ? COLORS.live : COLORS.border}`, borderRadius: 8, padding: 10, marginBottom: 8 }}>
          <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 8 }}>
            {g.live && <LiveBadge reducedMotion />}
            <span style={{ fontWeight: 600, fontSize: 13 }}>{g.title}</span>
            <span style={{ fontSize: 11, padding: "1px 6px", borderRadius: 4, background: "rgba(108,140,255,0.15)", color: COLORS.accent }}>{g.outcome}</span>
            <span style={{ fontSize: 11, color: COLORS.muted, marginLeft: "auto" }}>{g.wallets.length} traders</span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {g.wallets.map((w, j) => (
              <div key={j} style={{ display: "flex", justifyContent: "space-between", fontSize: 11, fontFamily: "monospace" }}>
                <a href={profileUrl(w.wallet)} target="_blank" rel="noopener noreferrer" style={{ color: COLORS.text, textDecoration: "none" }}>
                  {w.name || shortWallet(w.wallet)}
                  {w.streak >= 3 ? ` · ${w.streak}W streak` : ""}
                  {w.live ? " · LIVE" : ""}
                </a>
                <span>
                  {fmtPrice(w.entry)} → {fmtPrice(w.now)} · {fmtUsd(w.pnl)}
                </span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </section>
  );
}

export default function StreakScopeSports() {
  const [rawTraders, setRawTraders] = useState([]);
  const [kpis, setKpis] = useState({});
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(null);
  const [view, setView] = useState("pulse");
  const [winStreaksOnly, setWinStreaksOnly] = useState(false);
  const [ignoreFavorites, setIgnoreFavorites] = useState(true);
  const [liveOnly, setLiveOnly] = useState(false);
  const [diagOpen, setDiagOpen] = useState(false);
  const [diagnostics, setDiagnostics] = useState([]);
  const [scanProgress, setScanProgress] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResult, setSearchResult] = useState(null);
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
    setKpis({});
    setDiagnostics([]);
    clearGammaCache();
    setScanProgress("Discovering wallets across chain…");

    const { seeds, tradeCount } = await discoverWalletSeeds(logDiag, setScanProgress);
    if (abort.aborted) return;

    metaRef.current = { seedCount: seeds.length, tradeCount };
    setScanProgress(`Enriching top ${Math.min(seeds.length, INITIAL_ENRICH)} of ${seeds.length} wallets…`);

    await enrichTradersProgressive(
      seeds,
      logDiag,
      ignoreFavorites,
      (batch, done, total) => {
        if (abort.aborted) return;
        setRawTraders((prev) => {
          const merged = new Map(prev.map((t) => [t.wallet, t]));
          for (const t of batch) merged.set(t.wallet, t);
          const list = [...merged.values()];
          setKpis(computeKpis(list, metaRef.current));
          return list;
        });
        setScanProgress(`Enriched ${done}/${total} wallets…`);
      },
      abort,
    );

    if (!abort.aborted) {
      setScanProgress("Scan complete");
      setLoading(false);
    }
  }, [logDiag, ignoreFavorites]);

  useEffect(() => {
    loadData();
    return () => { if (abortRef.current) abortRef.current.aborted = true; };
  }, [loadData]);

  const traders = useMemo(() => {
    return rawTraders.map((t) => {
      const stats = computeTraderStats(t.openSports, t.closedSports, ignoreFavorites);
      return { ...t, ...stats };
    });
  }, [rawTraders, ignoreFavorites]);

  const pulseTraders = useMemo(() => {
    const ids = new Set();
    const add = (list) => { for (const t of list || []) ids.add(t.wallet); };
    add(kpis.hotStreaks?.filter((t) => t.liveCount > 0));
    add(kpis.bigMovers?.filter((t) => t.liveCount > 0 || Math.abs(t.dayPnl ?? 0) > 10000));
    add(kpis.whales);
    for (const g of kpis.samePlay || []) {
      for (const w of g.wallets) {
        const t = traders.find((x) => x.wallet === w.wallet);
        if (t) ids.add(t.wallet);
      }
    }
    const live = traders.filter((t) => t.liveCount > 0);
    for (const t of live.slice(0, 20)) ids.add(t.wallet);
    return traders.filter((t) => ids.has(t.wallet));
  }, [traders, kpis]);

  const sorted = useMemo(() => {
    let list = view === "pulse" ? [...pulseTraders] : [...traders];
    if (winStreaksOnly) list = list.filter((t) => t.streakType === "W" && t.streak > 0);
    if (liveOnly) list = list.filter((t) => t.liveCount > 0);
    list.sort((a, b) => {
      if (liveOnly || view === "pulse") {
        const liveDiff = (b.liveCount ?? 0) - (a.liveCount ?? 0);
        if (liveDiff) return liveDiff;
      }
      const aScore = a.streakType === "W" ? a.streak : 0;
      const bScore = b.streakType === "W" ? b.streak : 0;
      if (bScore !== aScore) return bScore - aScore;
      return Math.abs(b.dayPnl ?? b.unrealizedPnl ?? 0) - Math.abs(a.dayPnl ?? a.unrealizedPnl ?? 0);
    });
    return list;
  }, [traders, pulseTraders, view, winStreaksOnly, liveOnly]);

  const handleSearch = async () => {
    setSearchResult(null);
    const seed = await lookupWallet(searchQuery, logDiag);
    if (!seed) { setSearchResult({ error: "No wallet or username found" }); return; }
    setScanProgress(`Looking up ${seed.name || seed.wallet}…`);
    const trader = await enrichTrader(seed, logDiag, ignoreFavorites);
    setSearchResult(trader);
    setRawTraders((prev) => {
      const merged = new Map(prev.map((t) => [t.wallet, t]));
      merged.set(trader.wallet, trader);
      const list = [...merged.values()];
      setKpis(computeKpis(list, metaRef.current));
      return list;
    });
    setScanProgress("");
  };

  const toggleStyle = (on) => ({
    padding: "6px 12px",
    borderRadius: 6,
    border: `1px solid ${on ? COLORS.win : COLORS.border}`,
    background: on ? "rgba(61,220,151,0.12)" : COLORS.card,
    color: on ? COLORS.win : COLORS.muted,
    fontSize: 12,
    cursor: "pointer",
    fontFamily: "inherit",
  });

  const tabStyle = (on) => ({
    ...toggleStyle(on),
    fontWeight: on ? 700 : 400,
    color: on ? COLORS.text : COLORS.muted,
  });

  return (
    <div style={{ minHeight: "100vh", background: COLORS.bg, color: COLORS.text, fontFamily: "'Inter', system-ui, sans-serif", padding: "12px 12px 80px", maxWidth: 960, margin: "0 auto" }}>
      <style>{`
        @keyframes pulse { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.4; transform: scale(0.85); } }
        * { box-sizing: border-box; }
        a:hover { text-decoration: underline !important; }
        button:focus-visible { outline: 2px solid ${COLORS.win}; outline-offset: 2px; }
        input:focus-visible { outline: 2px solid ${COLORS.accent}; outline-offset: 1px; }
      `}</style>

      <header style={{ marginBottom: 12 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 8 }}>
          <div>
            <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700 }}>StreakScope</h1>
            <p style={{ margin: "4px 0 0", fontSize: 12, color: COLORS.muted }}>
              Blockchain sports pulse · <span style={{ color: COLORS.win }}>live APIs</span>
            </p>
          </div>
          <button type="button" onClick={loadData} disabled={loading} style={{ ...toggleStyle(false), color: COLORS.text, opacity: loading ? 0.5 : 1 }}>
            {loading ? "↻ Scanning…" : "↻ Refresh"}
          </button>
        </div>

        <KpiBar kpis={kpis} />

        <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 8 }}>
          <button type="button" style={tabStyle(view === "pulse")} onClick={() => setView("pulse")}>⚡ Live Pulse</button>
          <button type="button" style={tabStyle(view === "explore")} onClick={() => setView("explore")}>🔍 Explore All</button>
          <button type="button" style={tabStyle(view === "search")} onClick={() => setView("search")}>⌕ Search</button>
        </div>

        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
          <button type="button" style={toggleStyle(winStreaksOnly)} onClick={() => setWinStreaksOnly((v) => !v)}>Win streaks only</button>
          <button type="button" style={toggleStyle(ignoreFavorites)} onClick={() => setIgnoreFavorites((v) => !v)}>Ignore &gt;95¢ favorites</button>
          <button type="button" style={toggleStyle(liveOnly)} onClick={() => setLiveOnly((v) => !v)}>Live games only</button>
        </div>

        {scanProgress && (
          <p style={{ fontSize: 11, color: COLORS.muted, margin: "8px 0 0", fontFamily: "monospace" }}>{scanProgress}</p>
        )}
      </header>

      {view === "search" && (
        <div style={{ marginBottom: 16, display: "flex", gap: 8 }}>
          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            placeholder="Wallet 0x… or username"
            style={{ flex: 1, padding: "8px 12px", borderRadius: 6, border: `1px solid ${COLORS.border}`, background: COLORS.card, color: COLORS.text, fontSize: 13 }}
          />
          <button type="button" onClick={handleSearch} style={{ ...toggleStyle(true), color: COLORS.win }}>Search</button>
        </div>
      )}

      {view === "search" && searchResult?.error && (
        <p style={{ color: COLORS.loss, fontSize: 13 }}>{searchResult.error}</p>
      )}

      {view === "search" && searchResult && !searchResult.error && (
        <div style={{ marginBottom: 16 }}>
          <TraderRow t={searchResult} expanded={expanded} onToggle={setExpanded} liveOnly={liveOnly} reducedMotion={reducedMotion} />
        </div>
      )}

      {view === "pulse" && (
        <>
          <SamePlaySection groups={kpis.samePlay} />
          {kpis.hotStreaks?.length > 0 && (
            <section style={{ marginBottom: 12 }}>
              <h2 style={{ fontSize: 14, margin: "0 0 8px", color: COLORS.streakHigh }}>🔥 Hot Streaks</h2>
              <div style={{ fontSize: 11, color: COLORS.muted, marginBottom: 8, fontFamily: "monospace" }}>
                {kpis.hotStreaks.slice(0, 5).map((t) => `${t.name} (${t.streak}W)`).join(" · ")}
              </div>
            </section>
          )}
          {kpis.bigMovers?.length > 0 && (
            <section style={{ marginBottom: 12 }}>
              <h2 style={{ fontSize: 14, margin: "0 0 8px", color: COLORS.whale }}>💰 Biggest Movers Today</h2>
              <div style={{ fontSize: 11, color: COLORS.muted, marginBottom: 8, fontFamily: "monospace" }}>
                {kpis.bigMovers.slice(0, 5).map((t) => `${t.name} (${fmtUsd(t.dayPnl ?? t.unrealizedPnl)})`).join(" · ")}
              </div>
            </section>
          )}
        </>
      )}

      {sorted.length === 0 && !loading && (
        <div style={{ padding: 24, textAlign: "center", color: COLORS.muted }}>
          {view === "pulse" ? "No live pulse signals yet — try Explore All or refresh" : "No traders loaded"}
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {sorted.map((t) => (
          <TraderRow key={t.wallet} t={t} expanded={expanded} onToggle={setExpanded} liveOnly={liveOnly} reducedMotion={reducedMotion} />
        ))}
      </div>

      <div style={{ position: "fixed", bottom: 0, left: 0, right: 0, background: COLORS.card, borderTop: `1px solid ${COLORS.border}`, zIndex: 100 }}>
        <button type="button" onClick={() => setDiagOpen((v) => !v)} style={{ width: "100%", padding: "10px 14px", background: "transparent", border: "none", color: COLORS.muted, fontSize: 12, cursor: "pointer", textAlign: "left", fontFamily: "monospace" }}>
          {diagOpen ? "▾" : "▸"} Diagnostics ({diagnostics.length} requests)
        </button>
        {diagOpen && (
          <div style={{ maxHeight: 200, overflowY: "auto", padding: "0 10px 10px", fontFamily: "monospace", fontSize: 10 }}>
            {diagnostics.map((d, i) => (
              <div key={i} style={{ padding: "3px 0", borderBottom: `1px solid ${COLORS.border}`, color: d.ok ? COLORS.text : COLORS.loss }}>
                <span style={{ color: COLORS.muted }}>{d.ts}</span> {d.ok ? "✓" : "✗"} <span style={{ color: COLORS.muted }}>{d.status}</span> <span style={{ color: COLORS.win }}>×{d.count}</span> <span style={{ color: COLORS.muted, wordBreak: "break-all" }}>{d.url}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
