%%writefile main.py
# ---------------------------------------------------------------------------
# PATCH NOTES (v4) -- Fix survival-mode false triggers (self-inflicted collapse)
#
# Diagnosed from 5 lost replays (81341940, 81342110, 81344073, 81354283,
# 81370266), all played as "ola sadek". Cross-referencing replay state against
# the v3 macro-phase logic step-by-step (not just at the old hoard checkpoint)
# revealed something the v3 diagnosis missed: SURVIVAL mode itself -- the
# "fight back instead of hoarding while being erased" fix from v3 -- was
# firing almost continuously, including at step 0 of every single game.
#
# Root cause: survival_planet_count=2 triggers on "owned_planets <= 2". Every
# game starts at exactly 1 planet. So survival mode (frontier_reserve_margin
# *0.12, i.e. near-zero defensive reserve, max_waves_per_turn>=10) was active
# from turn one, and kept re-triggering through the midgame any time the agent
# dipped to 1-2 planets during ordinary combat -- not just genuine last-stands.
#
# Concretely, in 81344073 at step 135 ola had owned_planets=2, ratio=0.17 (so
# survival correctly should have fired for being behind) -- but with
# frontier_reserve_margin gutted, the agent emptied BOTH of its planets in one
# turn (228->35 ships, 366->107 ships) launching two ~200+ ship offensive
# waves while leaving ~0 garrison at home. Neither wave ever landed a capture
# that stuck; both home planets fell within 2-5 steps to a trivial counter-
# attack, because there was nothing left to defend them. The same pattern
# (full-bank offensive dump + near-zero garrison right before the planet is
# lost) shows up near the collapse point in all 5 losses, not just one.
#
# Survival mode's intent (fight, don't hoard, while dying) was right. The bug
# is that it disabled defense *while* going all-in on offense, instead of
# choosing one. An agent at 1-2 planets needs to defend what it has at least
# as much as it needs to counter-attack -- emptying your last planet to send
# a wave is how you get eliminated one turn before that wave would have
# mattered anyway.
#
# FIX (three changes):
#   1. Early-game grace period: survival_grace_steps=20. Owning few planets
#      in the opening is normal start-of-game state, not a crisis -- don't
#      gate behavior on it.
#   2. Planet-count survival trigger raised from "<=2" to "<=1" (only a true
#      last-stand), with a separate softer trigger for "<=2 planets AND
#      ratio<=0.55" so genuinely-losing-with-2-planets still counts, but
#      having 2 modest planets while roughly even isn't treated as dying.
#   3. Survival mode no longer guts frontier reserve to near-zero. Reserve
#      scale raised from 0.12 to 0.45 -- still much thinner than normal play
#      (so the agent does commit more to offense than usual) but no longer
#      removes the defensive floor entirely. A last-stand agent should still
#      keep enough ships home to make the enemy pay to finish it off; an
#      empty planet falls for free and wastes the offensive wave that drained
#      it, since by the time that wave could return, there's nothing left to
#      return to.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# PATCH NOTES (v3) -- Conditional hoard + survival mode
#
# Diagnosed from 4 lost replays (81241069, 81246396, 81262906, 81266346).
# All 4 games ended via player elimination at steps 130-239 (NOT the 500-step
# scoring endpoint), so the dump phase (last 100 steps of 500 = step 400+)
# NEVER fired.  The games were already over before it was supposed to help.
#
# Root cause confirmed by replaying phase tags against every planet-loss event:
#   81241069: 13 of 19 planet losses tagged HOARD(WEAK-SHOULD-NOT-HOARD)
#   81246396: 11 of 16 planet losses tagged HOARD(WEAK-SHOULD-NOT-HOARD)
#   81262906: 16 of 24 planet losses tagged HOARD(WEAK-SHOULD-NOT-HOARD)
#   81266346: 10 of 11 planet losses tagged HOARD(WEAK-SHOULD-NOT-HOARD)
#   At the hoard trigger (step 90), strength ratios were 0.58-0.92 with
#   planet counts as low as 3.  The hoard phase fired UNCONDITIONALLY despite
#   ola being behind or equal, which turned a recoverable position into a
#   death spiral: hoard → stop attacking → lose more planets → weaker still.
#
# The previous version misread what made Isaiah's strategy work.  Isaiah
# COULD hoard because he was already WINNING (more planets, more ships).
# Hoarding while losing just compounds the deficit.  The bank never gets
# big enough to matter when you're getting eliminated before step 400.
#
# FIX (three changes that together cover all 4 failure modes):
#   1. Hoard gating: hoard only fires when ratio >= 0.95 (essentially tied
#      or ahead) AND owned_planets >= 5. Under the new rule, NONE of the 4
#      losing games would have triggered hoard at step 90.  Planet losses
#      now tagged correctly as EXPAND or SURVIVAL throughout.
#   2. Softer hoard when it DOES fire: roi_floor 2.4→1.65, max_waves 2→4.
#      The original values were extreme enough to completely freeze expansion
#      even when the agent was slightly ahead.
#   3. Survival mode (new): when ratio <= 0.32 OR planets <= 2, override
#      everything -- ROI floor to 1.05, waves to 10, reserve scale to 0.12.
#      This makes the agent fight back in a death spiral instead of hoarding
#      while being erased.
#   Also: dump_window 140→100 (fires 40 steps earlier); anti-drip floor
#   scales min_ships_to_launch with total owned mass so the agent doesn't
#   spend wave slots on 4-ship trickle attacks when it has 400 ships banked.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# PATCH NOTES (v2) -- "hoard then dump" macro phase
#
# Source: forensic analysis of 4 replays of the top leaderboard opponent
# ("Isaiah @ Tufa Labs", 80824418, 80830575, 80832496, 80831272).
# Key facts: ships on planets grow +prod/turn with NO cap; winner in every
# replay was the player with more total ships (planets + in-flight) at game
# end, even with fewer planets/production; and the winning action log showed
# a short expansion burst, a 200-300 step quiet compound phase, then a
# one-shot dump in the last 100-140 steps.
#
# FIX (v2): _suppress_late_candidates payback-time decay switched off in
# the dump window; step-gated phase config applied via _adjust_config.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# PATCH NOTES (v1) -- frontier garrison reserve
#
# Diagnosed from 4 lost replays (81124742, 81128990, 81139010, 81141173):
# every single loss followed the same pattern -- a frontline planet with a
# healthy garrison got selected as an offensive SOURCE purely because it had
# a lot of ships (source_score only rewards ships/prod/centrality), got
# drained to ~0-5 ships by an outgoing wave, and was overrun 1-3 steps later
# by an enemy fleet that only needed to match the now-tiny garrison.
#
# _build_defense_entries already projects threats to planets, but it runs
# BEFORE plan_lite_waves and has no visibility into what plan_lite_waves is
# about to drain from those same planets this turn -- so a planet can look
# "safe" to the defense pass and then get stripped bare by the offense pass
# a few lines later, with neither pass aware of the other's plan.
#
# FIX: give every potential source planet a computed "frontier reserve" --
# an estimate of how many ships a nearby enemy could plausibly throw at it
# within a short horizon (reusing the existing cheap_enemy_pressure signal,
# which the code already computed for targets but never applied to sources).
# That reserve is subtracted from what's available to drain for offense.
# Interior planets far from any enemy keep a ~0 reserve and lose no
# offensive capacity; frontline planets keep enough to survive a plausible
# counter-attack instead of being emptied out by their own agent.
# ---------------------------------------------------------------------------
from __future__ import annotations

