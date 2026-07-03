export function fmtPrice(v) {
  if (v == null || Number.isNaN(v)) return "—";
  return `${(v * 100).toFixed(1)}¢`;
}

export function fmtUsd(v) {
  if (v == null || Number.isNaN(v)) return "—";
  const abs = Math.abs(v);
  const sign = v < 0 ? "-" : "";
  if (abs >= 1_000_000) return `${sign}$${(abs / 1_000_000).toFixed(2)}M`;
  if (abs >= 1_000) return `${sign}$${(abs / 1_000).toFixed(1)}K`;
  return `${sign}$${abs.toFixed(2)}`;
}

export function fmtPct(v) {
  if (v == null || Number.isNaN(v)) return "—";
  return `${(v * 100).toFixed(0)}%`;
}

export function fmtSize(v) {
  if (v == null || Number.isNaN(v)) return "—";
  if (v >= 1000) return `${(v / 1000).toFixed(1)}K`;
  return v.toFixed(0);
}

export function shortWallet(w) {
  if (!w) return "—";
  return `${w.slice(0, 6)}…${w.slice(-4)}`;
}

export function streakColor(n, colors) {
  if (n < 3) return colors.streakLow;
  const t = Math.min((n - 3) / 7, 1);
  const r = Math.round(0xd9 + (0xff - 0xd9) * t);
  const g = Math.round(0xa4 + (0x4b - 0xa4) * t);
  const b = Math.round(0x41 + (0x2e - 0x41) * t);
  return `rgb(${r},${g},${b})`;
}

export function profileUrl(wallet) {
  return `https://polymarket.com/profile/${wallet}`;
}

export function marketUrl(bet) {
  if (bet.eventSlug) return `https://polymarket.com/event/${bet.eventSlug}`;
  if (bet.slug) return `https://polymarket.com/event/${bet.slug}`;
  return null;
}

export function txUrl(hash) {
  if (!hash) return null;
  return `https://polygonscan.com/tx/${hash}`;
}
