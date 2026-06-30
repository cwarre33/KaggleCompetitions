"""Track the lifecycle of large fleets: where they launch, where they die."""
import argparse
import math
import sys

from kaggle_environments import make


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agents", nargs="+", default=["main.py", "starter"])
    ap.add_argument("--seed", type=int, default=101)
    ap.add_argument("--min-ships", type=int, default=80)
    ap.add_argument("--owner", type=int, default=0)
    args = ap.parse_args()

    env = make("orbit_wars", configuration={"seed": args.seed}, debug=True)
    env.run(list(args.agents))

    # fleet id -> (birth_step, ships, last_x, last_y, last_step)
    tracked = {}
    planets_by_step = []
    for si, st in enumerate(env.steps):
        obs = st[0].observation
        fl = obs["fleets"] if isinstance(obs, dict) else obs.fleets
        pl = obs["planets"] if isinstance(obs, dict) else obs.planets
        planets_by_step.append(pl)
        seen = set()
        for f in fl:
            fid, owner, x, y, angle, src, ships = f
            if owner != args.owner or ships < args.min_ships:
                continue
            seen.add(fid)
            if fid not in tracked:
                tracked[fid] = [si, ships, x, y, si, src]
            else:
                tracked[fid][2:5] = [x, y, si]

    for fid, (b, ships, x, y, last, src) in sorted(tracked.items()):
        death = last + 1
        # what's near the last position at death step?
        pl = planets_by_step[min(death, len(planets_by_step) - 1)]
        near = sorted(pl, key=lambda p: math.hypot(p[2] - x, p[3] - y))[:2]
        near_s = ", ".join(
            f"pid{p[0]}(own{p[1]} ships{p[5]} prod{p[6]} d={math.hypot(p[2]-x,p[3]-y):.1f})"
            for p in near)
        sun_d = math.hypot(x - 50, y - 50)
        oob = not (0 <= x <= 100 and 0 <= y <= 100)
        print(f"fleet {fid}: {ships} ships, born s{b} from pid{src}, "
              f"last seen s{last} at ({x:.1f},{y:.1f}) sun_d={sun_d:.1f} oob={oob}")
        print(f"    nearest planets after death: {near_s}")


if __name__ == "__main__":
    sys.exit(main())