import dataclasses
import os
import sys
from dataclasses import dataclass, replace

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _HERE = os.getcwd()
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import torch
from torch import Tensor

from orbit_lite.geometry import fleet_speed
from orbit_lite.intercept_aim import intercept_angle
from orbit_lite.movement import MovementConfig, PlanetMovement
from orbit_lite.movement_step import (
    apply_private_planned_launches,
    concat_launch_entries,
    disambiguate_duplicate_launches,
    ensure_planet_movement,
    infer_planned_launches_from_entries,
)
from orbit_lite.obs import parse_obs
from orbit_lite.distance_cache import build_distance_cache
from orbit_lite.planner_core import (
    _candidate_indices,
    _empty_entries,
    _greedy_select,
    _plan_regroup,
    build_target_shortlist,
    capture_floor,
    empty_action_row,
    entries_to_sparse_payload,
    largest_initial_player_count,
    make_launch_set,
    reachable_mask,
    reinforcement_timing_factor,
    safe_drain,
    score_candidates,
)
from orbit_lite.adapter import single_obs_to_tensor, sparse_action_row_to_moves

TOTAL_STEPS = 500


# ---------------------------------------------------------------------------
# Config – extended with dynamic knobs + defense/geometry parameters
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProducerLiteConfig:
    horizon: int = 18
    max_sources_per_lane: int = 12
    max_offensive_targets: int = 12
    max_defensive_targets: int = 6
    max_waves_per_turn: int = 6
    roi_threshold: float = 1.35
    min_ships_to_launch: float = 4.0
    reinforce_size_beta: float = 2.2
    reinforce_eta_free: float = 3.0
    reinforce_eta_scale: float = 12.0
    enable_regroup: bool = True
    max_regroup_time: float = 7.0
    regroup_pressure_delta_min: float = 0.20
    max_regroup_sources_per_lane: int = 6
    max_regroup_targets_per_source: int = 7
    regroup_pressure_norm: str = "none"
    regroup_time_penalty_weight: float = 1e-3
    min_roi: float = 1.05
    max_roi: float = 1.45
    horizon_min: int = 8
    horizon_max: int = 24
    beta_min: float = 1.2
    beta_max: float = 3.5
    defense_threat_horizon: float = 14.0
    defense_min_intercept_margin: float = 1.05
    defense_max_waves: int = 3
    geometry_weight: float = 0.35
    prod_rush_steps: int = 120
    prod_rush_top_k: int = 3
    prod_rush_roi_discount: float = 0.80
    frontier_reserve_horizon: float = 10.0
    frontier_reserve_margin: float = 1.15
    frontier_reserve_min: float = 0.0
    frontier_reserve_cap_frac: float = 0.85

    hoard_start_step: int = 90
    dump_window: int = 100            # was 140; fire dump 40 steps earlier
    hoard_roi_floor: float = 1.65     # was 2.4 -- far too extreme
    hoard_max_waves: int = 4          # was 2
    dump_roi_ceiling: float = 1.05    # was 1.10
    dump_max_waves: int = 12          # was 10
    dump_frontier_reserve_scale: float = 0.10   # was 0.15

    # Hoard gating + survival mode (see v3 patch notes above)
    hoard_min_ratio: float = 0.95     # must be >=95% of leader to hoard
    hoard_min_planets: int = 5        # must have >=5 planets to hoard
    survival_ratio: float = 0.32      # all-out fight if at <=32% of leader

    # v4: survival planet-count trigger split into a hard last-stand bound
    # and a softer bound that also requires being clearly behind, plus a
    # grace period so "1 planet" at game start isn't treated as a crisis.
    survival_planet_count: int = 1        # was 2 -- true last-stand only
    survival_soft_planet_count: int = 2   # secondary bound, needs ratio too
    survival_soft_ratio: float = 0.55     # ...and must also be behind
    survival_grace_steps: int = 20        # ignore planet-count trigger early
    survival_reserve_scale: float = 0.45  # was 0.12 -- keep a defensive floor


