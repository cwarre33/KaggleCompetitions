%%writefile main.py
from __future__ import annotations

import dataclasses
import os
import sys
from dataclasses import dataclass, replace

# Make the sibling ``orbit_lite`` package importable wherever this file runs.
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
# Config
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProducerLiteConfig:
    """Minimal config with dynamic-adjustment hooks."""
    # Planning
    horizon: int = 18
    max_sources_per_lane: int = 12
    max_offensive_targets: int = 12
    max_defensive_targets: int = 4
    max_waves_per_turn: int = 6
    roi_threshold: float = 1.40
    min_ships_to_launch: float = 4.0
    # Reinforcement risk (β)
    reinforce_size_beta: float = 2.2
    reinforce_eta_free: float = 3.0
    reinforce_eta_scale: float = 12.0
    # Regroup
    enable_regroup: bool = True
    max_regroup_time: float = 7.0
    regroup_pressure_delta_min: float = 0.25
    max_regroup_sources_per_lane: int = 6
    max_regroup_targets_per_source: int = 7
    regroup_pressure_norm: str = "none"
    regroup_time_penalty_weight: float = 1e-3


# ---------------------------------------------------------------------------
# Dynamic adjustment — single lightweight function
# ---------------------------------------------------------------------------

def _owner_strength(obs, prod: Tensor, player_count: int) -> Tensor:
    """Per-owner production + 2.5% ships as strength proxy. [player_count]"""
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


