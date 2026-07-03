import { useState, useEffect, useCallback, useRef, useMemo } from "react";

const DATA_API = "https://data-api.polymarket.com";
const GAMMA_API = "https://gamma-api.polymarket.com";
const BATCH_SIZE = 4;
const GAMMA_CHUNK = 20;
const LEADERBOARD_LIMIT = 15;

const COLORS = {
  bg: "#0F1523",
  card: "#171F33",
  border: "#26304A",
  text: "#E8ECF4",
  muted: "#8B95A8",
  win: "#3DDC97",
  loss: "#FF5C5C",
  streakLow: "#D9A441",
  streakHigh: "#FF4B2E",
  live: "#3DDC97",
};

const SPORTS_RE =
  /\b(nba|nfl|nhl|mlb|wnba|ncaa|epl|premier league|la liga|serie a|bundesliga|ligue 1|mls|champions league|uefa|world cup|ufc|mma|boxing|f1|grand prix|nascar|tennis|atp|wta|wimbledon|pga|golf|cricket|ipl|rugby|super bowl|stanley cup|world series|playoff(?:s)?|finals)\b|\bvs\b/i;

const gammaCache = new Map();

function isSportsPosition(p) {
  const hay = [p.title, p.slug, p.eventSlug]
    .filter(Boolean)
    .join(" ")
    .replace(/-/g, " ");
  return SPORTS_RE.test(hay);
}

function isResolved(p) {
  return (
    p.redeemable === true ||
    (p.curPrice != null && (p.curPrice >= 0.999 || p.curPrice <= 0.001))
  );
}

function isWinResolved(p) {
  return p.redeemable === true || (p.curPrice != null && p.curPrice >= 0.999);
}

function isWinClosed(p) {
  return (p.realizedPnl ?? 0) > 0;
}

function hedgeExcludedIds(positions) {
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
  const da = new Date(a.endDate || a.timestamp * 1000 || 0).getTime();
  const db = new Date(b.endDate || b.timestamp * 1000 || 0).getTime();
  return db - da;
}

function computeStreak(resolved, ignoreFavorites) {
  const rows = [];
  for (const p of resolved) {
    const win =
      p.streakSource === "realized" ? isWinClosed(p) : isWinResolved(p);
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
  const last20 = rows.slice(0, 20).reverse();

  return {
    streak,
    streakType: firstType,
    hitRate: rows.length ? wins / rows.length : 0,
    resolvedCount: rows.length,
    avgEntry: rows.reduce((s, r) => s + r.avgPrice, 0) / rows.length,
    last20,
    streakSource: resolved[0]?.streakSource ?? "inferred",
  };
}

function computeTraderStats(seed, openSports, closedSports, ignoreFavorites) {
  const allForHedge = [...openSports, ...closedSports];
  const excluded = hedgeExcludedIds(allForHedge);
  const resolved = buildResolvedList(closedSports, openSports, excluded);
  const stats = computeStreak(resolved, ignoreFavorites);
  return { stats };
}

async function enrichActiveBets(activeSports, logDiag) {
  const condIds = [...new Set(activeSports.map((p) => p.conditionId).filter(Boolean))];
  const now = Date.now();
  const gammaMarkets = condIds.length ? await fetchGammaMarkets(condIds, logDiag) : [];
  const gammaById = new Map();
  condIds.forEach((id, idx) => gammaById.set(id, gammaMarkets[idx]));

  const activeBets = activeSports.map((p) => {
    const gm = gammaById.get(p.conditionId);
    const live = isLiveBet(p, gm, now);
    return { ...p, gameStartTime: gm?.gameStartTime ?? null, live };
  });
  activeBets.sort((a, b) => (b.live ? 1 : 0) - (a.live ? 1 : 0));
  return { activeBets, liveCount: activeBets.filter((b) => b.live).length };
}

function buildResolvedList(closedSports, openSports, excluded) {
  const closedFiltered = closedSports
    .filter((p) => !excluded.has(p.conditionId))
    .map((p) => ({ ...p, streakSource: "realized" }))
    .sort(sortByDateDesc);

  if (closedFiltered.length > 0) return closedFiltered;

  const inferred = openSports
    .filter((p) => !excluded.has(p.conditionId) && isResolved(p))
    .map((p) => ({ ...p, streakSource: "inferred" }))
    .sort(sortByDateDesc);

  return inferred;
}

function streakColor(n) {
  if (n < 3) return COLORS.streakLow;
  const t = Math.min((n - 3) / 7, 1);
  const r = Math.round(0xd9 + (0xff - 0xd9) * t);
  const g = Math.round(0xa4 + (0x4b - 0xa4) * t);
  const b = Math.round(0x41 + (0x2e - 0x41) * t);
  return `rgb(${r},${g},${b})`;
}

function fmtPrice(v) {
  if (v == null || Number.isNaN(v)) return "—";
  return `${(v * 100).toFixed(1)}¢`;
}

function fmtUsd(v) {
  if (v == null || Number.isNaN(v)) return "—";
  const abs = Math.abs(v);
  const sign = v < 0 ? "-" : "";
  if (abs >= 1_000_000) return `${sign}$${(abs / 1_000_000).toFixed(2)}M`;
  if (abs >= 1_000) return `${sign}$${(abs / 1_000).toFixed(1)}K`;
  return `${sign}$${abs.toFixed(2)}`;
}

function fmtPct(v) {
  if (v == null || Number.isNaN(v)) return "—";
  return `${(v * 100).toFixed(0)}%`;
}

async function fetchJson(url, logDiag, retries = 3) {
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const res = await fetch(url);
      if (res.status === 429 && attempt < retries) {
        const delay = Math.pow(2, attempt + 1) * 500;
        await new Promise((r) => setTimeout(r, delay));
        continue;
      }
      if (!res.ok) {
        logDiag(url, false, res.status, 0);
        return null;
      }
      const data = await res.json();
      const count = Array.isArray(data) ? data.length : data ? 1 : 0;
      logDiag(url, true, res.status, count);
      return data;
    } catch {
      if (attempt < retries) {
        await new Promise((r) => setTimeout(r, Math.pow(2, attempt + 1) * 500));
        continue;
      }
      logDiag(url, false, 0, 0);
      return null;
    }
  }
  return null;
}