# ---------------------------------------------------------------------------
# Strength proxy with production weight
# ---------------------------------------------------------------------------

def _owner_strength(obs, prod: Tensor, player_count: int) -> Tensor:
    dtype = prod.dtype
    device = prod.device
    strength = torch.zeros(int(player_count), dtype=dtype, device=device)
    owner = obs.owner_abs.to(device=device)
    alive = obs.alive.to(device=device)
    ships = obs.ships.to(device=device, dtype=dtype)
    prod_v = prod.to(device=device, dtype=dtype)
    for oid in range(int(player_count)):
        mask = alive & (owner == oid)
        if bool(mask.any()):
            strength[oid] = prod_v[mask].sum() + 0.025 * ships[mask].sum()
    return strength


# ---------------------------------------------------------------------------
# Orbital centrality score
# ---------------------------------------------------------------------------

def _orbital_centrality(obs, cache) -> Tensor:
    P = int(obs.P)
    device = obs.device
    if P <= 1:
        return torch.ones(P, device=device)
    d0 = cache.cross_dist[0].clone().float()
    alive = obs.alive.to(device=device)
    d0 = torch.where(alive.view(1, P) & alive.view(P, 1), d0, torch.zeros_like(d0))
    n_alive = alive.float().sum().clamp(min=1.0)
    mean_dist = d0.sum(dim=1) / n_alive
    centrality = 1.0 / (mean_dist + 1.0)
    return centrality.to(obs.ships.dtype)


# ---------------------------------------------------------------------------
# Proactive defense
# ---------------------------------------------------------------------------

def _build_defense_entries(
    *,
    movement: PlanetMovement,
    obs,
    cache,
    config: ProducerLiteConfig,
    player_count: int,
):
    P = int(obs.P)
    device = obs.device
    dtype = obs.ships.dtype
    pid = int(obs.player_id)

    if P == 0:
        return _empty_entries(device, dtype)

    owned = obs.owned & obs.alive
    if not bool(owned.any()):
        return _empty_entries(device, dtype)

    H = min(int(config.defense_threat_horizon), int(movement.garrison_status(max_horizon=int(config.defense_threat_horizon)).ships.shape[-1]) - 1)
    if H <= 0:
        return _empty_entries(device, dtype)

    status = movement.garrison_status(max_horizon=H)
    ships_at_H = status.ships[:, -1]

    threatened = owned & (ships_at_H < 0)
    if not bool(threatened.any()):
        return _empty_entries(device, dtype)

    tgt_indices = threatened.nonzero(as_tuple=False).squeeze(1)
    src_indices = owned.nonzero(as_tuple=False).squeeze(1)

    if src_indices.numel() == 0 or tgt_indices.numel() == 0:
        return _empty_entries(device, dtype)

    d0 = cache.cross_dist[0].to(dtype)
    src_ships = obs.ships[src_indices].to(dtype)

    all_entries = []
    waves_launched = 0

    for t_i in range(int(tgt_indices.shape[0])):
        if waves_launched >= int(config.defense_max_waves):
            break
        tgt = int(tgt_indices[t_i].item())
        deficit = float(-ships_at_H[tgt].item())
        need = deficit * float(config.defense_min_intercept_margin)

        dists = d0[src_indices, tgt]
        speeds = fleet_speed(src_ships.clamp(min=1.0))
        etas = (dists / speeds.clamp(min=1e-6)).ceil()

        can_arrive = etas <= float(H)
        has_surplus = src_ships > (need + float(config.min_ships_to_launch))
        src_neq_tgt = src_indices != tgt
        valid_src = can_arrive & has_surplus & src_neq_tgt

        if not bool(valid_src.any()):
            continue

        best_src_local = int(torch.where(valid_src, dists, torch.full_like(dists, 1e9)).argmin().item())
        best_src = int(src_indices[best_src_local].item())
        send_ships = min(float(src_ships[best_src_local].item()) * 0.6,
                         need + float(config.min_ships_to_launch))
        send_ships = max(send_ships, float(config.min_ships_to_launch))

        src_t = torch.tensor([[best_src]], dtype=torch.long, device=device)
        tgt_t = torch.tensor([tgt],       dtype=torch.long, device=device)
        send_t = torch.tensor([[send_ships]], dtype=dtype, device=device)
        eta_t = torch.tensor([[float(etas[best_src_local].item())]], dtype=dtype, device=device)
        valid_t = torch.tensor([[True]], dtype=torch.bool, device=device)

        entry = make_launch_set(
            source_slots=src_t,
            target_slots=tgt_t.unsqueeze(-1).expand(1, 1),
            ships=send_t,
            eta=eta_t,
            valid=valid_t,
            player_id=pid,
        )
        all_entries.append(entry)
        waves_launched += 1

    if not all_entries:
        return _empty_entries(device, dtype)
    return concat_launch_entries(all_entries)


# ---------------------------------------------------------------------------
# Dynamic adjustment
# ---------------------------------------------------------------------------

