import { DATA_API, GAMMA_API, GAMMA_CHUNK } from "./constants.js";

const gammaCache = new Map();

export function createLogger(setDiagnostics) {
  return (url, ok, status, count) => {
    const entry = {
      ts: new Date().toISOString().slice(11, 19),
      ok,
      status,
      count,
      url: typeof url === "string"
        ? url.replace(DATA_API, "").replace(GAMMA_API, "[gamma]")
        : url,
    };
    setDiagnostics((prev) => [entry, ...prev].slice(0, 300));
  };
}

export async function fetchJson(url, logDiag, retries = 3) {
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const res = await fetch(url);
      if (res.status === 429 && attempt < retries) {
        await new Promise((r) => setTimeout(r, Math.pow(2, attempt + 1) * 500));
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

export async function fetchGammaMarkets(conditionIds, logDiag) {
  const missing = conditionIds.filter((id) => !gammaCache.has(id));
  for (let i = 0; i < missing.length; i += GAMMA_CHUNK) {
    const chunk = missing.slice(i, i + GAMMA_CHUNK);
    const params = chunk.map((id) => `condition_ids=${encodeURIComponent(id)}`).join("&");
    const data = await fetchJson(`${GAMMA_API}/markets?${params}`, logDiag);
    const markets = Array.isArray(data) ? data : [];
    const returned = new Set(markets.map((m) => m.conditionId));
    for (const id of chunk) {
      if (!returned.has(id)) gammaCache.set(id, null);
    }
    for (const m of markets) {
      if (m.conditionId) gammaCache.set(m.conditionId, m);
    }
  }
  return conditionIds.map((id) => gammaCache.get(id) ?? null);
}

export async function fetchProfile(wallet, logDiag) {
  return fetchJson(`${GAMMA_API}/public-profile?address=${wallet}`, logDiag);
}

export async function fetchValue(wallet, logDiag) {
  const data = await fetchJson(`${DATA_API}/value?user=${wallet}`, logDiag);
  return Array.isArray(data) ? data[0]?.value ?? null : null;
}

export async function fetchTradedCount(wallet, logDiag) {
  const data = await fetchJson(`${DATA_API}/traded?user=${wallet}`, logDiag);
  return data?.traded ?? null;
}

export function clearGammaCache() {
  gammaCache.clear();
}
