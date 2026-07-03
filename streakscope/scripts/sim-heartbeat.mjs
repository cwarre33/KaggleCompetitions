#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { discoverWalletSeeds, enrichTradersProgressive } from "../src/lib/discovery.js";
import { pollRecentTrades } from "../src/lib/alerts.js";
import { computeTraderStats } from "../src/lib/sports.js";
import { createInitialState, loadState, runLiveHeartbeat } from "../src/lib/simLive.js";
import { formatLiveStateMarkdown } from "../src/lib/simTrader.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");
const DATA_DIR = path.join(ROOT, "data");
const STATE_PATH = path.join(DATA_DIR, "sim-state.json");
const LOG_PATH = path.join(DATA_DIR, "sim-log.md");
const HEARTBEAT_ENRICH = 40;

const logDiag = (url, ok, status, count) => {
  const tag = ok ? "✓" : "✗";
  const short = typeof url === "string" ? url.replace("https://data-api.polymarket.com", "") : url;
  console.log(`${tag} ${short} (${count ?? 0})`);
};

async function readState() {
  try {
    const raw = await fs.readFile(STATE_PATH, "utf8");
    return loadState(JSON.parse(raw));
  } catch {
    return createInitialState();
  }
}

async function writeOutputs(state) {
  await fs.mkdir(DATA_DIR, { recursive: true });
  await fs.writeFile(STATE_PATH, `${JSON.stringify(state, null, 2)}\n`);
  await fs.writeFile(LOG_PATH, `${formatLiveStateMarkdown(state)}\n`);
}

async function main() {
  console.log("StreakScope sim heartbeat");
  const state = await readState();

  const { seeds } = await discoverWalletSeeds(logDiag, (msg) => console.log(msg));
  const limited = seeds.slice(0, HEARTBEAT_ENRICH);
  console.log(`Enriching ${limited.length} wallets…`);

  const traders = [];
  await enrichTradersProgressive(
    limited,
    logDiag,
    state.ignoreFavorites,
    (batch) => {
      for (const t of batch) traders.push(t);
    },
    { aborted: false },
  );

  const withStats = traders.map((t) => ({
    ...t,
    ...computeTraderStats(t.openSports, t.closedSports, state.ignoreFavorites),
  }));

  const trades = await pollRecentTrades(logDiag);
  const summary = await runLiveHeartbeat(state, withStats, trades, logDiag);

  await writeOutputs(state);

  console.log("Done:", JSON.stringify(summary));
  console.log(`State → ${STATE_PATH}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