def _adjust_config(
    config: ProducerLiteConfig,
    *,
    obs,
    prod: Tensor,
    step: int,
    player_count: int,
) -> ProducerLiteConfig:
    pid = int(obs.player_id)
    strength = _owner_strength(obs, prod, int(player_count))
    if pid < 0 or pid >= int(player_count) or strength.numel() == 0:
        return config

    my = float(strength[pid].item())
    leader = float(strength.max().item())
    ratio = my / max(leader, 1e-6)

    remaining = TOTAL_STEPS - int(step)

    # ---- ROI ----
    if ratio < 1.0:
        deficit = 1.0 - ratio
        roi_drop = 0.30 * (1.0 - torch.exp(torch.tensor(-3.0 * deficit))).item()
        if remaining < 150 and ratio < 0.90:
            time_urgency = (150 - remaining) / 150.0
            roi_drop += 0.12 * time_urgency * deficit
        new_roi = max(config.min_roi, config.max_roi - roi_drop)
        config = replace(config, roi_threshold=new_roi)

    # ---- Horizon ----
    base_horizon = float(config.horizon)
    if ratio > 1.1:
        new_horizon = max(config.horizon_min, int(base_horizon * 0.7))
    elif ratio < 0.8:
        new_horizon = min(config.horizon_max, int(base_horizon * 1.3))
    else:
        new_horizon = int(base_horizon)
    config = replace(config, horizon=new_horizon)

    # ---- Beta ----
    enemy_total = strength.sum() - my
    if enemy_total > 0:
        beta_scale = 1.0 + 0.3 * (enemy_total / (my + 1e-6)).clamp(0, 2)
        beta = max(config.beta_min, min(config.beta_max, config.reinforce_size_beta * beta_scale))
        config = replace(config, reinforce_size_beta=beta)

    # ---- Waves ----
    base_waves = int(config.max_waves_per_turn)
    if ratio < 0.70:
        base_waves = min(8, base_waves + 1)
    if remaining < 100 and ratio < 0.95:
        base_waves = min(8, base_waves + 1)
    config = replace(config, max_waves_per_turn=base_waves)

    # ---- Min launch size (base) ----
    if remaining < 100:
        min_size = max(6.0, float(config.min_ships_to_launch) + 2.0 * (1.0 - ratio))
    else:
        min_size = float(config.min_ships_to_launch)

    # ---- Anti-drip: scale min fleet size with owned ship mass ----
    # Prevents wasting wave slots on 4-ship trickle attacks when 400 ships
    # are banked. Enforces at least 3% of total owned ships per launch.
    owned_alive_mask = obs.owned & obs.alive
    total_owned_ships = float(obs.ships[owned_alive_mask].sum().item()) if bool(owned_alive_mask.any()) else 0.0
    if total_owned_ships > 80.0:
        drip_floor = min(total_owned_ships * 0.03, 40.0)
        min_size = max(min_size, drip_floor)
    config = replace(config, min_ships_to_launch=min_size)

    # ---- Count owned planets (needed for hoard gating) ----
    owned_planets = int(owned_alive_mask.sum().item())

    # ---- Tighten regroup threshold as game ends ----
    if remaining < 200:
        scale = remaining / 200.0
        tighter = max(0.05, config.regroup_pressure_delta_min * scale)
        config = replace(config, regroup_pressure_delta_min=tighter)

    # ---- Frontier reserve margin ----
    base_margin = float(config.frontier_reserve_margin)
    if ratio < 0.85:
        margin = base_margin * (1.0 + 0.5 * (0.85 - ratio))
    else:
        margin = base_margin
    if remaining < 40:
        margin = max(1.0, margin * 0.5)
    config = replace(config, frontier_reserve_margin=margin)

    # ---- Macro phase: SURVIVAL > DUMP > HOARD (gated) > EXPAND ----
    # v4: planet-count crisis trigger now needs `step >= survival_grace_steps`
    # (every game starts at 1 planet -- that's not a crisis) and is split into
    # a hard last-stand bound (<=1 planet) and a softer bound that also
    # requires being clearly behind (<=2 planets AND ratio<=0.55), so holding
    # 2 modest planets while roughly even with the leader no longer reads as
    # dying.
    past_grace = int(step) >= int(config.survival_grace_steps)
    hard_last_stand = past_grace and owned_planets <= int(config.survival_planet_count)
    soft_last_stand = (
        past_grace
        and owned_planets <= int(config.survival_soft_planet_count)
        and ratio <= float(config.survival_soft_ratio)
    )
    in_survival = (ratio <= float(config.survival_ratio)) or hard_last_stand or soft_last_stand

    in_hoard_zone = (int(step) >= int(config.hoard_start_step)
                     and remaining > int(config.dump_window))
    position_ok_to_hoard = (ratio >= float(config.hoard_min_ratio)
                             and owned_planets >= int(config.hoard_min_planets))

    if in_survival:
        config = replace(
            config,
            roi_threshold=min(config.roi_threshold, 1.05),
            max_waves_per_turn=max(config.max_waves_per_turn, 10),
            # v4: was *0.12 -- that left ~no garrison at all, so the agent
            # emptied its last planets to attack and lost them for free to
            # the next enemy fleet that arrived. *0.45 still thins the
            # reserve well below normal play (still biased toward fighting
            # back, per the original v3 intent) but keeps enough ships home
            # that the planet doesn't fall without a fight.
            frontier_reserve_margin=config.frontier_reserve_margin * float(config.survival_reserve_scale),
            regroup_pressure_delta_min=min(config.regroup_pressure_delta_min, 0.02),
        )
    elif remaining <= int(config.dump_window):
        config = replace(
            config,
            roi_threshold=min(config.roi_threshold, float(config.dump_roi_ceiling)),
            max_waves_per_turn=max(config.max_waves_per_turn, int(config.dump_max_waves)),
            frontier_reserve_margin=config.frontier_reserve_margin * float(config.dump_frontier_reserve_scale),
            regroup_pressure_delta_min=min(config.regroup_pressure_delta_min, 0.05),
        )
    elif in_hoard_zone and position_ok_to_hoard:
        # Only hoard when genuinely ahead (ratio>=0.95 AND planets>=5)
        config = replace(
            config,
            roi_threshold=max(config.roi_threshold, float(config.hoard_roi_floor)),
            max_waves_per_turn=min(config.max_waves_per_turn, int(config.hoard_max_waves)),
        )
    # else: EXPAND -- dynamic ROI/horizon already handle being-behind

    return config


