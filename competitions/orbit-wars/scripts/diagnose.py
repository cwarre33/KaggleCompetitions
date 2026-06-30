"""Trace economy stats over a single game to see where we fall behind."""
import argparse
import sys

from kaggle_environments import make


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agents", nargs="+", default=["main.py", "starter"])
    ap.add_argument("--seed", type=int, default=101)
    args = ap.parse_args()

    env = make("orbit_wars", configuration={"seed": args.seed}, debug=True)
    env.run(list(args.agents))

    n = len(args.agents)
    print(f"seed={args.seed} agents={args.agents}")
    print(f"{'step':>5} | " + " | ".join(
        f"P{i}: planets prod ships fleets" for i in range(n)))
    for si, step_state in enumerate(env.steps):
        if si % 25 != 0 and si != len(env.steps) - 1:
            continue
        obs = step_state[0].observation
        planets = obs["planets"] if isinstance(obs, dict) else obs.planets
        fleets = obs["fleets"] if isinstance(obs, dict) else obs.fleets
        row = []
        for i in range(n):
            nplan = sum(1 for p in planets if p[1] == i)
            prod = sum(p[6] for p in planets if p[1] == i)
            ships = sum(p[5] for p in planets if p[1] == i)
            fs = sum(f[6] for f in fleets if f[1] == i)
            row.append(f"{nplan:3d} {prod:4d} {ships:6d} {fs:5d}")
        print(f"{si:>5} | " + " | ".join(row))

    final = env.steps[-1]
    print("rewards:", [s.reward for s in final])


if __name__ == "__main__":
    sys.exit(main())
