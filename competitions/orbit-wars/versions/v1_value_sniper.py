"""Orbit Wars agent v1 — "value sniper".

Heuristic bot:
- Targets planets by value: production / (capture_cost * eta), with intercept
  prediction for orbiting planets and sun/blocker path checks.
- Sends just enough ships to capture (garrison + production growth + buffer).
- Keeps a defensive reserve sized to incoming enemy fleets.
"""

import math

CENTER = (50.0, 50.0)
SUN_RADIUS = 10.0
BOARD = 100.0
MAX_SPEED = 6.0
EPISODE_STEPS = 500

_turn = 0  # module-level turn counter (persists across calls)


def fleet_speed(ships):
    if ships <= 1:
        return 1.0
    return 1.0 + (MAX_SPEED - 1.0) * (math.log(ships) / math.log(1000.0)) ** 1.5


def is_orbiting(x, y, radius):
    return math.hypot(x - CENTER[0], y - CENTER[1]) + radius < 50.0


def rotate_about_center(x, y, theta):
    dx, dy = x - CENTER[0], y - CENTER[1]
    c, s = math.cos(theta), math.sin(theta)
    return (CENTER[0] + dx * c - dy * s, CENTER[1] + dx * s + dy * c)


def predict_pos(p, t, av):
    """Position of planet p after t turns (av = angular velocity)."""
    if is_orbiting(p.x, p.y, p.radius):
        return rotate_about_center(p.x, p.y, av * t)
    return (p.x, p.y)


def seg_dist_to_point(ax, ay, bx, by, px, py):
    """Distance from point (px,py) to segment (a->b)."""
    abx, aby = bx - ax, by - ay
    ab2 = abx * abx + aby * aby
    if ab2 == 0:
        return math.hypot(px - ax, py - ay)
    u = max(0.0, min(1.0, ((px - ax) * abx + (py - ay) * aby) / ab2))
    return math.hypot(px - (ax + u * abx), py - (ay + u * aby))


class P:
    __slots__ = ("id", "owner", "x", "y", "radius", "ships", "production")

    def __init__(self, raw):
        (self.id, self.owner, self.x, self.y,
         self.radius, self.ships, self.production) = raw


class F:
    __slots__ = ("id", "owner", "x", "y", "angle", "from_planet_id", "ships")

    def __init__(self, raw):
        (self.id, self.owner, self.x, self.y,
         self.angle, self.from_planet_id, self.ships) = raw


def incoming_threat(planet, fleets, av, horizon=40):
    """Enemy ships on a collision course with planet within horizon turns."""
    threat = 0
    for f in fleets:
        v = fleet_speed(f.ships)
        # check successive positions of fleet vs (possibly moving) planet
        for t in range(1, horizon):
            fx = f.x + math.cos(f.angle) * v * t
            fy = f.y + math.sin(f.angle) * v * t
            if not (0 <= fx <= BOARD and 0 <= fy <= BOARD):
                break
            px, py = predict_pos(planet, t, av)
            if math.hypot(fx - px, fy - py) <= planet.radius + v:
                threat += f.ships
                break
    return threat


def solve_intercept(src, target, num_ships, av):
    """Iteratively find (eta, target_future_pos) for a fleet of num_ships."""
    v = fleet_speed(max(1, num_ships))
    tx, ty = target.x, target.y
    eta = math.hypot(tx - src.x, ty - src.y) / v
    for _ in range(6):
        tx, ty = predict_pos(target, eta, av)
        d = max(0.0, math.hypot(tx - src.x, ty - src.y) - target.radius - src.radius)
        eta = d / v
    return eta, tx, ty