# ---------------------------------------------------------------------------
# Movement + pressure helpers
# ---------------------------------------------------------------------------

def _movement_config(config: ProducerLiteConfig, *, player_count: int) -> MovementConfig:
    return MovementConfig(
        movement_horizon=int(config.horizon),
        drift_epsilon=1e-3,
        track_fleets=True,
        player_count=int(player_count),
        max_tracked_fleets=128,
    )


def cheap_enemy_pressure(obs, cache, *, horizon: float, player_id: int) -> Tensor:
    P = int(obs.P)
    device = obs.device
    dtype = obs.ships.dtype
    if P == 0:
        return torch.zeros(P, dtype=dtype, device=device)
    d0 = cache.cross_dist[0].to(dtype)
    ships = obs.ships.to(dtype)
    speeds = fleet_speed(ships.clamp(min=1e-6))
    reach_dist = (speeds.view(P, 1) * float(horizon)).clamp(min=1e-6)
    enemy = obs.alive & (obs.owner_abs >= 0) & (obs.owner_abs != int(player_id))
    eye = torch.eye(P, device=device, dtype=torch.bool)
    valid = enemy.view(P, 1) & obs.alive.view(1, P) & ~eye
    decay = (1.0 - d0 / reach_dist).clamp(min=0.0)
    contrib = torch.where(valid, ships.view(P, 1) * decay, torch.zeros_like(decay))
    return contrib.sum(dim=0)


# ---------------------------------------------------------------------------
# Late-game suppression
# ---------------------------------------------------------------------------

def _suppress_late_candidates(
    *,
    score: Tensor,
    obs,
    target_idx: Tensor,
    cand_tgt_short: Tensor,
    cand_is_def: Tensor,
    cand_eta: Tensor,
    step: int,
    player_id: int,
    dump_window: int = 100,
) -> Tensor:
    remaining = TOTAL_STEPS - int(step)
    P = int(obs.P)
    if P <= 0 or score.numel() == 0:
        return score
    device = score.device
    dtype = score.dtype
    pid = int(player_id)
    tgt_abs = target_idx[cand_tgt_short].clamp(0, P - 1)
    tgt_owner = obs.owner_abs.to(device=device)[tgt_abs].long()
    eta = cand_eta.reshape(score.shape).to(device=device, dtype=dtype)
    too_late = eta >= remaining

    if remaining > int(dump_window):
        is_neutral = tgt_owner < 0
        is_enemy = (tgt_owner >= 0) & (tgt_owner != pid) & (~cand_is_def)
        neutral_time = (remaining - eta) / max(1.0, 30.0)
        neutral_factor = torch.sigmoid(neutral_time * 0.5)
        score = torch.where(is_neutral, score * neutral_factor, score)
        enemy_time = (remaining - eta) / max(1.0, 20.0)
        enemy_factor = torch.sigmoid(enemy_time * 0.5)
        score = torch.where(is_enemy, score * enemy_factor, score)

    return torch.where(too_late, torch.full_like(score, float("-inf")), score)


# ---------------------------------------------------------------------------
# Production snowball boost
# ---------------------------------------------------------------------------

def _apply_prod_snowball_boost(
    *,
    score: Tensor,
    obs,
    target_idx: Tensor,
    cand_tgt_short: Tensor,
    prod: Tensor,
    step: int,
    config: ProducerLiteConfig,
) -> Tensor:
    if int(step) > int(config.prod_rush_steps):
        return score

    P = int(obs.P)
    device = score.device
    dtype = score.dtype

    neutral_mask = obs.owner_abs < 0
    if not bool(neutral_mask.any()):
        return score

    prod_neutral = torch.where(neutral_mask & obs.alive, prod.to(dtype), torch.zeros(P, dtype=dtype, device=device))
    if int(prod_neutral.numel()) == 0:
        return score

    top_k = min(int(config.prod_rush_top_k), int(prod_neutral.numel()))
    top_vals = torch.topk(prod_neutral, top_k).values
    if top_vals.numel() == 0:
        return score
    threshold = float(top_vals[-1].item())

    tgt_abs = target_idx[cand_tgt_short].clamp(0, P - 1)
    tgt_prod = prod.to(dtype)[tgt_abs]
    tgt_neutral = (obs.owner_abs[tgt_abs] < 0)
    is_top_prod_neutral = tgt_neutral & (tgt_prod >= threshold - 1e-6)

    boost_factor = 1.0 / float(config.prod_rush_roi_discount)
    score = torch.where(is_top_prod_neutral.reshape(score.shape), score * boost_factor, score)
    return score


# ---------------------------------------------------------------------------
# Frontier garrison reserve
# ---------------------------------------------------------------------------

def _frontier_reserve(
    *,
    obs,
    ships: Tensor,
    enemy_mass: Tensor | None,
    config: "ProducerLiteConfig",
) -> Tensor:
    device = ships.device
    dtype = ships.dtype
    P = ships.shape[0]
    if enemy_mass is None:
        return torch.zeros(P, dtype=dtype, device=device)

    pressure = enemy_mass.to(device=device, dtype=dtype)
    reserve = pressure * float(config.frontier_reserve_margin)
    reserve = torch.clamp(reserve, min=float(config.frontier_reserve_min))
    cap = ships * float(config.frontier_reserve_cap_frac)
    reserve = torch.minimum(reserve, cap)
    reserve = torch.where(obs.owned & obs.alive, reserve, torch.zeros_like(reserve))
    return reserve


