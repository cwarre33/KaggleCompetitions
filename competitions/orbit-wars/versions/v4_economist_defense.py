"""Orbit Wars agent v3 — "economist".

- Arrival simulation: predicts where every fleet in flight will land and when.
- Garrison timelines: each of my planets keeps exactly the reserve needed to
  survive incoming attacks (net of friendly reinforcements); rest is surplus.
- Anticipatory hold buffer: capture forces are sized to survive the first
  counter-wave from nearby enemy planets, not just to flip the target.
- Frontline funneling: rear planets ship surplus to the friendly planet
  nearest the enemy, so mass is available at the contact point.
- Evacuation: a doomed planet launches everything to the safest friendly
  planet right before it falls.
"""

import math

CENTER = 50.0
SUN_RADIUS = 10.0
BOARD = 100.0
MAX_SPEED = 6.0
EPISODE_STEPS = 500
ROT_LIMIT = 50.0

_turn = [0]


def fleet_speed(ships):
    if ships <= 1:
        return 1.0
    return min(MAX_SPEED,
               1.0 + (MAX_SPEED - 1.0) * (math.log(ships) / math.log(1000.0)) ** 1.5)


class P:
    __slots__ = ("id", "owner", "x", "y", "radius", "ships", "production", "orbiting")

    def __init__(self, raw):
        (self.id, self.owner, self.x, self.y,
         self.radius, self.ships, self.production) = raw
        self.orbiting = (math.hypot(self.x - CENTER, self.y - CENTER)
                         + self.radius < ROT_LIMIT)


class F:
    __slots__ = ("id", "owner", "x", "y", "angle", "from_planet_id", "ships")

    def __init__(self, raw):
        (self.id, self.owner, self.x, self.y,
         self.angle, self.from_planet_id, self.ships) = raw


def predict_pos(p, t, av):
    if not p.orbiting:
        return (p.x, p.y)
    dx, dy = p.x - CENTER, p.y - CENTER
    th = av * t
    c, s = math.cos(th), math.sin(th)
    return (CENTER + dx * c - dy * s, CENTER + dx * s + dy * c)


def seg_dist(ax, ay, bx, by, px, py):
    abx, aby = bx - ax, by - ay
    ab2 = abx * abx + aby * aby
    if ab2 == 0:
        return math.hypot(px - ax, py - ay)
    u = max(0.0, min(1.0, ((px - ax) * abx + (py - ay) * aby) / ab2))
    return math.hypot(px - (ax + u * abx), py - (ay + u * aby))


def simulate_arrivals(planets, fleets, av, horizon=80):
    """For each fleet, find which planet it will hit and when.

    Returns dict planet_id -> list of (eta, owner, ships)."""
    arrivals = {p.id: [] for p in planets}
    for f in fleets:
        v = fleet_speed(f.ships)
        fx, fy = f.x, f.y
        ca, sa = math.cos(f.angle), math.sin(f.angle)
        for t in range(1, horizon + 1):
            nx, ny = fx + ca * v, fy + sa * v
            hit = None
            hd = 1e18
            for p in planets:
                px, py = predict_pos(p, t, av)
                if seg_dist(fx, fy, nx, ny, px, py) <= p.radius + 0.3:
                    d = math.hypot(px - fx, py - fy)
                    if d < hd:
                        hit, hd = p, d
            if hit is not None:
                arrivals[hit.id].append((t, f.owner, f.ships))
                break
            if not (0 <= nx <= BOARD and 0 <= ny <= BOARD):
                break
            if seg_dist(fx, fy, nx, ny, CENTER, CENTER) < SUN_RADIUS:
                break
            fx, fy = nx, ny
    return arrivals


def garrison_timeline(p, arrivals, player, horizon=80):
    """Simulate p's garrison under incoming arrivals (no new launches).

    Returns (min_surplus, falls, fall_eta, deficit):
      min_surplus -- the lowest the garrison gets while still ours
      falls       -- True if the planet is captured by an enemy
      deficit     -- extra ships needed (before fall_eta) to survive
    """
    events = sorted(arrivals.get(p.id, []))
    g = p.ships
    owner = p.owner
    min_g = g
    last_t = 0
    for (t, fowner, fships) in events:
        if owner == player:
            g += p.production * (t - last_t)
        last_t = t
        if fowner == owner or (owner == player and fowner == player):
            g += fships
        else:
            g -= fships
            if g < 0:
                if p.owner == player:
                    return (0, True, t, -g + 1)
                owner = fowner
                g = -g
        if owner == player:
            min_g = min(min_g, g)
    return (min_g, False, None, 0)


