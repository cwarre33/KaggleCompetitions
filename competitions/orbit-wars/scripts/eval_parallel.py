"""Parallel evaluator: runs N games between two agents using multiprocessing.

Usage:
    python scripts/eval_parallel.py --a main.py --b research/orbit-star-wars-lb-max-1224/agent.py \
        --games 20 --seed 200 --workers 8
"""
import argparse
import multiprocessing as mp
import sys


def _play_one(args):
    agent_a, agent_b, seed, game_idx = args
    from kaggle_environments import make
    env = make("orbit_wars", configuration={"seed": seed}, debug=False)
    try:
        env.run([agent_a, agent_b])
    except Exception as e:
        return game_idx, "ERR", str(e)
    final = env.steps[-1]
    statuses = [s.status for s in final]
    if any(st == "ERROR" for st in statuses):
        return game_idx, "ERR", str(statuses)
    r = [s.reward if s.reward is not None else -2.0 for s in final]
    if r[0] > r[1]:
        result = "A"
    elif r[1] > r[0]:
        result = "B"
    else:
        result = "tie"
    return game_idx, result, None


def run_eval(agent_a, agent_b, games, seed_start, workers, label_a="A", label_b="B"):
    seeds = list(range(seed_start, seed_start + games))
    # Run A-as-P0 games and A-as-P1 games (both sides)
    tasks_p0 = [(agent_a, agent_b, s, i) for i, s in enumerate(seeds)]
    tasks_p1 = [(agent_b, agent_a, s, i + games) for i, s in enumerate(seeds)]
    all_tasks = tasks_p0 + tasks_p1

    with mp.Pool(processes=workers) as pool:
        results = pool.map(_play_one, all_tasks)

    w = l = t = err = 0
    for idx, result, errstr in sorted(results):
        side = "P0" if idx < games else "P1"
        if side == "P0":
            if result == "A":
                w += 1
            elif result == "B":
                l += 1
            elif result == "tie":
                t += 1
            else:
                err += 1
                print(f"  game {idx} (us-as-P0): ERROR — {errstr}", flush=True)
        else:
            if result == "B":
                w += 1
            elif result == "A":
                l += 1
            elif result == "tie":
                t += 1
            else:
                err += 1
                print(f"  game {idx-games} (us-as-P1): ERROR — {errstr}", flush=True)

    total = w + l + t
    rate = w / total * 100 if total > 0 else 0
    print(f"\n{label_a} vs {label_b}: {w}W-{l}L-{t}T  ({rate:.1f}% win, {err} errors, "
          f"{total} games both sides)")
    return w, l, t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", default="main.py", help="Agent A (ours)")
    ap.add_argument("--b", required=True, help="Agent B (opponent)")
    ap.add_argument("--games", type=int, default=20,
                    help="Games per side (total = 2× this)")
    ap.add_argument("--seed", type=int, default=200, help="First seed")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--label-a", default=None)
    ap.add_argument("--label-b", default=None)
    args = ap.parse_args()

    label_a = args.label_a or args.a
    label_b = args.label_b or args.b
    print(f"Running {args.games*2} games ({args.games}/side) using {args.workers} workers, "
          f"seeds {args.seed}-{args.seed + args.games - 1}", flush=True)
    run_eval(args.a, args.b, args.games, args.seed, args.workers, label_a, label_b)


if __name__ == "__main__":
    mp.freeze_support()
    sys.exit(main())
