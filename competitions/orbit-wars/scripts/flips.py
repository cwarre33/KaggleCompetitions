"""Count planet ownership flips per window: who captures, who loses what."""
import argparse
import sys
from collections import Counter

from kaggle_environments import make


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agents", nargs="+",
                    default=["main.py", "research/orbit-star-wars-lb-max-1224/agent.py"])
    ap.add_argument("--seed", type=int, default=500)
    ap.add_argument("--window", type=int, default=50)
    args = ap.parse_args()

    env = make("orbit_wars", configuration={"seed": args.seed}, debug=False)
    env.run(list(args.agents))

    prev = {}
    flips = Counter()  # (window, from_owner, to_owner) -> count
    for si, st in enumerate(env.steps):
        obs = st[0].observation
        pl = obs["planets"] if isinstance(obs, dict) else obs.planets
        cur = {p[0]: p[1] for p in pl}
        for pid, owner in cur.items():
            if pid in prev and prev[pid] != owner:
                flips[(si // args.window, prev[pid], owner)] += 1
        prev = cur

    print(f"seed={args.seed}: ownership flips per {args.window}-step window")
    print(f"{'win':>4} | {'neu->P0':>7} {'neu->P1':>7} {'P0->P1':>7} {'P1->P0':>7} {'->neu':>6}")
    windows = sorted(set(k[0] for k in flips))
    for w in windows:
        n0 = flips.get((w, -1, 0), 0)
        n1 = flips.get((w, -1, 1), 0)
        p01 = flips.get((w, 0, 1), 0)
        p10 = flips.get((w, 1, 0), 0)
        tonu = sum(v for k, v in flips.items() if k[0] == w and k[2] == -1)
        print(f"{w*args.window:>4} | {n0:>7} {n1:>7} {p01:>7} {p10:>7} {tonu:>6}")
    final = env.steps[-1]
    print("rewards:", [s.reward for s in final])


if __name__ == "__main__":
    sys.exit(main())
