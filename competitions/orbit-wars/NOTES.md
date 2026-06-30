# Orbit Wars — Working Notes

## Competition facts
- https://www.kaggle.com/competitions/orbit-wars — $5,000 × top 10 places
- Entry deadline **June 16, 2026**; final submission **June 23, 2026** (11:59 PM UTC)
- Ladder format: TrueSkill-like rating (μ0=600), 5 submissions/day, only latest 2 tracked
- Validation episode = agent vs copies of itself (must not error)
- Submit: `kaggle competitions submit orbit-wars -f main.py -m "msg"`
- Monitor: `kaggle competitions submissions orbit-wars`, `kaggle competitions episodes <SUB_ID>`,
  `kaggle competitions replay <EPISODE_ID>`, `kaggle competitions logs <EPISODE_ID> <agent_idx>`
- Leaderboard: `kaggle competitions leaderboard orbit-wars -s`
- Token: reuse `../ARC-AGI-3-Kaggle-Starter/.kaggle/access_token` (KAGGLE_API_TOKEN env var)

## Game mechanics (from engine source: .venv/.../envs/orbit_wars/orbit_wars.py)
- 100×100 board, sun r=10 at (50,50) kills crossing fleets. 500 turns. Score = total ships.
- Turn order: comet expire/spawn → fleet launch → production → fleet move (continuous
  swept collision) → planet rotation/comet move → combat.
- Capture needs STRICTLY more than garrison (production added before movement, so
  arrival-turn production counts). Tied top-two attackers annihilate each other.
- Orbiting planets: orbital_r + radius < 50; pos = rotate(initial, av * step). av ∈ [0.025, 0.05].
- Fleet speed = 1 + 5·(ln(ships)/ln(1000))^1.5, capped 6. Bigger = faster.
- Neutral planets don't produce. Map: 5–10 groups of 4, 4-fold rotational symmetry.
- Comets: spawn steps 50,150,250,350,450; prod 1; leave board (ships on them die).
- actTimeout = 1s/turn + overage budget. Our agent ~34ms/turn. debug=True locally.
- Built-in agents: `random`, `starter` (floods half garrison at nearest static planet, ≥20 only).

## Agent lineage (versions/)
- v1_value_sniper: targeted captures, beat random 2-0, lost to starter 2-4.
- v2 "economist": arrival sim + garrison timelines + greedy assignment. 5-5 vs starter.
- v3: + hold buffers (survive first counter-wave), frontline funneling. 6-4.
- v4 (current main.py): + defensive assistance for doomed planets, funnel only to safe
  planets (cap 60/turn, none in endgame), attack margin on long flights, eta cap on
  enemy attacks. ~10/16 vs starter both sides.

## Diagnosed failure modes (fixed or partially fixed)
- Capturing with +2 buffer → instant recapture by flood bots → hold_buffer.
- Funneling reinforcements into a front planet that flips mid-flight → suicide → safe-only + cap.
- Endgame chip attacks waste score (ships ARE score) → eta caps, no endgame funnel.
- Mid-game collapse vs concentrated floods → defensive assistance (partial fix).

## Roadmap (set 2026-06-11, deadline June 23)
1. Next session: v5.2 settled rating = score to beat. Pull losing ladder replays.
2. Fork-or-fight gate: v5.2 ≥1000 keep our chassis; <900 build on the 1224 kernel.
3. Parallel evaluator first (8 workers). No conclusions on <20 games/both sides.
4. Submission gate: beat previous sub AND 1224 kernel. Submit daily.
5. Differentiate late: counters to known fork constants, 4p FFA. Lock final 2 by ~June 21.