def _adjust_config(
    config: ProducerLiteConfig,
    *,
    obs,
    prod: Tensor,
    step: int,
    player_count: int,
) -> ProducerLiteConfig:
    """Continuous dynamic adjustment based on game state.

    Two knobs:
      1. Strength-ratio → ROI / waves (continuous, not tiered)
      2. Time remaining  → suppress late arrivals + devalue late neutrals
         (applied later in candidate scoring)
    No hard thresholds, no phase switches — smooth interpolation.
    """
    pid = int(obs.player_id)
    strength = _owner_strength(obs, prod, int(player_count))
    if pid < 0 or pid >= int(player_count) or strength.numel() == 0:
        return config

    my = float(strength[pid].item())
    leader = float(strength.max().item())
    ratio = my / max(leader, 1e-6)  # my_strength / leader_strength

    # --- ROI: continuous ramp ---
    #   ratio >= 1.0  → no change (we are leading)
    #   ratio = 0.80  → ROI - 0.05
    #   ratio = 0.50  → ROI - 0.15
    #   ratio = 0.30  → ROI - 0.25
    if ratio < 1.0:
        # deficit in [0, 1]: 0 = even, 1 = we have nothing
        deficit = 1.0 - ratio
        roi_drop = 0.25 * deficit * deficit  # quadratic: small deficit → small drop
        new_roi = max(1.10, float(config.roi_threshold) - roi_drop)
        # Late-game extra push: after step 350, if still behind, drop more
        remaining = TOTAL_STEPS - int(step)
        if remaining < 150 and ratio < 0.90:
            time_urgency = (150 - remaining) / 150.0  # 0→1 as game ends
            new_roi = max(1.10, new_roi - 0.10 * time_urgency * deficit)
        config = replace(config, roi_threshold=new_roi)

    # --- Waves: one extra wave when behind or in late game ---
    base_waves = int(config.max_waves_per_turn)
    if ratio < 0.70:
        base_waves = min(7, base_waves + 1)
    remaining = TOTAL_STEPS - int(step)
    if remaining < 100 and ratio < 0.95:
        base_waves = min(7, base_waves + 1)
    config = replace(config, max_waves_per_turn=base_waves)

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
    """Distance-decayed reachable enemy mass per planet — [P]."""
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
# Late-game candidate suppression
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
) -> Tensor:
    """Suppress attacks that arrive too late; devalue late neutral captures."""
    remaining = TOTAL_STEPS - int(step)
    # Only activate in last 120 turns
    if remaining > 120:
        return score
    P = int(obs.P)
    if P <= 0 or score.numel() == 0:
        return score
    device = score.device
    dtype = score.dtype
    pid = int(player_id)
    tgt_abs = target_idx[cand_tgt_short].clamp(0, P - 1)
    tgt_owner = obs.owner_abs.to(device=device)[tgt_abs].long()
    eta = cand_eta.reshape(score.shape).to(device=device, dtype=dtype)

    is_neutral = tgt_owner < 0
    is_enemy = (tgt_owner >= 0) & (tgt_owner != pid) & (~cand_is_def)

    # Too late to matter
    neutral_margin = max(1.0, float(remaining) - 8.0)
    enemy_margin = max(1.0, float(remaining) - 4.0)
    too_late = (is_neutral & (eta > neutral_margin)) | (is_enemy & (eta > enemy_margin))

    # Late neutrals depreciate — fewer turns to repay launch cost
    neutral_factor = ((float(remaining) - eta) / max(1.0, 80.0)).clamp(min=0.20, max=1.0)
    score = torch.where(is_neutral, score * neutral_factor, score)
    return torch.where(too_late, torch.full_like(score, float("-inf")), score)


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
    """Single-size attack planner + regroup. One candidate per (source, target)."""
    P = obs.P
    device = obs.device
    dtype = obs.ships.dtype
    pid = int(obs.player_id)
    step = int(obs_tensors["step"].reshape(-1)[0].item())

    H_axis = int(garrison_status.ships.shape[-1])
    H = max(H_axis - 1, 0)
    K_eta = max(1, min(int(config.horizon), H))
    W = max(1, int(config.max_waves_per_turn))

    source_mask = obs.owned & obs.alive & (obs.ships >= float(config.min_ships_to_launch))
    if not bool(source_mask.any()):
        return _empty_entries(device, dtype)

    S_cap = max(1, min(int(config.max_sources_per_lane), P))
    source_idx, source_exists = _candidate_indices(obs.ships, source_mask, S_cap)
    target_idx, target_exists = build_target_shortlist(
        obs, obs_tensors, garrison_status, cache,
        config=config, K_eta=K_eta, H=H, prod=prod, source_mask=source_mask,
    )
    if not bool(target_exists.any()):
        return _empty_entries(device, dtype)
    S = int(source_idx.shape[0])
    T = int(target_idx.shape[0])
    target_is_mine = obs.owned[target_idx.clamp(0, P - 1)]

    source_ships = obs.ships[source_idx.clamp(0, P - 1)].to(dtype)
    H_eff = torch.full((), float(H), dtype=dtype, device=device)
    drain = safe_drain(
        garrison_status, source_idx=source_idx, source_ships=source_ships,
        H_eff=H_eff, player_id=pid,
    )

    eta_cap = torch.full((T,), float(K_eta), dtype=dtype, device=device)

    # Enemy pressure — reused for β floor and regroup
    beta = float(config.reinforce_size_beta)
    enemy_mass = (
        cheap_enemy_pressure(obs, cache, horizon=float(K_eta), player_id=pid)
        if beta > 0.0 or bool(config.enable_regroup) else None
    )

    # Reinforcement risk floor
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

    # Single size = safe_drain (full garrison launch)
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

    # Late-game suppression
    score = _suppress_late_candidates(
        score=score, obs=obs, target_idx=target_idx,
        cand_tgt_short=cand_tgt_short, cand_is_def=cand_is_def,
        cand_eta=cand_eta, step=int(step), player_id=pid,
    )

    score = torch.where(cand_valid, score, torch.full_like(score, float("-inf")))

    wave_entries, leftover = _greedy_select(
        P=P, W=W, device=device, dtype=dtype, score=score,
        cand_src=cand_src, cand_send=cand_send, cand_angle=cand_angle, cand_eta=cand_eta,
        cand_active=cand_active, cand_tgt_slot=cand_tgt_slot, cand_tgt_short=cand_tgt_short,
        cand_is_def=cand_is_def, source_budget=obs.ships.to(dtype).clone(),
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

    # Dynamic adjustment: continuously tune ROI + waves based on game state
    config = _adjust_config(
        config, obs=obs, prod=movement.planet_prod, step=step, player_count=int(player_count)
    )

    cache = build_distance_cache(movement, max_k=int(config.horizon))
    H = int(config.horizon)
    status = movement.garrison_status(max_horizon=H)
    alive_by_step = movement.alive_by_step[: H + 1]

    entries = plan_lite_waves(
        movement=movement, obs=obs, obs_tensors=obs_tensors, cache=cache,
        garrison_status=status, prod=movement.planet_prod,
        alive_by_step=alive_by_step, config=config, player_count=int(player_count),
    )
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

CONFIG_2P = ProducerLiteConfig()  # ROI=1.40, horizon=18, waves=6

CONFIG_3P = replace(
    ProducerLiteConfig(),
    horizon=15,
    max_sources_per_lane=8,
    max_offensive_targets=10,
    max_defensive_targets=3,
    roi_threshold=1.35,
)

CONFIG_4P = replace(
    ProducerLiteConfig(),
    horizon=13,
    roi_threshold=1.25,
    max_sources_per_lane=7,
    max_defensive_targets=2,
    max_waves_per_turn=5,
    max_regroup_time=6.0,
    max_regroup_targets_per_source=8,
)


def _config_for(player_count: int) -> ProducerLiteConfig:
    pc = int(player_count)
    if pc >= 4:
        return CONFIG_4P
    elif pc == 3:
        return CONFIG_3P
    return CONFIG_2P


# ---------------------------------------------------------------------------
# Runtime
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


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def agent(obs):
    """Single-observation entry point for local play and Kaggle."""
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

# The exact payload the archive must contain - nothing more, nothing less.
EXPECTED_ORBIT_LITE = {
    "__init__.py", "adapter.py", "aiming.py", "constants.py", "distance_cache.py",
    "garrison_launch.py", "geometry.py", "intercept_aim.py", "movement.py",
    "movement_aiming.py", "movement_step.py", "obs.py", "planner_core.py",
}
EXPECTED_MEMBERS = {"main.py"} | {f"orbit_lite/{name}" for name in EXPECTED_ORBIT_LITE}


def py_files(d: Path) -> set:
    return {p.name for p in d.glob("*.py")}


# --- 0. main.py must exist (created by the %%writefile cell above) -----------
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

# --- 1. locate orbit_lite under /kaggle/input (mount layout varies) ----------
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

# --- 2. assemble a clean build tree (only the expected .py files) ------------
build = Path(tempfile.mkdtemp(prefix="submission_build_"))
shutil.copy2(MAIN, build / "main.py")
(build / "orbit_lite").mkdir()
for name in sorted(EXPECTED_ORBIT_LITE):
    shutil.copy2(SRC / name, build / "orbit_lite" / name)

# --- 3. create the archive and verify its exact contents ---------------------
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

# --- 4. smoke test: extract the archive and import the agent from it ---------
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

# --- 5. leave /kaggle/working with ONLY submission.tar.gz --------------------
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