async function fetchGammaMarkets(conditionIds, logDiag) {
  const missing = conditionIds.filter((id) => !gammaCache.has(id));
  const chunks = [];
  for (let i = 0; i < missing.length; i += GAMMA_CHUNK) {
    chunks.push(missing.slice(i, i + GAMMA_CHUNK));
  }

  let zeroHits = 0;
  for (const chunk of chunks) {
    const params = chunk.map((id) => `condition_ids=${encodeURIComponent(id)}`).join("&");
    const url = `${GAMMA_API}/markets?${params}`;
    const data = await fetchJson(url, logDiag);
    const markets = Array.isArray(data) ? data : [];
    const returned = new Set(markets.map((m) => m.conditionId));
    for (const id of chunk) {
      if (!returned.has(id)) {
        gammaCache.set(id, null);
        zeroHits++;
      }
    }
    for (const m of markets) {
      if (m.conditionId) gammaCache.set(m.conditionId, m);
    }
  }

  if (zeroHits > 0) {
    logDiag(`[gamma] ${zeroHits} conditionId(s) returned no market metadata`, true, 0, zeroHits);
  }

  return conditionIds.map((id) => gammaCache.get(id) ?? null);
}

function isLiveBet(position, gammaMarket, now) {
  if (isResolved(position)) return false;
  const gst = gammaMarket?.gameStartTime;
  if (!gst) return false;
  const start = new Date(gst).getTime();
  return !Number.isNaN(start) && start <= now;
}

function WLStrip({ last20 }) {
  if (!last20.length) return <span style={{ color: COLORS.muted, fontSize: 11 }}>no data</span>;
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
              flexShrink: 0,
            }}
          />
        );
      })}
    </div>
  );
}

function LiveBadge({ reducedMotion }) {
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 4,
        fontSize: 10,
        fontWeight: 700,
        letterSpacing: "0.06em",
        color: COLORS.live,
        fontFamily: "monospace",
      }}
    >
      <span
        style={{
          width: 6,
          height: 6,
          borderRadius: "50%",
          background: COLORS.live,
          animation: reducedMotion ? "none" : "pulse 1.4s ease-in-out infinite",
        }}
      />
      LIVE
    </span>
  );
}