## Session 2026-06-16 — fork executed
- **v5.2 settled at 576.8** (regression vs v4's 617.4). Confirms local 7-1 win over v4
  was not predictive of ladder performance — gate triggered.
- **Fork-or-fight: FORKED.** Both submissions sit far under the 900 threshold; the
  research kernel's constants are themselves more evolved than what we read previously
  (HOSTILE_TARGET_VALUE_MULT 2.05, EXPOSED_PLANET_VALUE_MULT 2.0, ELIMINATION_BONUS 55,
  WEAK_ENEMY_THRESHOLD 110, new WEAKEST_ENEMY/GANG_UP multipliers, MULTI_ENEMY_PROACTIVE_RATIO
  0.35) — this copy is ahead of the PPO-fork snapshot we compared against in session 1.
- Built `scripts/eval_parallel.py` — multiprocessing pool, both-sides games, ~40 games
  in well under a minute with 8 workers. Hard rule satisfied going forward.
- v5_reinforcement_network.py archived to versions/. **main.py is now the 1224-fork
  verbatim** (no tuning yet).
- Local: 1224-fork beat v5.2 39-1 (97.5%, 40 games, seed 200).
- **Submitted v6** (1224-fork, msg "fork public LB-1224 mission-architecture kernel...").
  This is submission #3; only latest 2 are tracked, so v4 (53577673) will drop off the
  ladder once v6 settles, leaving v5.2 and v6 as the tracked pair until the next submit.
- Leaderboard scan: top score now 1794.9 (was unseen in session 1); fork-cluster range
  appears to have moved up to ~1450-1600, higher than the 1100-1300 noted in session 1.
  The clear differentiator above the fork cluster is `research/lb-highest-1000-search-
  learned-value-function/agent.py`: forward sim (20-turn lookahead, top-8 branching) +
  a GBC value function (AUC 0.97, trained on 26.7k replay-derived rows) replacing
  heuristic mission scoring. Not reproducible without training data/infra this session.
- **Next planned move (not yet done):** find one concrete, low-risk improvement on top
  of the verbatim fork — candidate ideas: production-aware "is_behind"/"is_ahead" (currently
  ship-count only, ignores production trajectory), smarter doomed-planet evacuation target
  selection (currently nearest-only, no inventory-aware choice), or a shallow top-K lookahead
  on the highest-scored mission candidates as a tie-breaker. Test via eval_parallel.py
  against verbatim-fork baseline (≥20 games/side) before submitting.

## Ideas backlog
- Side-dependent noise: evaluate both sides, more seeds, count games not aggregates.
- Coordinated multi-source attacks (synchronized arrival).
- Snipe planets right after the enemy launches (garrison halved) — arrival sim partly does this.
- Re-evaluate in-flight commitments each turn? Can't redirect fleets; prefer shorter flights.
- Evacuation tuning: dodge value (launch garrison away before a big hit, recapture after).
- Comet riding: capture cheap comet early in its path, harvest production, leave before expiry.
- 4p FFA: avoid early aggression vs humans; target weakest neighbor.
- Watch replays: env.render(mode="html") → replay.html, or kaggle competitions replay.

## Submission log
- 2026-06-11 18:00 UTC — **53577673** v4 economist (versions/v4_economist_defense.py + comet fixes). Local: 30-0 vs starter (seeds 200-214, both sides). **Scored: rank 2705/4295.**
- 2026-06-11 ~22:00 UTC — v5.2 reinforcement network (versions/v5_reinforcement_network.py). Local: 8-0 starter, 7-1 vs v4, 0-6 vs LB-1224 kernel.

## Public-kernel research (research/)
- `orbit-star-wars-lb-max-1224/agent.py` — THE benchmark. Pure Python missions:
  snipe (outbound≥80% garrison → exposed), rescue, recapture, reinforce (mult 1.35),
  crash-exploit (two enemies colliding on a planet), gang-up (4p weakest enemy),
  elimination (bonus 55). Proactive keep 0.35×stacked(4-turn window, 14 horizon).
  Swarm sync tolerance 1-2 turns, top-5 sources. SUN_SAFETY 1.5, opening to turn 80
  with hostile value ×1.55. search_safe_intercept = aim-offset search when sun-blocked.
- Producer-Lite family (slawekbiel, romantamrazov forks): torch orbit_lite planner,
  horizon 18, ROI 1.5, safe_drain launches, regroup along enemy-pressure gradient.
  Not runnable locally (orbit_lite pkg not embedded in notebook).
- Loss anatomy vs 1224: turns 50-150 synced swarms strip our planets (flips.py shows
  11 losses that window); turns 100+ our expansion freezes (keep+hold double-pay).

## Eval harness
- `PYTHONUTF8=1 .venv/Scripts/python.exe scripts/run_local.py --agents main.py starter --games 10 --seed 100`
- scripts/diagnose.py — economy trace per 25 steps; scripts/trace_fleets.py — fleet lifecycle.
