# StreakScope

Rank Polymarket sports traders by current win streak. Shows recent W/L history and active bets with live-game detection.

## Stack

- Vite + React (static SPA)
- Polymarket public APIs (no auth, no backend)

## Development

```bash
npm install
npm run dev
```

## Build

```bash
npm run build
```

Output in `dist/`.

## Deploy

Static deploy of `dist/` to Vercel, Netlify, or GitHub Pages. `vercel.json` included for SPA routing.

## Data sources

- Leaderboard: `data-api.polymarket.com/v1/leaderboard`
- Positions: `data-api.polymarket.com/positions`
- Closed positions: `data-api.polymarket.com/closed-positions`
- Market metadata: `gamma-api.polymarket.com/markets`