export default function StreakScopeSports() {
  const [rawTraders, setRawTraders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(null);
  const [winStreaksOnly, setWinStreaksOnly] = useState(false);
  const [ignoreFavorites, setIgnoreFavorites] = useState(true);
  const [liveOnly, setLiveOnly] = useState(false);
  const [diagOpen, setDiagOpen] = useState(false);
  const [diagnostics, setDiagnostics] = useState([]);
  const [scanProgress, setScanProgress] = useState("");
  const [dataSource, setDataSource] = useState("live");
  const abortRef = useRef(null);
  const reducedMotion = useMemo(
    () => typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches,
    [],
  );

  const logDiag = useCallback((url, ok, status, count) => {
    const entry = {
      ts: new Date().toISOString().slice(11, 19),
      ok,
      status,
      count,
      url: typeof url === "string" ? url.replace(DATA_API, "").replace(GAMMA_API, "[gamma]") : url,
    };
    setDiagnostics((prev) => [entry, ...prev].slice(0, 200));
  }, []);

  const loadData = useCallback(async () => {
    if (abortRef.current) abortRef.current.aborted = true;
    const abort = { aborted: false };
    abortRef.current = abort;

    setLoading(true);
    setRawTraders([]);
    setDiagnostics([]);
    setScanProgress("Fetching leaderboard…");
    setDataSource("live");

    const lbUrl = `${DATA_API}/v1/leaderboard?category=SPORTS&timePeriod=MONTH&orderBy=PNL&limit=${LEADERBOARD_LIMIT}`;
    const leaderboard = await fetchJson(lbUrl, logDiag);
    if (abort.aborted) return;

    if (!leaderboard?.length) {
      setScanProgress("Leaderboard fetch failed");
      setLoading(false);
      return;
    }

    const seeds = leaderboard.map((t) => ({
      wallet: t.proxyWallet,
      name: t.userName || t.proxyWallet?.slice(0, 8),
      pnl: t.pnl,
      profileImage: t.profileImage,
    }));

    setScanProgress(`Scanning ${seeds.length} traders…`);

    for (let i = 0; i < seeds.length; i += BATCH_SIZE) {
      if (abort.aborted) return;
      const batch = seeds.slice(i, i + BATCH_SIZE);
      setScanProgress(`Batch ${Math.floor(i / BATCH_SIZE) + 1}/${Math.ceil(seeds.length / BATCH_SIZE)}…`);

      const results = await Promise.allSettled(
        batch.map(async (seed) => {
          const [openRaw, closedRaw] = await Promise.all([
            fetchJson(`${DATA_API}/positions?user=${seed.wallet}&limit=200`, logDiag),
            fetchJson(`${DATA_API}/closed-positions?user=${seed.wallet}&limit=200`, logDiag),
          ]);

          const openAll = Array.isArray(openRaw) ? openRaw : [];
          const closedAll = Array.isArray(closedRaw) ? closedRaw : [];
          const openSports = openAll.filter(isSportsPosition);
          const closedSports = closedAll.filter(isSportsPosition);
          const activeSports = openSports.filter((p) => !isResolved(p));
          const { activeBets, liveCount } = await enrichActiveBets(activeSports, logDiag);

          return {
            ...seed,
            openSports,
            closedSports,
            activeBets,
            liveCount,
          };
        }),
      );

      const newTraders = results
        .filter((r) => r.status === "fulfilled")
        .map((r) => r.value);

      if (!abort.aborted) {
        setRawTraders((prev) => [...prev, ...newTraders]);
      }
    }

    if (!abort.aborted) {
      setScanProgress("Done");
      setLoading(false);
    }
  }, [logDiag]);

  const traders = useMemo(() => {
    return rawTraders.map((t) => {
      const { stats } = computeTraderStats(t, t.openSports, t.closedSports, ignoreFavorites);
      return { ...t, ...stats };
    });
  }, [rawTraders, ignoreFavorites]);

  useEffect(() => {
    loadData();
    return () => {
      if (abortRef.current) abortRef.current.aborted = true;
    };
  }, [loadData]);

  const sorted = useMemo(() => {
    let list = [...traders];
    if (winStreaksOnly) list = list.filter((t) => t.streakType === "W" && t.streak > 0);
    list.sort((a, b) => {
      const aScore = a.streakType === "W" ? a.streak : 0;
      const bScore = b.streakType === "W" ? b.streak : 0;
      if (bScore !== aScore) return bScore - aScore;
      return (b.pnl ?? 0) - (a.pnl ?? 0);
    });
    return list;
  }, [traders, winStreaksOnly]);

  const totalLive = useMemo(
    () => traders.reduce((s, t) => s + (t.liveCount ?? 0), 0),
    [traders],
  );

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

  return (
    <div
      style={{
        minHeight: "100vh",
        background: COLORS.bg,
        color: COLORS.text,
        fontFamily: "'Inter', system-ui, sans-serif",
        padding: "12px 12px 80px",
        maxWidth: 900,
        margin: "0 auto",
      }}
    >
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.4; transform: scale(0.85); }
        }
        * { box-sizing: border-box; }
        button:focus-visible { outline: 2px solid ${COLORS.win}; outline-offset: 2px; }
      `}</style>

      <header style={{ marginBottom: 16 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 8 }}>
          <div>
            <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700, letterSpacing: "-0.02em" }}>
              StreakScope
            </h1>
            <p style={{ margin: "4px 0 0", fontSize: 12, color: COLORS.muted }}>
              Sports trader win streaks ·{" "}
              <span style={{ color: COLORS.win }}>{dataSource} data</span>
              {totalLive > 0 && (
                <>
                  {" · "}
                  <span style={{ fontFamily: "monospace", color: COLORS.live }}>{totalLive} live</span>
                </>
              )}
            </p>
          </div>
          <button
            type="button"
            onClick={loadData}
            disabled={loading}
            style={{
              ...toggleStyle(false),
              color: COLORS.text,
              opacity: loading ? 0.5 : 1,
            }}
          >
            {loading ? "↻ Scanning…" : "↻ Refresh"}
          </button>
        </div>

        <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 12 }}>
          <button type="button" style={toggleStyle(winStreaksOnly)} onClick={() => setWinStreaksOnly((v) => !v)}>
            Win streaks only
          </button>
          <button type="button" style={toggleStyle(ignoreFavorites)} onClick={() => setIgnoreFavorites((v) => !v)}>
            Ignore &gt;95¢ favorites
          </button>
          <button type="button" style={toggleStyle(liveOnly)} onClick={() => setLiveOnly((v) => !v)}>
            Live games only
          </button>
        </div>

        {scanProgress && (
          <p style={{ fontSize: 11, color: COLORS.muted, margin: "8px 0 0", fontFamily: "monospace" }}>
            {scanProgress}
          </p>
        )}
      </header>

      {sorted.length === 0 && !loading && (
        <div style={{ padding: 24, textAlign: "center", color: COLORS.muted }}>No traders loaded</div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {sorted.map((t) => {
          const isOpen = expanded === t.wallet;
          const streakActive = t.streakType === "W" && t.streak > 0;
          const glow = streakActive && t.streak >= 6;
          const bets = liveOnly ? t.activeBets.filter((b) => b.live) : t.activeBets;

          return (
            <div
              key={t.wallet}
              style={{
                background: COLORS.card,
                border: `1px solid ${COLORS.border}`,
                borderRadius: 10,
                overflow: "hidden",
                boxShadow: glow ? `0 0 20px ${streakColor(t.streak)}44` : "none",
              }}
            >
              <button
                type="button"
                onClick={() => setExpanded(isOpen ? null : t.wallet)}
                style={{
                  width: "100%",
                  display: "grid",
                  gridTemplateColumns: "auto 1fr auto",
                  gap: 12,
                  alignItems: "center",
                  padding: "12px 14px",
                  background: "transparent",
                  border: "none",
                  color: COLORS.text,
                  cursor: "pointer",
                  textAlign: "left",
                }}
              >
                <div
                  style={{
                    fontFamily: "monospace",
                    fontSize: 22,
                    fontWeight: 700,
                    color: streakActive ? streakColor(t.streak) : COLORS.muted,
                    minWidth: 44,
                    textAlign: "center",
                  }}
                >
                  {streakActive ? `${t.streak}W` : t.streakType === "L" ? `${t.streak}L` : "—"}
                </div>

                <div style={{ minWidth: 0 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                    <span style={{ fontWeight: 600, fontSize: 14 }}>{t.name}</span>
                    {t.streakSource === "inferred" && (
                      <span
                        style={{
                          fontSize: 10,
                          padding: "1px 6px",
                          borderRadius: 4,
                          background: "rgba(217,164,65,0.15)",
                          color: COLORS.streakLow,
                        }}
                      >
                        held-only
                      </span>
                    )}
                    {t.liveCount > 0 && <LiveBadge reducedMotion={reducedMotion} />}
                  </div>
                  <div style={{ marginTop: 6 }}>
                    <WLStrip last20={t.last20} />
                  </div>
                  <div
                    style={{
                      marginTop: 6,
                      fontSize: 11,
                      color: COLORS.muted,
                      fontFamily: "monospace",
                      display: "flex",
                      gap: 12,
                      flexWrap: "wrap",
                    }}
                  >
                    <span>hit {fmtPct(t.hitRate)}</span>
                    <span>{t.resolvedCount} resolved</span>
                    <span>avg entry {fmtPrice(t.avgEntry)}</span>
                    <span>pnl {fmtUsd(t.pnl)}</span>
                  </div>
                </div>

                <span style={{ color: COLORS.muted, fontSize: 18 }}>{isOpen ? "▾" : "▸"}</span>
              </button>

              {isOpen && (
                <div style={{ borderTop: `1px solid ${COLORS.border}`, padding: "8px 10px 12px", overflowX: "auto" }}>
                  {bets.length === 0 ? (
                    <p style={{ fontSize: 12, color: COLORS.muted, margin: 8 }}>No active bets{liveOnly ? " (live)" : ""}</p>
                  ) : (
                    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11, fontFamily: "monospace" }}>
                      <thead>
                        <tr style={{ color: COLORS.muted, textAlign: "left" }}>
                          <th style={{ padding: "4px 6px" }}>MARKET</th>
                          <th style={{ padding: "4px 6px" }}>SIDE</th>
                          <th style={{ padding: "4px 6px" }}>ENTRY</th>
                          <th style={{ padding: "4px 6px" }}>NOW</th>
                          <th style={{ padding: "4px 6px" }}>VALUE</th>
                          <th style={{ padding: "4px 6px" }}>PNL</th>
                          <th style={{ padding: "4px 6px" }}>ENDS</th>
                        </tr>
                      </thead>
                      <tbody>
                        {bets.map((b, i) => (
                          <tr key={i} style={{ borderTop: `1px solid ${COLORS.border}` }}>
                            <td style={{ padding: "6px", maxWidth: 180, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                              {b.live && (
                                <span style={{ marginRight: 6 }}>
                                  <LiveBadge reducedMotion={reducedMotion} />
                                </span>
                              )}
                              {b.title}
                            </td>
                            <td style={{ padding: "6px" }}>{b.outcome}</td>
                            <td style={{ padding: "6px" }}>{fmtPrice(b.avgPrice)}</td>
                            <td style={{ padding: "6px" }}>{fmtPrice(b.curPrice)}</td>
                            <td style={{ padding: "6px" }}>{fmtUsd(b.currentValue)}</td>
                            <td
                              style={{
                                padding: "6px",
                                color: (b.cashPnl ?? 0) >= 0 ? COLORS.win : COLORS.loss,
                              }}
                            >
                              {fmtUsd(b.cashPnl)}
                            </td>
                            <td style={{ padding: "6px", color: COLORS.muted }}>
                              {b.endDate ? new Date(b.endDate).toLocaleDateString() : "—"}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div
        style={{
          position: "fixed",
          bottom: 0,
          left: 0,
          right: 0,
          background: COLORS.card,
          borderTop: `1px solid ${COLORS.border}`,
          zIndex: 100,
        }}
      >
        <button
          type="button"
          onClick={() => setDiagOpen((v) => !v)}
          style={{
            width: "100%",
            padding: "10px 14px",
            background: "transparent",
            border: "none",
            color: COLORS.muted,
            fontSize: 12,
            cursor: "pointer",
            textAlign: "left",
            fontFamily: "monospace",
          }}
        >
          {diagOpen ? "▾" : "▸"} Diagnostics ({diagnostics.length} requests)
        </button>
        {diagOpen && (
          <div
            style={{
              maxHeight: 200,
              overflowY: "auto",
              padding: "0 10px 10px",
              fontFamily: "monospace",
              fontSize: 10,
            }}
          >
            {diagnostics.length === 0 && (
              <p style={{ color: COLORS.muted, margin: 4 }}>No requests yet</p>
            )}
            {diagnostics.map((d, i) => (
              <div
                key={i}
                style={{
                  padding: "3px 0",
                  borderBottom: `1px solid ${COLORS.border}`,
                  color: d.ok ? COLORS.text : COLORS.loss,
                }}
              >
                <span style={{ color: COLORS.muted }}>{d.ts}</span>{" "}
                {d.ok ? "✓" : "✗"} <span style={{ color: COLORS.muted }}>{d.status}</span>{" "}
                <span style={{ color: COLORS.win }}>×{d.count}</span>{" "}
                <span style={{ color: COLORS.muted, wordBreak: "break-all" }}>{d.url}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