def path_clear(src, tx, ty, target, planets, av, eta):
    """Check the straight path from src to (tx,ty) misses the sun and other planets."""
    # launch point: just outside src radius toward target
    d = math.hypot(tx - src.x, ty - src.y)
    if d < 1e-6:
        return False
    ux, uy = (tx - src.x) / d, (ty - src.y) / d
    ax, ay = src.x + ux * (src.radius + 0.6), src.y + uy * (src.radius + 0.6)
    if seg_dist_to_point(ax, ay, tx, ty, *CENTER) <= SUN_RADIUS + 1.0:
        return False
    for p in planets:
        if p.id == target.id or p.id == src.id:
            continue
        # approximate: check planet at half-eta position
        px, py = predict_pos(p, eta / 2.0, av)
        if seg_dist_to_point(ax, ay, tx, ty, px, py) <= p.radius + 1.2:
            return False
    return True


def agent(obs):
    global _turn
    _turn = obs.get("step", _turn + 1) if isinstance(obs, dict) else _turn + 1

    if not isinstance(obs, dict):
        obs = {k: getattr(obs, k) for k in
               ("player", "planets", "fleets", "angular_velocity")}

    player = obs.get("player", 0)
    av = obs.get("angular_velocity", 0.0) or 0.0
    planets = [P(p) for p in obs.get("planets", [])]
    fleets = [F(f) for f in obs.get("fleets", [])]
    comet_ids = set(obs.get("comet_planet_ids", []) or [])

    mine = [p for p in planets if p.owner == player]
    if not mine:
        return []

    enemy_fleets = [f for f in fleets if f.owner != player]
    my_fleet_targets = {}  # target planet id -> ships already en route (mine)
    for f in fleets:
        if f.owner == player:
            # attribute friendly fleets to nearest planet on their ray (approx)
            best, bd = None, 1e9
            for p in planets:
                dd = seg_dist_to_point(
                    f.x, f.y,
                    f.x + math.cos(f.angle) * 200, f.y + math.sin(f.angle) * 200,
                    p.x, p.y)
                if dd <= p.radius + 0.5:
                    dist = math.hypot(p.x - f.x, p.y - f.y)
                    if dist < bd:
                        best, bd = p.id, dist
            if best is not None:
                my_fleet_targets[best] = my_fleet_targets.get(best, 0) + f.ships

    remaining = max(1, EPISODE_STEPS - _turn)
    moves = []

    # defensive reserve per planet
    reserves = {}
    for p in mine:
        threat = incoming_threat(p, enemy_fleets, av)
        reserves[p.id] = threat + max(2, p.production)

    targets = [p for p in planets if p.owner != player]

    for src in sorted(mine, key=lambda p: -p.ships):
        avail = src.ships - reserves.get(src.id, 0)
        if avail <= 0:
            continue

        best = None  # (score, target, num, angle)
        for tgt in targets:
            # rough first guess of required ships
            eta0, _, _ = solve_intercept(src, tgt, max(10, avail), av)
            if tgt.owner == -1:
                need = tgt.ships + 2
            else:
                need = tgt.ships + tgt.production * (eta0 + 2) + 3
            need = int(math.ceil(need)) - my_fleet_targets.get(tgt.id, 0)
            if need <= 0 or need > avail:
                continue

            eta, tx, ty = solve_intercept(src, tgt, need, av)
            if tgt.id in comet_ids and eta > 25:
                continue  # comet may leave before we arrive
            if not path_clear(src, tx, ty, tgt, planets, av, eta):
                continue

            # value: future production captured, discounted by cost and time
            prod = tgt.production if tgt.id not in comet_ids else 1
            payoff = prod * max(0, remaining - eta)
            cost = need + eta * 2.0
            score = payoff / cost
            if tgt.owner not in (-1, player):
                score *= 1.3  # capturing enemy production swings the game harder
            if best is None or score > best[0]:
                angle = math.atan2(ty - src.y, tx - src.x)
                best = (score, tgt, need, angle)

        if best is not None and best[0] > 0.8:
            _, tgt, need, angle = best
            moves.append([src.id, angle, int(need)])
            my_fleet_targets[tgt.id] = my_fleet_targets.get(tgt.id, 0) + need

    return moves