# ---------------------------------------------------------------------------
# Core planner
# ---------------------------------------------------------------------------

def plan_lite_waves(
    *,
    movement: PlanetMovement,
    obs,
    obs_tensors: dict,
    cache,
    garrison_status,
    prod: Tensor,
    alive_by_step: Tensor,
    config: ProducerLiteConfig,
    player_count: int,
):
    P = obs.P
    device = obs.device
    dtype = obs.ships.dtype
    pid = int(obs.player_id)
    step = int(obs_tensors["step"].reshape(-1)[0].item())

    H_axis = int(garrison_status.ships.shape[-1])
    H = max(H_axis - 1, 0)
    K_eta = max(1, min(int(config.horizon), H))
    W = max(1, int(config.max_waves_per_turn))

    ships = obs.ships.to(dtype)
    prod_val = prod.to(dtype)

    centrality = _orbital_centrality(obs, cache)
    geo_w = float(config.geometry_weight)
    source_score = (
        (1.0 - geo_w) * (ships + 0.5 * prod_val * (ships / (ships + 1.0)))
        + geo_w * centrality * ships
    )
    source_mask = obs.owned & obs.alive & (ships >= float(config.min_ships_to_launch))
    source_score = torch.where(source_mask, source_score, torch.tensor(float("-inf"), device=device, dtype=dtype))
    S_cap = max(1, min(int(config.max_sources_per_lane), P))
    source_idx = torch.topk(source_score, min(S_cap, int(source_score.numel())), dim=0).indices
    source_exists = source_mask[source_idx]

    target_idx, target_exists = build_target_shortlist(
        obs, obs_tensors, garrison_status, cache,
        config=config, K_eta=K_eta, H=H, prod=prod, source_mask=source_mask,
    )
    if not bool(target_exists.any()):
        return _empty_entries(device, dtype)
    S = int(source_idx.shape[0])
    T = int(target_idx.shape[0])
    target_is_mine = obs.owned[target_idx.clamp(0, P - 1)]

    eta_cap = torch.full((T,), float(K_eta), dtype=dtype, device=device)

    beta = float(config.reinforce_size_beta)
    enemy_mass = (
        cheap_enemy_pressure(obs, cache, horizon=float(K_eta), player_id=pid)
        if beta > 0.0 or bool(config.enable_regroup) or float(config.frontier_reserve_margin) > 0.0
        else None
    )

    reserve_pressure = (
        cheap_enemy_pressure(obs, cache, horizon=float(config.frontier_reserve_horizon), player_id=pid)
        if float(config.frontier_reserve_margin) > 0.0 else None
    )
    frontier_reserve = _frontier_reserve(
        obs=obs, ships=ships, enemy_mass=reserve_pressure, config=config,
    )
    effective_ships = (ships - frontier_reserve).clamp(min=0.0)

    source_ships = effective_ships[source_idx.clamp(0, P - 1)].to(dtype)
    H_eff = torch.full((), float(H), dtype=dtype, device=device)
    drain = safe_drain(
        garrison_status, source_idx=source_idx, source_ships=source_ships,
        H_eff=H_eff, player_id=pid,
    )

    reinforcement = None
    if beta > 0.0:
        enemy_mass_t = enemy_mass[target_idx.clamp(0, P - 1)]
        k_arange = torch.arange(1, K_eta + 1, device=device, dtype=dtype)
        rho = reinforcement_timing_factor(
            k_arange, eta_free=float(config.reinforce_eta_free),
            eta_scale=float(config.reinforce_eta_scale),
        )
        reinforcement = beta * rho.view(1, K_eta) * enemy_mass_t.view(T, 1)
    floor = capture_floor(
        garrison_status, target_idx=target_idx, k_max=K_eta,
        capture_overhead=1.0, player_id=pid,
        reinforcement=reinforcement,
    )
    K = int(floor.shape[-1])

    sizes = drain.view(S, 1).expand(S, T).floor().clamp(min=1.0)

    active = reachable_mask(
        movement, source_idx=source_idx, target_idx=target_idx,
        fleet_sizes=sizes.unsqueeze(-1), eta_cap=eta_cap,
    ).squeeze(-1)
    aim = intercept_angle(
        movement,
        source_idx.unsqueeze(1),
        target_idx.unsqueeze(0),
        sizes,
        active=active,
    )
    angle = aim["angle"]
    eta = aim["eta"]
    viable = aim["viable"] & (eta <= eta_cap.view(1, T))

    if K > 0:
        k_arr = (eta.clamp(min=1.0, max=float(K)).ceil().long() - 1).clamp(0, K - 1)
        floor_at_arr = floor.unsqueeze(0).expand(S, T, K).gather(-1, k_arr.unsqueeze(-1)).squeeze(-1)
    else:
        floor_at_arr = torch.ones(S, T, dtype=dtype, device=device)
    clears_floor = sizes >= floor_at_arr

    src_neq_tgt = source_idx.view(S, 1) != target_idx.view(1, T)
    valid = (
        viable & clears_floor & (sizes >= float(config.min_ships_to_launch))
        & src_neq_tgt & source_exists.view(S, 1) & target_exists.view(1, T)
    )

    L = 1
    C = S * T
    cand_src = source_idx.view(S, 1).expand(S, T).reshape(C, L)
    cand_tgt_slot = target_idx.view(1, T).expand(S, T).reshape(C)
    cand_tgt_short = torch.arange(T, device=device).view(1, T).expand(S, T).reshape(C)
    cand_send = torch.where(valid, sizes, torch.zeros_like(sizes)).reshape(C, L)
    cand_angle = angle.reshape(C, L)
    cand_eta = torch.where(valid, eta, torch.ones_like(eta)).reshape(C, L)
    cand_active = valid.reshape(C, L)
    cand_valid = valid.reshape(C)
    cand_is_def = target_is_mine[cand_tgt_short]

    launches = make_launch_set(
        source_slots=cand_src,
        target_slots=cand_tgt_slot.unsqueeze(-1).expand(C, L),
        ships=cand_send,
        eta=cand_eta,
        valid=cand_active & cand_valid.unsqueeze(-1),
        player_id=pid,
    )
    score = score_candidates(
        garrison_status, prod=prod, alive_by_step=alive_by_step,
        player_count=int(player_count), launches=launches, player_id=pid,
    )

    score = _suppress_late_candidates(
        score=score, obs=obs, target_idx=target_idx,
        cand_tgt_short=cand_tgt_short, cand_is_def=cand_is_def,
        cand_eta=cand_eta, step=int(step), player_id=pid,
        dump_window=int(config.dump_window),
    )

    score = _apply_prod_snowball_boost(
        score=score, obs=obs, target_idx=target_idx,
        cand_tgt_short=cand_tgt_short, prod=prod,
        step=int(step), config=config,
    )

    score = torch.where(cand_valid, score, torch.full_like(score, float("-inf")))

    wave_entries, leftover = _greedy_select(
        P=P, W=W, device=device, dtype=dtype, score=score,
        cand_src=cand_src, cand_send=cand_send, cand_angle=cand_angle, cand_eta=cand_eta,
        cand_active=cand_active, cand_tgt_slot=cand_tgt_slot, cand_tgt_short=cand_tgt_short,
        cand_is_def=cand_is_def, source_budget=effective_ships.clone(),
        target_exists=target_exists, roi_threshold=float(config.roi_threshold),
    )

    if not bool(config.enable_regroup):
        return wave_entries

    regroup_entries = _plan_regroup(
        movement=movement, obs=obs, obs_tensors=obs_tensors, garrison_status=garrison_status,
        leftover=leftover, original_ships=obs.ships.to(dtype), pressure=enemy_mass,
        config=config, H=H,
    )
    return concat_launch_entries([wave_entries, regroup_entries])


