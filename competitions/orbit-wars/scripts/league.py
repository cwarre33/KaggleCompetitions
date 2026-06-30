"""Round-robin league: main.py vs each research agent, both sides."""
import argparse
import glob
import os
import sys

from kaggle_environments import make


def play(a, b, seed):
    env = make("orbit_wars", configuration={"seed": seed}, debug=False)
    try:
        env.run([a, b])
    except Exception as e:
        return f"CRASH: {e}"
    final = env.steps[-1]
    statuses = [s.status for s in final]
    if any(st == "ERROR" for st in statuses):
        return "ERR" + str(statuses)
    rewards = [s.reward if s.reward is not None else -2 for s in final]
    if rewards[0] > rewards[1]:
        return "A"
    if rewards[1] > rewards[0]:
        return "B"
    return "tie"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ours", default="main.py")
    ap.add_argument("--games", type=int, default=4, help="games per side")
    ap.add_argument("--seed", type=int, default=500)
    ap.add_argument("--opponents", nargs="*", default=None)
    args = ap.parse_args()

    opps = args.opponents or sorted(glob.glob("research/*/agent.py"))
    for opp in opps:
        name = os.path.basename(os.path.dirname(opp)) if "research" in opp else opp
        w = l = t = e = 0
        for g in range(args.games):
            r = play(args.ours, opp, args.seed + g)
            print(f"  [{name}] g{g} us-as-P0: {r[:120]}", flush=True)
            if r == "A":
                w += 1
            elif r == "B":
                l += 1
            elif r == "tie":
                t += 1
            else:
                e += 1
            r = play(opp, args.ours, args.seed + g)
            print(f"  [{name}] g{g} us-as-P1: {r[:120]}", flush=True)
            if r == "B":
                w += 1
            elif r == "A":
                l += 1
            elif r == "tie":
                t += 1
            else:
                e += 1
        total = w + l + t
        print(f"{name}: {w}W-{l}L-{t}T (of {total}, {e} errored)", flush=True)


if __name__ == "__main__":
    sys.exit(main())