def required_to_capture(tgt, arrivals, eta, player):
    """Ships needed for MY fleet arriving at eta to capture tgt."""
    events = sorted(a for a in arrivals.get(tgt.id, []) if a[0] <= eta)
    g = tgt.ships
    owner = tgt.owner
    last_t = 0
    for (t, fowner, fships) in events:
        if owner != -1:
            g += tgt.production * (t - last_t)
        last_t = t
        if fowner == owner:
            g += fships
        else:
            g -= fships
            if g < 0:
                owner = fowner
                g = -g
    if owner != -1:
        g += tgt.production * (eta - last_t + 1)
    if owner == player:
        return 0  # already ours by then
    return int(math.ceil(g)) + 1


def solve_intercept(sx, sy, src_radius, tgt, num_ships, av):
    v = fleet_speed(max(1, num_ships))
    tx, ty = tgt.x, tgt.y
    eta = math.hypot(tx - sx, ty - sy) / v
    for _ in range(8):
        tx, ty = predict_pos(tgt, eta, av)
        d = max(0.5, math.hypot(tx - sx, ty - sy) - tgt.radius - src_radius)
        eta = d / v
    return eta, tx, ty


def path_clear(src, tx, ty, tgt, planets, av, num_ships):
    d = math.hypot(tx - src.x, ty - src.y)
    if d < 1e-6:
        return False
    ux, uy = (tx - src.x) / d, (ty - src.y) / d
    ax, ay = src.x + ux * (src.radius + 0.6), src.y + uy * (src.radius + 0.6)
    if seg_dist(ax, ay, tx, ty, CENTER, CENTER) <= SUN_RADIUS + 1.0:
        return False
    v = fleet_speed(max(1, num_ships))
    for p in planets:
        if p.id == tgt.id or p.id == src.id:
            continue
        # time at which fleet is nearest to p's orbit region
        px0, py0 = p.x, p.y
        # project p onto path to get approximate passing time
        u = max(0.0, min(1.0, ((px0 - ax) * ux + (py0 - ay) * uy) / d))
        t_pass = (u * d) / v
        px, py = predict_pos(p, t_pass, av)
        if seg_dist(ax, ay, tx, ty, px, py) <= p.radius + 1.5:
            return False
    return True