# ---------------------------------------------------------------------------
# Turn pipeline
# ---------------------------------------------------------------------------

def run_turn(obs_tensors: dict, *, config: ProducerLiteConfig, player_count: int, memory) -> dict:
    device = obs_tensors["planets"].device
    obs = parse_obs(obs_tensors)
    P = obs.P
    if P == 0:
        return empty_action_row(device)

    movement = ensure_planet_movement(
        obs_tensors=obs_tensors,
        expected_cfg=_movement_config(config, player_count=int(player_count)),
        cached_movement=getattr(memory, "movement", None),
    )
    memory.movement = movement
    step = int(obs_tensors["step"].reshape(-1)[0].item())

    config = _adjust_config(
        config, obs=obs, prod=movement.planet_prod, step=step, player_count=int(player_count)
    )

    cache = build_distance_cache(movement, max_k=int(config.horizon))
    H = int(config.horizon)
    status = movement.garrison_status(max_horizon=H)
    alive_by_step = movement.alive_by_step[: H + 1]

    defense_entries = _build_defense_entries(
        movement=movement, obs=obs, cache=cache,
        config=config, player_count=int(player_count),
    )

    entries = plan_lite_waves(
        movement=movement, obs=obs, obs_tensors=obs_tensors, cache=cache,
        garrison_status=status, prod=movement.planet_prod,
        alive_by_step=alive_by_step, config=config, player_count=int(player_count),
    )

    entries = concat_launch_entries([defense_entries, entries])
    entries = disambiguate_duplicate_launches(entries)

    launches = infer_planned_launches_from_entries(
        obs_tensors=obs_tensors, movement=movement, entries=entries, player_id=int(obs.player_id),
    )
    apply_private_planned_launches(
        movement=movement, launches=launches, owner_id=int(obs.player_id),
        obs_tensors=obs_tensors,
    )
    planet_ids = obs_tensors["planets"][..., 0].long()
    return entries_to_sparse_payload(entries, planet_ids=planet_ids)


# ---------------------------------------------------------------------------
# Mode presets
# ---------------------------------------------------------------------------

CONFIG_2P = ProducerLiteConfig()

CONFIG_3P = replace(
    ProducerLiteConfig(),
    horizon=15,
    max_sources_per_lane=8,
    max_offensive_targets=10,
    max_defensive_targets=5,
    roi_threshold=1.30,
    prod_rush_steps=100,
)

CONFIG_4P = replace(
    ProducerLiteConfig(),
    horizon=13,
    roi_threshold=1.20,
    max_sources_per_lane=7,
    max_defensive_targets=4,
    max_waves_per_turn=5,
    max_regroup_time=6.0,
    max_regroup_targets_per_source=8,
    prod_rush_steps=80,
    geometry_weight=0.45,
)


def _config_for(player_count: int) -> ProducerLiteConfig:
    pc = int(player_count)
    if pc >= 4:
        return CONFIG_4P
    elif pc == 3:
        return CONFIG_3P
    return CONFIG_2P


# ---------------------------------------------------------------------------
# Runtime & entry point
# ---------------------------------------------------------------------------

class ProducerLiteMemory:
    def __init__(self) -> None:
        self.movement = None
        self.cached_player_count: int | None = None
        self.last_sparse_action_row: dict | None = None

    def reset(self) -> None:
        self.movement = None
        self.cached_player_count = None
        self.last_sparse_action_row = None


