import math
import time
import copy
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from kaggle_environments.envs.orbit_wars.orbit_wars import (
    Fleet, CENTER, ROTATION_RADIUS_LIMIT, SUN_RADIUS,
    distance, point_to_segment_distance
)

class HPlanet:
    def __init__(self, id, owner, x, y, radius, ships, production):
        self.id = id; self.owner = owner; self.x = x; self.y = y
        self.radius = radius; self.ships = ships; self.production = production
        self.reinforcement_target: 'HPlanet | None' = None  # nearest owned planet on shortest path to front

# HPlanet -> (orbital_radius, initial_angle) if the planet orbits the sun, else None
OrbitalInfo = dict[HPlanet, tuple[float, float] | None]
# HPlanets rotated by ROTATION_LOOK_AHEAD
FuturePos = dict[HPlanet, tuple[float, float]]
# dst -> [(src, travel_steps)]: directed graph; src departs now, dst is its intercept position
ProximityGraph = dict[HPlanet, list[tuple[HPlanet, float]]]
# HPlanet -> [(owner, ships, travel_time, src_x, src_y, arrival_x, arrival_y)]
DestinationList = dict[HPlanet, list[tuple[int, float, float, float, float, float, float]]]
# [planet_id, angle, ships]
FleetOrders = list[list]
# (intercept_x, intercept_y, travel_steps)
Intercept = tuple[float, float, float]
# (target planet, heuristic value, fleet orders, intercepts)
# intercepts is parallel to fleet_orders: list of (ix, iy, travel) pre-computed at plan time
MoveOrders = tuple[HPlanet | None, int, FleetOrders, list[Intercept]]

@dataclass(slots=True)
class EarlyGameFleet:
    source_id: int
    destination_id: int
    fleet_size: int
    garrison_on_arrival: int
    arrival_turn: int
    is_capture: bool

@dataclass(slots=True)
class EarlyGameState:
    turn: int
    garrison: dict
    production: dict
    owned: set
    fleets: list = field(default_factory=list)


