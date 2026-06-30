"""Local evaluation harness for Orbit Wars agents.

Usage:
  python scripts/run_local.py --agents main.py random --games 5
  python scripts/run_local.py --agents main.py versions/v0.py --games 10 --seed 1
"""

import argparse
import sys
import time

from kaggle_environments import make


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agents", nargs="+", default=["main.py", "random"])
    ap.add_argument("--games", type=int, default=3)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--render", action="store_true", help="save HTML replay of last game")
    args = ap.parse_args()

    n = len(args.agents)
    wins = [0] * n
    ties = 0
    t0 = time.time()

    for g in range(args.games):
        seed = (args.seed + g) if args.seed is not None else int(time.time() * 1000) % 100000 + g
        env = make("orbit_wars", configuration={"seed": seed}, debug=True)
        env.run(list(args.agents))
        final = env.steps[-1]
        rewards = [s.reward if s.reward is not None else float("-inf") for s in final]
        statuses = [s.status for s in final]
        best = max(rewards)
        winners = [i for i, r in enumerate(rewards) if r == best]
        if len(winners) == 1:
            wins[winners[0]] += 1
        else:
            ties += 1
        print(f"game {g} seed={seed} rewards={rewards} statuses={statuses} "
              f"winner={'tie' if len(winners) > 1 else args.agents[winners[0]]}",
              flush=True)
        if args.render and g == args.games - 1:
            html = env.render(mode="html", width=800, height=600)
            with open("replay.html", "w", encoding="utf-8") as fh:
                fh.write(html)
            print("saved replay.html")

    dt = time.time() - t0
    print(f"\n=== {args.games} games in {dt:.0f}s ===")
    for name, w in zip(args.agents, wins):
        print(f"  {name}: {w} wins")
    print(f"  ties: {ties}")


if __name__ == "__main__":
    sys.exit(main())