class ProducerLiteRuntime:
    def __init__(self, memory: ProducerLiteMemory | None = None) -> None:
        self.memory = memory if memory is not None else ProducerLiteMemory()

    def reset(self) -> None:
        self.memory.reset()

    def tensor_action(self, obs_tensors: dict):
        mem = self.memory
        if bool((obs_tensors["step"] == 0).all()):
            mem.cached_player_count = None
        if mem.cached_player_count is None:
            mem.cached_player_count = largest_initial_player_count(obs_tensors)
        config = _config_for(mem.cached_player_count)
        row = run_turn(
            obs_tensors, config=config,
            player_count=int(mem.cached_player_count), memory=mem,
        )
        mem.last_sparse_action_row = row
        return row


_RUNTIME = ProducerLiteRuntime()


def agent(obs):
    player = obs.get("player", 0) if isinstance(obs, dict) else obs.player
    player_id = int(player)
    obs_tensors = single_obs_to_tensor(obs, player_id=player_id)
    with torch.no_grad():
        sparse_row = _RUNTIME.tensor_action(obs_tensors)
    return sparse_action_row_to_moves(sparse_row, obs, player_id=player_id)

import shutil, subprocess, sys, tarfile, tempfile
from pathlib import Path

WORK = Path("/kaggle/working")
MAIN = WORK / "main.py"
ARCHIVE = WORK / "submission.tar.gz"

EXPECTED_ORBIT_LITE = {
    "__init__.py", "adapter.py", "aiming.py", "constants.py", "distance_cache.py",
    "garrison_launch.py", "geometry.py", "intercept_aim.py", "movement.py",
    "movement_aiming.py", "movement_step.py", "obs.py", "planner_core.py",
}
EXPECTED_MEMBERS = {"main.py"} | {f"orbit_lite/{name}" for name in EXPECTED_ORBIT_LITE}

def py_files(d: Path) -> set:
    return {p.name for p in d.glob("*.py")}

if not MAIN.is_file():
    print("=" * 72)
    print("ERROR: /kaggle/working/main.py does not exist.")
    print()
    print("This cell only PACKAGES main.py - it does not create it. Run the")
    print("'%%writefile main.py' code cell above first, then re-run this cell.")
    print("(Note: this cell deletes main.py after a successful build, so a")
    print("re-run also needs the %%writefile cell executed again.)")
    print("=" * 72)
    raise FileNotFoundError(MAIN)

known_layouts = [
    Path("/kaggle/input/datasets/slawekbiel/producer-orbit-wars-utils/orbit_lite"),
    Path("/kaggle/input/producer-orbit-wars-utils/orbit_lite"),
]
candidates = [d for d in known_layouts if d.is_dir()]
if not candidates:
    print("known layouts not found, scanning /kaggle/input ...")
    candidates = sorted(d for d in Path("/kaggle/input").rglob("orbit_lite") if d.is_dir())
print(f"orbit_lite candidates: {len(candidates)}")
for d in candidates:
    missing = sorted(EXPECTED_ORBIT_LITE - py_files(d))
    extra = sorted(py_files(d) - EXPECTED_ORBIT_LITE)
    print(f"  {d}\n    missing={missing or 'none'}  extra-py={extra or 'none'}")
exact = [d for d in candidates if EXPECTED_ORBIT_LITE <= py_files(d)]
assert exact, (
    "No orbit_lite directory with the expected modules found under /kaggle/input. "
    "Is the 'producer-orbit-wars-utils' dataset attached to this notebook?"
)
SRC = exact[0]
print(f"using: {SRC}")

build = Path(tempfile.mkdtemp(prefix="submission_build_"))
shutil.copy2(MAIN, build / "main.py")
(build / "orbit_lite").mkdir()
for name in sorted(EXPECTED_ORBIT_LITE):
    shutil.copy2(SRC / name, build / "orbit_lite" / name)

ARCHIVE.unlink(missing_ok=True)
with tarfile.open(ARCHIVE, "w:gz") as tar:
    for rel in sorted(EXPECTED_MEMBERS):
        tar.add(build / rel, arcname=rel)
with tarfile.open(ARCHIVE, "r:gz") as tar:
    members = {m.name for m in tar.getmembers() if m.isfile()}
print(f"\n{ARCHIVE.name}: {ARCHIVE.stat().st_size:,} bytes, {len(members)} files")
for name in sorted(members):
    print(f"  {name}")
assert members == EXPECTED_MEMBERS, (
    f"archive mismatch: missing={sorted(EXPECTED_MEMBERS - members)} "
    f"extra={sorted(members - EXPECTED_MEMBERS)}"
)

smoke = Path(tempfile.mkdtemp(prefix="submission_smoke_"))
with tarfile.open(ARCHIVE, "r:gz") as tar:
    tar.extractall(smoke)
proc = subprocess.run(
    [sys.executable, "-c",
     "import main; assert callable(main.agent), 'main.agent not callable'; "
     "print('smoke test: packaged agent imports, main.agent is callable')"],
    cwd=smoke, capture_output=True, text=True,
)
print(proc.stdout.strip())
if proc.returncode != 0:
    print(proc.stderr)
    raise RuntimeError("smoke import of the packaged agent failed (stderr above)")

shutil.rmtree(build)
shutil.rmtree(smoke)
for p in WORK.iterdir():
    if p != ARCHIVE:
        print(f"cleanup: removing {p}")
        shutil.rmtree(p) if p.is_dir() else p.unlink()
leftover = sorted(p.name for p in WORK.iterdir())
print(f"/kaggle/working contents: {leftover}")
assert leftover == [ARCHIVE.name], f"unexpected leftovers: {leftover}"
print("\nAll checks passed - submission.tar.gz is ready.")