class Hellburner:
    SHIP_SPEED_MAX: float = 6.0
    EARLY_ROUNDS: int = 3
    EARLY_LOOK_AHEAD: int = 33
    MAX_DISTANCE: int = 38
    ROTATION_LOOK_AHEAD: int = 10
    REINFORCEMENT_SIZE: int = 17
    GARRISON_SIZE: int = 11

    def __init__(self):
        self.player: int = 0
        self.scene_step: int = 0
        self.angular_velocity: float = 0.0
        self.planets: list[HPlanet] = []
        self.owned_planets: list[HPlanet] = []
        self.enemy_planets: list[HPlanet] = []
        self.fleets: list[Fleet] = []
        self.orbital_info: OrbitalInfo = {}
        self.inbound_edges: ProximityGraph = {}
        self.outbound_edges: ProximityGraph = {}
        self.future_pos: FuturePos = {}
        self.destination_list: DestinationList = {}

    def fleet_speed(self, ships: int | float) -> float:
        return min(self.SHIP_SPEED_MAX, 1.0 + (self.SHIP_SPEED_MAX - 1.0) * (math.log(ships) / math.log(1000)) ** 1.5)

    def build_orbital_info(self, initial_planets: list[Any]) -> None:
        """Return dict mapping Planet -> (r, initial_angle) if orbiting, else None."""
        cx = cy = CENTER
        ip_by_id = {ip[0]: ip for ip in initial_planets}
        self.orbital_info = {}
        for p in self.planets:
            r = distance((p.x, p.y), (cx, cy))
            if r + p.radius < ROTATION_RADIUS_LIMIT and p.id in ip_by_id:
                ip = ip_by_id[p.id]
                self.orbital_info[p] = (r, math.atan2(ip[3] - cy, ip[2] - cx))
            else:
                self.orbital_info[p] = None

    def build_proximity_graph(self) -> None:
        """Build directed adjacency list: dst -> [(src, travel_steps)].

        Directed because:
        - src departs from its current position immediately
        - dst is rotated into the future to its intercept position
        So travel from A->B and B->A may differ and one direction may exceed MAX_DISTANCE.

        future_pos stores each planet's current position (source frame).
        intercept_pos stores each planet's arrival position given a shot from the center
        (used only for visualization; actual intercepts are computed per-src in evaluate_frontline_strategy).
        """
        cx = cy = CENTER
        self.future_pos = {}
        for p in self.planets:
            orb = self.orbital_info[p]
            if orb is not None:
                r, ia = orb
                a = ia + self.angular_velocity * (self.scene_step + 1 + self.ROTATION_LOOK_AHEAD)
                self.future_pos[p] = (cx + r * math.cos(a), cy + r * math.sin(a))
            else:
                self.future_pos[p] = (p.x, p.y)

        self.inbound_edges = {p: [] for p in self.planets}
        for src in self.planets:
            for dst in self.planets:
                if dst is src:
                    continue
                travel = distance((src.x, src.y), self.future_pos[dst])
                if travel <= self.MAX_DISTANCE:
                    self.inbound_edges[dst].append((src, travel))

        # self.outbound_edges[p] = [(dst, travel)] — keyed by source, complement of the inbound-keyed inbound_edges.
        self.outbound_edges = {p: [] for p in self.planets}
        for dst, inbound in self.inbound_edges.items():
            for src, travel in inbound:
                self.outbound_edges[src].append((dst, travel))

    def build_reinforcement_targets(self) -> None:
        front_line = {
            p for p in self.owned_planets
            if any(src.owner != self.player for src, _ in self.inbound_edges[p])
            or any(dst.owner != self.player for dst, _ in self.outbound_edges[p])
        }

        # BFS hop-distance from every owned node to nearest frontline planet,
        # traversing only owned-planet edges (frontline nodes are sinks, not sources).
        hops_to_front: dict[HPlanet, int] = {p: 0 for p in front_line}
        queue: list[HPlanet] = list(front_line)
        head = 0
        while head < len(queue):
            node = queue[head]; head += 1
            for src, _ in self.inbound_edges[node]:
                if src.owner != self.player or src in hops_to_front:
                    continue
                hops_to_front[src] = hops_to_front[node] + 1
                queue.append(src)

        for p in self.owned_planets:
            p.reinforcement_target = None
            if p in front_line:
                continue

            direct_front = [
                dst for dst, _ in self.outbound_edges[p]
                if dst in front_line
            ]
            if direct_front:
                p.reinforcement_target = min(direct_front, key=lambda d: d.ships)
                continue

            # No direct edge to a frontline planet: pick the direct neighbor with
            # fewest hops to the front, breaking ties by fewest ships at destination.
            reachable = [
                dst for dst, _ in self.outbound_edges[p]
                if dst.owner == self.player and dst not in front_line and dst in hops_to_front
            ]
            if reachable:
                p.reinforcement_target = min(reachable, key=lambda d: (hops_to_front[d], d.ships))

    def intercept_planet(
        self,
        sx: float, sy: float, target: HPlanet, ships: int | float,
        tol: float = 1e-6, max_iters: int = 30,
    ) -> tuple[float, float, float, float]:
        """Aim angle from (sx, sy) toward where target will be when a fleet arrives.
        Returns (angle, intercept_x, intercept_y, travel_steps).
        """
        speed = self.fleet_speed(ships)
        orb = self.orbital_info[target]
        if orb is None:
            tx, ty = target.x, target.y
            travel = distance((sx, sy), (tx, ty)) / speed
        else:
            cx = cy = CENTER
            r, ia = orb
            # Seed: straight-line travel time to the planet's current position.
            travel = distance((sx, sy), (target.x, target.y)) / speed
            for _ in range(max_iters):
                a = ia + self.angular_velocity * (self.scene_step + travel - 0.5)
                new_tx, new_ty = cx + r * math.cos(a), cy + r * math.sin(a)
                new_travel = distance((sx, sy), (new_tx, new_ty)) / speed
                # Damp update: average old and new travel to suppress oscillation.
                new_travel = 0.5 * (travel + new_travel - 0.5)
                if abs(new_travel - travel) < tol:
                    travel = new_travel
                    break
                travel = new_travel
            else:
                # Diverged: fleet too slow to catch this planet's orbital speed.
                return 0.0, target.x, target.y, math.inf
            # Recompute final position from converged travel so tx/ty/angle are consistent.
            a = ia + self.angular_velocity * (self.scene_step + travel - 0.5)
            tx, ty = cx + r * math.cos(a), cy + r * math.sin(a)
        angle = math.atan2(ty - sy, tx - sx)
        return angle, tx, ty, travel

    def first_planet_hit(self, sx: float, sy: float, angle: float, ships: int | float, source: HPlanet) -> HPlanet | None:
        """Return the first planet a fleet launched from (sx, sy) at `angle` would hit, or None.
        Returns None if the path crosses the sun before any planet is hit."""
        best = None
        best_t = float('inf')
        for planet in self.planets:
            if planet is source:
                continue
            needed_angle, px, py, travel = self.intercept_planet(sx, sy, planet, ships)
            dist = distance((sx, sy), (px, py))
            if dist < planet.radius:
                half_cone = math.pi
            else:
                half_cone = math.asin(min(1.0, planet.radius / dist))
            delta = abs(math.atan2(math.sin(angle - needed_angle), math.cos(angle - needed_angle)))
            if math.isfinite(travel) and delta <= half_cone and travel < best_t:
                best_t = travel
                best = planet
        if best is None:
            return None
        # Check if the sun blocks the path to the first planet hit.
        ex, ey = sx + best_t * self.fleet_speed(ships) * math.cos(angle), sy + best_t * self.fleet_speed(ships) * math.sin(angle)
        if point_to_segment_distance((CENTER, CENTER), (sx, sy), (ex, ey)) <= SUN_RADIUS:
            return None
        return best

    def build_destination_list(self) -> None:
        """For each fleet, find the first planet it is on an interception course for.
        Populates self.destination_list: Planet -> list of (owner, ships, t, src_x, src_y, arrival_x, arrival_y).
        t is continuous time in turns.
        """
        self.destination_list = defaultdict(list)
        for fleet in self.fleets:
            best = None
            best_t = float('inf')
            for planet in self.planets:
                needed_angle, px, py, travel = self.intercept_planet(
                    fleet.x, fleet.y, planet, fleet.ships
                )
                dist = distance((fleet.x, fleet.y), (px, py))
                if dist < planet.radius:
                    half_cone = math.pi
                else:
                    half_cone = math.asin(min(1.0, planet.radius / dist))
                delta = abs(math.atan2(math.sin(fleet.angle - needed_angle),
                                       math.cos(fleet.angle - needed_angle)))
                if math.isfinite(travel) and delta <= half_cone and travel < best_t:
                    best_t = travel
                    best = (planet, travel, px, py)
            if best is not None:
                planet, travel, px, py = best
                self.destination_list[planet].append((fleet.owner, fleet.ships, travel, fleet.x, fleet.y, px, py))

    def simulate_planet_timeline(self, planet: HPlanet, destination_list: DestinationList) -> tuple[int, float]:
        """Simulate planet ownership/production over time given a list of inbound fleets.
        All arrivals at the same integer turn are resolved simultaneously (highest stack wins).
        Returns (final_owner, excess_ships) where excess_ships is the surplus in the last entry in destination_list.
        """
        cur_owner = planet.owner
        entries = destination_list.get(planet)
        if not bool(entries):
            return cur_owner, 0

        buckets = defaultdict(list)
        for owner, ships, t, _, _, _, _ in entries:
            turn = max(1, math.ceil(t))
            buckets[turn].append((owner, ships))

        last_ships, last_t = entries[-1][1], entries[-1][2]
        last_turn = max(1, math.ceil(last_t))

        cur_ships = float(planet.ships)
        prod = planet.production
        cur_t = 0
        # minimum margin by which the player survived each fight after the last entry landed
        excess_ships = float('inf')

        for turn in sorted(buckets):
            elapsed = turn - cur_t
            if elapsed > 0:
                if cur_owner == self.player:
                    cur_ships += prod * elapsed
                elif cur_owner != -1:
                    cur_ships += prod * elapsed
            cur_t = turn

            owner_ships = defaultdict(float)
            for owner, ships in buckets[turn]:
                owner_ships[owner] += ships

            if owner_ships:
                sorted_owners = sorted(owner_ships.items(), key=lambda x: x[1], reverse=True)
                if len(sorted_owners) == 1:
                    survivor_owner, survivor_ships = sorted_owners[0]
                else:
                    top_owner, top_ships = sorted_owners[0]
                    second_ships = sorted_owners[1][1]
                    survivor_ships = top_ships - second_ships
                    survivor_owner = top_owner if survivor_ships > 0 else -1

                if survivor_ships > 0:
                    if survivor_owner == cur_owner:
                        cur_ships += survivor_ships
                    else:
                        cur_ships -= survivor_ships
                        if cur_ships < 0:
                            cur_owner = survivor_owner
                            cur_ships = abs(cur_ships)

            if turn >= last_turn:
                # track the narrowest margin by which we stayed in control
                margin = cur_ships if cur_owner == self.player else 0.0
                excess_ships = min(excess_ships, margin)

        if excess_ships == float('inf'):
            excess_ships = 0.0
        # excess can't exceed what the last entry actually sent
        excess_ships = min(excess_ships, last_ships)

        return cur_owner, excess_ships

    def evaluate_frontline_strategy(self, target: HPlanet) -> tuple[FleetOrders, list[Intercept], bool]:
        """Find the set of nearby ships needed to attack or reinforce a target.
        Returns (fleet_orders, intercepts, battle_won).
        intercepts is parallel to fleet_orders: list of (ix, iy, travel) pre-computed at plan time.
        """
        possible_origins = sorted(
            [(src, travel) for src, travel in self.inbound_edges.get(target, [])
                if src.owner == self.player], key=lambda x: x[1])

        fleet_orders: FleetOrders = []
        intercepts: list[Intercept] = []
        # Scale enemy ships at the target down to 50% — only half may actually threaten us.
        trial_destination_list = {}
        for _p, _entries in self.destination_list.items():
            if _p is target:
                trial_destination_list[_p] = [
                    (o, int(s * 0.5) if o != self.player else s, t, x, y, bx, by)
                    for o, s, t, x, y, bx, by in _entries
                ]
            else:
                trial_destination_list[_p] = list(_entries)
        trial_destination_list.setdefault(target, [])
        battle_won = False

        # If an enemy fleet is already inbound to this target (attacking its current owner,
        # who is not us), don't arrive until after that battle resolves.
        second_enemy_arrival = None
        if target.owner != self.player:
            for owner, _, t, _, _, _, _ in self.destination_list.get(target, []):
                if owner != self.player and owner != target.owner:
                    turn = math.ceil(t)
                    if second_enemy_arrival is None or turn < second_enemy_arrival:
                        second_enemy_arrival = turn

        for neighbor, _ in possible_origins:
            if neighbor.ships == 0:
                continue

            # Cost/benefit: is exposing neighbor to worst-case enemy pressure worthwhile?
            # Only relevant when neighbor survives in the baseline — if it's already doomed, send freely.
            # Assume all enemy planets connected via inbound_edges attack neighbor simultaneously.
            ships_to_send = int(neighbor.ships)
            baseline_owner, _ = self.simulate_planet_timeline(neighbor, self.destination_list)
            not_doomed = baseline_owner == self.player
            if not_doomed:
                worst_case_dl = {k: list(v) for k, v in self.destination_list.items()}
                worst_case_dl.setdefault(neighbor, [])
                half_pressure = 0
                for attacker, _ in self.inbound_edges.get(neighbor, []):
                    if attacker.owner == self.player or attacker.owner == -1 or attacker.ships == 0:
                        continue
                    _, ax, ay, atk_travel = self.intercept_planet(attacker.x, attacker.y, neighbor, attacker.ships)
                    if not math.isfinite(atk_travel):
                        continue
                    half_ships = max(1, int(attacker.ships * 0.5))
                    worst_case_dl[neighbor].append((attacker.owner, half_ships, atk_travel, attacker.x, attacker.y, ax, ay))
                    half_pressure += half_ships

                saved_ships = neighbor.ships
                neighbor.ships = 0
                exposed_owner, _ = self.simulate_planet_timeline(neighbor, worst_case_dl)
                neighbor.ships = saved_ships

                if exposed_owner != self.player:
                    # Neighbor would fall under worst-case pressure; skip unless target production offsets the loss.
                    if target.production <= neighbor.production:
                        continue
                    # Knowingly sacrificing neighbor — send all ships.
                else:
                    # Neighbor holds worst-case; keep 50% of enemy pressure as a garrison buffer.
                    ships_to_send = max(0, int(neighbor.ships) - half_pressure)
                    if ships_to_send == 0:
                        continue

            # Cannot reach or is blocked.
            angle, ix, iy, travel = self.intercept_planet(neighbor.x, neighbor.y, target, ships_to_send)
            if not math.isfinite(travel):
                continue
            if self.first_planet_hit(neighbor.x, neighbor.y, angle, ships_to_send, neighbor) is not target:
                continue

            # second enemy arrival handling
            # + 1 for tolerance in swept collision handling
            if second_enemy_arrival is not None and math.ceil(travel) <= second_enemy_arrival + 1:
                continue

            trial_destination_list[target].append((self.player, ships_to_send, travel, neighbor.x, neighbor.y, ix, iy))
            fleet_orders.append([neighbor.id, angle, ships_to_send])
            intercepts.append((ix, iy, travel))
            trial_end_owner, excess_ships = self.simulate_planet_timeline(target, trial_destination_list)
            if trial_end_owner == self.player:
                battle_won = True

                if not_doomed:
                    # Try leaving half the excess ships behind; re-simulate to confirm still winning.
                    # Never trim below 10 ships (small fleets move slowly and may miss the battle window).
                    keep = int(excess_ships // 2)
                    trimmed = max(10, ships_to_send - keep)
                    if trimmed < ships_to_send:
                        t_angle, t_ix, t_iy, t_travel = self.intercept_planet(neighbor.x, neighbor.y, target, trimmed)
                        if math.isfinite(t_travel):
                            trial_destination_list[target][-1] = (self.player, trimmed, t_travel, neighbor.x, neighbor.y, t_ix, t_iy)
                            if self.simulate_planet_timeline(target, trial_destination_list)[0] == self.player:
                                ships_to_send, angle, ix, iy, travel = trimmed, t_angle, t_ix, t_iy, t_travel
                            else:
                                # Trim would lose the battle; revert entry and keep original fleet.
                                trial_destination_list[target][-1] = (self.player, ships_to_send, travel, neighbor.x, neighbor.y, ix, iy)
                        # If t_travel is not finite, trimmed fleet can't reach target — keep original.
                    fleet_orders[-1] = [neighbor.id, angle, ships_to_send]
                    intercepts[-1] = (ix, iy, travel)
                break

        return fleet_orders, intercepts, battle_won

    def evaluate_move_orders(self) -> MoveOrders:
        """Score every reachable planet and pick the best destination."""
        best_move_orders: MoveOrders = (None, -65535, [], [])

        for target in sorted(self.planets, key=lambda p: p.ships, reverse=True):
            if not bool(self.inbound_edges.get(target)):
                continue # effectively unreachable

            # is owned
            if (target.owner == self.player):
                if not bool(self.destination_list.get(target)):
                    continue # no incoming

                end_owner, _ = self.simulate_planet_timeline(target, self.destination_list)
                threatened = (end_owner != self.player)
                if not threatened:
                    continue

                fleet_orders, intercepts, battle_won = self.evaluate_frontline_strategy(target)

                if not battle_won:
                    continue  # can't save it; skip for now

                value = target.production
                _, best_value, best_orders, _ = best_move_orders
                if (value > best_value or
                        (value == best_value and len(fleet_orders) < len(best_orders))):
                    best_move_orders = (target, value, fleet_orders, intercepts)

            # not owned
            else:
                end_owner, _ = self.simulate_planet_timeline(target, self.destination_list)
                if end_owner == self.player:
                    continue  # already won by in-flight fleets

                fleet_orders, intercepts, battle_won = self.evaluate_frontline_strategy(target)
                if not battle_won:
                    continue

                value = target.production
                if (target.owner == -1):
                    value = value - 1

                _, best_value, best_orders, _ = best_move_orders
                if (value > best_value or
                        (value == best_value and len(fleet_orders) < len(best_orders))):
                    best_move_orders = (target, value, fleet_orders, intercepts)

        return best_move_orders

    def send_reinforcements(self) -> FleetOrders:
        """ Allows sending by an intermediate planet if in the way. """
        orders: FleetOrders = []
        for p in self.owned_planets:
            if p.reinforcement_target is None:
                continue
            if p.ships < (self.REINFORCEMENT_SIZE + self.GARRISON_SIZE):
                continue
            has_enemy_incoming = any(
                src.owner != self.player
                for src, _ in self.inbound_edges.get(p, []) )
            if has_enemy_incoming:
                continue
            target = p.reinforcement_target
            ships = int(p.ships - self.GARRISON_SIZE)
            angle, ix, iy, travel = self.intercept_planet(p.x, p.y, target, ships)
            if not math.isfinite(travel):
                continue
            orders.append([p.id, angle, ships])
        return orders

    def commit_move_orders(self, move: MoveOrders) -> None:
        target, _, fleet_orders, intercepts = move

        for (from_id, _, ships), (ix, iy, travel) in zip(fleet_orders, intercepts):
            src = next((p for p in self.planets if p.id == from_id), None)
            if src is None:
                continue
            src.ships = max(0, src.ships - ships)
            self.destination_list.setdefault(target, [])
            self.destination_list[target].append((self.player, ships, travel, src.x, src.y, ix, iy))

    # ------------------------------------------------------------------
    # Early game optimizer

    def early_game_compute_travel_turns(self, source_id: int, target: HPlanet, fleet_size: int, launch_turn: int) -> float:
        src = next(p for p in self.planets if p.id == source_id)
        orb = self.orbital_info.get(src)
        if orb is not None:
            cx = cy = CENTER
            r, ia = orb
            a = ia + self.angular_velocity * (launch_turn - 0.5)
            sx, sy = cx + r * math.cos(a), cy + r * math.sin(a)
        else:
            sx, sy = src.x, src.y
        _, _, _, travel = self.intercept_planet(sx, sy, target, fleet_size)
        return travel

    def early_game_find_capture_turn(self, state: EarlyGameState, target: HPlanet) -> float:
        """Return the earliest turn any single owned source can deliver > garrison ships."""
        garrison_size = target.ships
        horizon = state.turn + self.EARLY_LOOK_AHEAD
        best = math.inf
        for source in state.owned:
            current_ships = state.garrison[source]
            production_rate = state.production[source]
            for wait_turns in range(self.EARLY_LOOK_AHEAD):
                fleet_size = int(current_ships + production_rate * wait_turns)
                if fleet_size <= garrison_size:
                    continue
                launch_turn = state.turn + wait_turns
                if launch_turn >= horizon:
                    break
                travel_turns = self.early_game_compute_travel_turns(source, target, fleet_size, launch_turn)
                if not math.isfinite(travel_turns):
                    continue
                arrival_turn = launch_turn + math.ceil(travel_turns)
                if arrival_turn <= horizon:
                    best = min(best, arrival_turn)
                    break  # larger fleets from this source arrive no earlier
        return best

    def early_game_assign_fleets(self, state: EarlyGameState, target: HPlanet, capture_turn: int) -> dict:
        """Pick the single best source: earliest arrival with fleet > garrison."""
        garrison_size = target.ships
        best_source = None
        best_entry = None
        best_arrival = math.inf
        for source in state.owned:
            current_ships = state.garrison[source]
            production_rate = state.production[source]
            for wait_turns in range(capture_turn - state.turn):
                fleet_size = int(current_ships + production_rate * wait_turns)
                if fleet_size <= garrison_size:
                    continue
                launch_turn = state.turn + wait_turns
                travel_turns = self.early_game_compute_travel_turns(source, target, fleet_size, launch_turn)
                if not math.isfinite(travel_turns):
                    continue
                arrival_turn = launch_turn + math.ceil(travel_turns)
                if arrival_turn <= capture_turn and arrival_turn < best_arrival:
                    best_arrival = arrival_turn
                    best_source = source
                    best_entry = (fleet_size, launch_turn, arrival_turn)
                break  # larger fleets from this source arrive no earlier
        if best_source is None:
            return {}
        return {best_source: best_entry}

    def early_game_advance(self, state: EarlyGameState, from_turn: int, to_turn: int) -> EarlyGameState:
        for current_turn in range(from_turn + 1, to_turn + 1):
            for fleet in list(state.fleets):
                if fleet.arrival_turn == current_turn:
                    if fleet.is_capture:
                        state.garrison[fleet.destination_id] = fleet.garrison_on_arrival
                        state.owned.add(fleet.destination_id)
                        if fleet.destination_id not in state.production:
                            state.production[fleet.destination_id] = self.early_game_production(fleet.destination_id)
                    else:
                        state.garrison[fleet.destination_id] += fleet.garrison_on_arrival
                    state.fleets.remove(fleet)
            for planet_id in state.owned:
                state.garrison[planet_id] += state.production[planet_id]
        return state

    def early_game_execute_attack(self, state: EarlyGameState, target: HPlanet, fleet_assignment: dict, capture_turn: int) -> EarlyGameState:
        garrison_size = target.ships
        total_fleet = sum(fs for fs, _, _ in fleet_assignment.values())

        current_turn = state.turn
        for source, (fleet_size, launch_turn, _) in sorted(fleet_assignment.items(), key=lambda se: se[1][1]):
            state = self.early_game_advance(state, current_turn, launch_turn)
            current_turn = launch_turn
            state.garrison[source] -= fleet_size

        state.fleets.append(EarlyGameFleet(
            source_id=-1,
            destination_id=target.id,
            fleet_size=total_fleet,
            garrison_on_arrival=total_fleet - garrison_size,
            arrival_turn=capture_turn,
            is_capture=True,
        ))
        state = self.early_game_advance(state, current_turn, capture_turn)
        return state

    def early_game_score(self, state: EarlyGameState) -> int:
        horizon = state.turn + self.EARLY_LOOK_AHEAD
        total = 0
        for planet_id in state.owned:
            total += state.garrison[planet_id] + state.production[planet_id] * (horizon - state.turn)
        for fleet in state.fleets:
            total += fleet.garrison_on_arrival
            if fleet.is_capture:
                total += self.early_game_production(fleet.destination_id) * max(0, horizon - fleet.arrival_turn)
        return total

    def early_game_production(self, planet_id: int) -> int:
        p = next((pl for pl in self.planets if pl.id == planet_id), None)
        return p.production if p else 0

    def run_early_game(self) -> list:
        owned_ids = {p.id for p in self.owned_planets}
        neutral_candidates = [
            p for p in self.planets
            if p.owner == -1 and any(src.id in owned_ids for src, _ in self.inbound_edges.get(p, []))
        ]

        # Populate in-flight friendly fleets from destination_list so the optimizer
        # knows about already-committed ships and won't double-assign the same target.
        in_flight: list[EarlyGameFleet] = []
        for dest_planet, arrivals in self.destination_list.items():
            for owner, ships, t, _, _, _, _ in arrivals:
                if owner != self.player:
                    continue
                arrival = self.scene_step + math.ceil(t)
                is_cap = dest_planet.owner != self.player
                surplus = ships - dest_planet.ships
                in_flight.append(EarlyGameFleet(
                    source_id=-1,
                    destination_id=dest_planet.id,
                    fleet_size=int(ships),
                    garrison_on_arrival=int(surplus) if is_cap else int(ships),
                    arrival_turn=arrival,
                    is_capture=is_cap,
                ))

        initial_state = EarlyGameState(
            turn=self.scene_step,
            garrison={p.id: float(p.ships) for p in self.owned_planets},
            production={p.id: p.production for p in self.owned_planets},
            owned=owned_ids.copy(),
            fleets=in_flight,
        )

        def initial_gain(planet: HPlanet) -> float:
            ct = self.early_game_find_capture_turn(initial_state, planet)
            horizon = initial_state.turn + self.EARLY_LOOK_AHEAD
            return planet.production * (horizon - ct) - planet.ships if math.isfinite(ct) else -math.inf

        candidates = sorted(neutral_candidates, key=initial_gain, reverse=True)
        gain_dbg = [(f'P{p.id}', round(initial_gain(p), 2)) for p in candidates]
        candidates = [p for p in candidates if initial_gain(p) > 0]
        viz.add_text(self.scene_step, f'eg_candidates gain: {gain_dbg}\neg_kept: {[f"P{p.id}" for p in candidates]}')

        if not candidates:
            return []

        best = [self.early_game_score(initial_state), []]

        def upper_bound(state, remaining):
            horizon = state.turn + self.EARLY_LOOK_AHEAD
            bound = self.early_game_score(state)
            for planet in remaining:
                ct = self.early_game_find_capture_turn(state, planet)
                gain = planet.production * (horizon - ct) - planet.ships
                if gain > 0:
                    bound += gain
            return bound

        def dfs(state, remaining, sequence):
            current_score = self.early_game_score(state)
            if current_score > best[0]:
                best[0] = current_score
                best[1] = list(sequence)

            if upper_bound(state, remaining) <= best[0]:
                return

            already_targeted = {f.destination_id for f in state.fleets if f.is_capture}
            for index, planet in enumerate(remaining):
                if planet.id in already_targeted:
                    continue
                horizon = state.turn + self.EARLY_LOOK_AHEAD
                ct = self.early_game_find_capture_turn(state, planet)
                if not math.isfinite(ct):
                    continue
                if planet.production * (horizon - ct) - planet.ships <= 0:
                    continue
                fleet_assignment = self.early_game_assign_fleets(state, planet, ct)
                if not fleet_assignment:
                    continue
                next_state = self.early_game_execute_attack(copy.deepcopy(state), planet, fleet_assignment, ct)
                dfs(next_state, remaining[:index] + remaining[index + 1:], sequence + [(planet, fleet_assignment, ct)])

        dfs(initial_state, candidates, [])
        _, best_sequence = best

        if not best_sequence:
            return []

        # Emit only the moves whose launch_turn == current step
        moves: FleetOrders = []
        for target_planet, fleet_assignment, _ in best_sequence:
            for source_id, (fleet_size, launch_turn, _) in fleet_assignment.items():
                if launch_turn != self.scene_step:
                    continue
                src = next((p for p in self.planets if p.id == source_id), None)
                if src is None:
                    continue
                angle, _, _, travel = self.intercept_planet(src.x, src.y, target_planet, fleet_size)
                if not math.isfinite(travel):
                    continue
                hit = self.first_planet_hit(src.x, src.y, angle, fleet_size, src)
                if hit is not target_planet:
                    continue
                moves.append([source_id, angle, fleet_size])

        return moves

    # ------------------------------------------------------------------

    def main(self, obs: dict[str, Any]) -> list[Any]:
        self.player = obs['player']
        self.scene_step = obs['step'] - 1
        self.angular_velocity = obs['angular_velocity']

        comet_ids = set(obs['comet_planet_ids'])
        planets_and_comets = [HPlanet(*p) for p in obs['planets']]
        self.planets = [p for p in planets_and_comets if p.id not in comet_ids]
        self.owned_planets = [p for p in self.planets if p.owner == self.player]
        self.enemy_planets = [p for p in self.planets if p.owner != self.player]
        self.fleets = [Fleet(*f) for f in obs['fleets']]

        if not self.enemy_planets:
            return []

        self.build_orbital_info(obs.get('initial_planets', []))
        self.build_proximity_graph()
        self.build_destination_list()

        if self.scene_step < self.EARLY_ROUNDS:
            moves = self.run_early_game()
            elapsed_ms = (time.perf_counter() - _t0) * 1000
            return moves

        self.build_reinforcement_targets()

        moves = []
        while True:
            move_orders = self.evaluate_move_orders()
            target_planet, _, fleet_orders, _ = move_orders
            if target_planet is None:
                break
            self.commit_move_orders(move_orders)
            moves.extend(fleet_orders)

        reinforcement_orders = self.send_reinforcements()
        if reinforcement_orders:
            moves.extend(reinforcement_orders)

        return moves


def agent(obs: dict[str, Any]) -> list[Any]:
    _agent = Hellburner()
    try:
        return _agent.main(obs)
    except Exception:
        return []