def agent(obs):
    if not isinstance(obs, dict):
        obs = {k: getattr(obs, k, None) for k in
               ("step", "player", "planets", "fleets", "angular_velocity",
                "comet_planet_ids", "comets")}

    step = obs.get("step") or _turn[0] + 1
    _turn[0] = step
    player = obs.get("player", 0)
    av = obs.get("angular_velocity", 0.0) or 0.0
    planets = [P(p) for p in obs.get("planets", [])]
    fleets = [F(f) for f in obs.get("fleets", [])]
    comet_ids = set(obs.get("comet_planet_ids") or [])

    mine = [p for p in planets if p.owner == player]
    if not mine:
        return []

    remaining = max(1, EPISODE_STEPS - step)
    arrivals = simulate_arrivals(planets, fleets, av)

    moves = []
    surplus = {}
    doomed = {}     # pid -> (fall_eta, deficit)
    for p in mine:
        min_g, falls, fall_eta, deficit = garrison_timeline(p, arrivals, player)
        if falls:
            doomed[p.id] = (fall_eta, deficit)
            surplus[p.id] = 0
        else:
            surplus[p.id] = max(0, min_g - max(1, p.production // 2))

    safe = [p for p in mine if p.id not in doomed]
    by_id = {p.id: p for p in planets}

    # --- Defensive assistance: try to save doomed planets worth saving
    for pid, (fall_eta, deficit) in sorted(doomed.items(),
                                           key=lambda kv: -by_id[kv[0]].production):
        tgt = by_id[pid]
        helpers = []
        for src in safe:
            avail = surplus.get(src.id, 0)
            if avail < 5:
                continue
            send = min(avail, deficit + 2)
            eta, tx, ty = solve_intercept(src.x, src.y, src.radius, tgt, send, av)
            if eta < fall_eta:
                helpers.append((eta, src, send, tx, ty))
        helpers.sort()
        remaining_deficit = deficit + 2
        for (eta, src, send, tx, ty) in helpers:
            if remaining_deficit <= 0:
                break
            send = min(send, remaining_deficit, surplus.get(src.id, 0))
            if send < 3:
                continue
            if not path_clear(src, tx, ty, tgt, planets, av, send):
                continue
            angle = math.atan2(ty - src.y, tx - src.x)
            moves.append([src.id, angle, int(send)])
            surplus[src.id] -= send
            remaining_deficit -= send
    # --- Evacuation: doomed planet dumps everything to safest friendly planet
    for p in mine:
        if p.id in doomed and doomed[p.id][0] <= 3 and p.ships > 5 and safe:
            best = min(safe, key=lambda q: math.hypot(q.x - p.x, q.y - p.y))
            eta, tx, ty = solve_intercept(p.x, p.y, p.radius, best, p.ships, av)
            if path_clear(p, tx, ty, best, planets, av, p.ships):
                angle = math.atan2(ty - p.y, tx - p.x)
                moves.append([p.id, angle, int(p.ships)])
                surplus[p.id] = 0

    enemy_planets = [p for p in planets if p.owner not in (-1, player)]

    def hold_buffer(tgt, eta):
        """Extra ships so the captured planet survives the first counter-wave."""
        buf = 0
        for ep in enemy_planets:
            d = math.hypot(ep.x - tgt.x, ep.y - tgt.y)
            wave = max(0, ep.ships) * 0.55
            if wave < 5:
                continue
            counter_eta = d / fleet_speed(max(1, int(wave)))
            if counter_eta <= eta + 25:
                buf = max(buf, wave - tgt.production * max(0, counter_eta - eta))
        return int(math.ceil(min(buf, 120)))

    # --- Build capture candidates
    targets = [p for p in planets if p.owner != player]
    cands = []
    for src in mine:
        avail = surplus.get(src.id, 0)
        if avail <= 2:
            continue
        for tgt in targets:
            eta0, _, _ = solve_intercept(src.x, src.y, src.radius, tgt,
                                         max(5, avail), av)
            need = required_to_capture(tgt, arrivals, eta0, player) + 2
            if need <= 0:
                continue
            eta, tx, ty = solve_intercept(src.x, src.y, src.radius, tgt, need, av)
            need = max(need, required_to_capture(tgt, arrivals, eta, player) + 2)
            if tgt.owner not in (-1, player):
                # margin for garrison growth / estimate error on long flights
                need += int(tgt.production * eta * 0.3) + 2
                if eta > min(45.0, remaining * 0.6):
                    continue  # too long: too much can change mid-flight
            hold = hold_buffer(tgt, eta)
            total = need + hold
            if total > avail:
                continue
            if tgt.id in comet_ids:
                prod = 1.0
                payoff_window = min(remaining - eta, 40.0)  # comets leave
            else:
                prod = float(tgt.production)
                payoff_window = remaining - eta
            if payoff_window <= 0:
                continue
            payoff = prod * payoff_window
            if tgt.owner not in (-1, player):
                payoff *= 1.6  # denies enemy production too
            cost = float(need) + 1.5 * eta  # hold buffer isn't lost, not a cost
            score = payoff / cost
            cands.append((score, src, tgt, total, eta, tx, ty))

    cands.sort(key=lambda c: -c[0])
    committed = set()
    for (score, src, tgt, total, eta, tx, ty) in cands:
        if score < 1.0:
            break
        if tgt.id in committed:
            continue
        if surplus.get(src.id, 0) < total:
            continue
        if not path_clear(src, tx, ty, tgt, planets, av, total):
            continue
        angle = math.atan2(ty - src.y, tx - src.x)
        moves.append([src.id, angle, int(total)])
        surplus[src.id] -= total
        committed.add(tgt.id)

    # --- Frontline funneling: rear planets push surplus toward the front.
    # Only to SAFE planets (a reinforcement crashing into a planet the enemy
    # just captured is a gift), capped per turn, and not in the endgame.
    if enemy_planets and safe and remaining > 60:
        def enemy_proximity(p):
            return min(math.hypot(ep.x - p.x, ep.y - p.y) for ep in enemy_planets)

        front = min(safe, key=enemy_proximity)
        for src in mine:
            extra = min(surplus.get(src.id, 0), 60)
            if src.id == front.id or extra < 20:
                continue
            if enemy_proximity(src) < enemy_proximity(front) + 10:
                continue  # already near the front itself
            eta, tx, ty = solve_intercept(src.x, src.y, src.radius, front,
                                          extra, av)
            if eta > 30:
                continue
            if path_clear(src, tx, ty, front, planets, av, extra):
                angle = math.atan2(ty - src.y, tx - src.x)
                moves.append([src.id, angle, int(extra)])
                surplus[src.id] -= extra

    return moves
