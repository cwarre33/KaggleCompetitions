import math
import os
import time
from collections import defaultdict, namedtuple

F14_4A_2P_FOCUS_ENABLED = True
F14_4A_2P_FOCUS_DIST_BONUS = 18.0   
F14_4A_2P_FOCUS_HAMMER_BONUS = 20.0
F14_4A_2P_FOCUS_MEGA_BONUS = 100

BOARD = 100.0
CENTER_X = 50.0
CENTER_Y = 50.0
SUN_R = 10.0
SUN_SAFETY = 1.5
ROTATION_LIMIT = 50.0
LAUNCH_CLEARANCE = 0.1
MAX_SPEED = 6.0
TOTAL_STEPS = 500
SIM_HORIZON = 110
FWD_SIM_FILTER_ENABLED = True   
FWD_SIM_HORIZON = 7             
FWD_SIM_DEFENSE_CHECK = True    
FWD_SIM_RANK_BONUS_4P = 0.0     
                                
SEARCH_EXPAND_4P_ENABLED = True 
                                
                                
SEARCH_EXPAND_2P_ENABLED = True 
SEARCH_MAX_PER_SOURCE = 3       
SEARCH_MAX_ACTIONS_TO_PICK = 5    
SEARCH_MAX_ACTIONS_TO_PICK_2P = 7 
SEARCH_DISABLES_CHEAP_PICKUP = True  
HAMMER_MELIS_VERIFY = True      
SEARCH_DEPTH2_ENABLED = False   


NEUTRAL_CAP_USES_EFFECTIVE_GARRISON = True
NEUTRAL_CAP_LOOKAHEAD = 10       

N6_USE_EFFECTIVE_PRE_GARRISON = True

TERMINAL_PHASE_ENABLED = True
TERMINAL_PHASE_TURNS = 30

FLEET_INTENT_ENABLED = True
FLEET_INTENT_MIN_DROP = 8       
FLEET_INTENT_HAMMER_BONUS = 5.0 





F1B_EXPAND_BONUS_ENABLED = True
F1B_EXPAND_BONUS = 3.0   


R1_RECAPTURE_PRIORITY_ENABLED = True
R1_RECAPTURE_HAMMER_BONUS = 8.0

E2_USE_GARRISON_THRESHOLD = True


SO1_STATIC_PREFERENCE_ENABLED = True
SO1_STATIC_BONUS = 2.179862   
SO1_STATIC_BONUS_2P = 2.179862    
SO1_STATIC_BONUS_4P = 2.95474    


SP1_SPEED_AWARE_ENABLED = True
SP1_LONG_DIST_THRESHOLD = 27.637375  
SP1_LONG_DIST_SHIPS = 22         






TI1_TIE_FOR_WIN_ENABLED = True
TI1_HORIZON_TURNS = 25           
TI1_REQUIRED_EXTRA_MARGIN = 5    
TI1_TRAILING_GAP_MIN = 10        





AS1_ANTI_SECOND_ENABLED = True





FAILTOLERANT_ENABLED = True




MELIS_SANITY_ENABLED = True
MELIS_SANITY_THETA = 3.0





F16_DIVERSITY_ENABLED = True
F16_CLOSEST_PICKS = 2   
F16_PROD_PICKS = 1      



FWD_SCORE_AGG_ENABLED = True
FWD_SCORE_AGG_TURNS = (4, 8, 14, 20)





PSM_OPENING_TURN = 14
PSM_OPENING_TURN_2P = 14    
PSM_OPENING_TURN_4P = 10    


ABSORB_MIN_THREAT = 3            
ABSORB_PROJECTION_MARGIN = 0     


DEFENSE_OVERSEND = 1             
DEFENSE_OVERSEND_2P = 1    
DEFENSE_OVERSEND_4P = 0    
DEFENSE_COALITION_MAX = 2        





MIN_DISPATCH_SHIPS = 8           



F3_THREE_BUCKET_ENABLED = True
F3_SAFE_FLOOR = 5
F3_SAFE_DIST = 12.0
F3_HARD_FLOOR = 14
F3_HARD_GARRISON = 14


EXPAND_K_OPENING = 2             
EXPAND_K_MID = 1                 
EXPAND_MAX_TRAVEL_OPENING = 20
EXPAND_MAX_TRAVEL_MID = 14
EXPAND_MIN_MARGIN = 0            
EXPAND_MIN_MARGIN_4P = 3  


X8B_2P_EXTRA = 3
EXPAND_MIN_SHIPS = MIN_DISPATCH_SHIPS


EXPAND_MIN_PROD_2P = 2





TIEBREAK_ENABLED = True
TIEBREAK_EPS_FRAC = 0.005   
TIEBREAK_EPS_MIN = 1.439234      







ROT_AWARE_RANK_ENABLED = os.environ.get("V124_ROT_AWARE", "1") != "0"






VALUE_WEIGHT_2P = 4.86118
VALUE_WEIGHT_4P = float(os.environ.get("V126_VALUE_WEIGHT_4P", "2.0"))







ANTI_SNIPE_ENABLED = os.environ.get("V124_ANTI_SNIPE", "1") != "0"
ANTI_SNIPE_HORIZON = 25          
ANTI_SNIPE_2P_ONLY = False       






REACTIVE_SNIPE_PROJECTION_ENABLED = True
REACTIVE_EMIT_FRAC = 0.49629        
REACTIVE_MIN_ENEMY_SHIPS = 5     
REACTIVE_MIN_PROJECTED = 3       



SUN_SHADOW_REACTIVE_FILTER = True






COUNTER_SNIPE_ENABLED = os.environ.get("V124_COUNTER_SNIPE", "1") != "0"
COUNTER_SNIPE_2P_ONLY = False    
COUNTER_SNIPE_MAX_COST = 30
COUNTER_SNIPE_MIN_DELAY = 1
COUNTER_SNIPE_MAX_DELAY = 12








CHEAP_PICKUP_ENABLED = os.environ.get("V124_CHEAP_PICKUP", "1") != "0"
CHEAP_PICKUP_4P_ONLY = True
CHEAP_PICKUP_MAX_GARRISON = 25

CHEAP_PICKUP_MIN_PROD = int(os.environ.get("F32_CP_MIN_PROD", "2"))









ENDGAME_ROI_ENABLED = os.environ.get("V128_ENDGAME_ROI", "1") != "0"
ENDGAME_ROI_TURNS = 30






NEUTRAL_TEMPO_FILTER_ENABLED = os.environ.get("V128_TEMPO_FILTER", "1") != "0"
NEUTRAL_TEMPO_THRESHOLD = 10     






LAUNCH_BLACKOUT_ENABLED = os.environ.get("V128_LAUNCH_BLACKOUT", "1") != "0"
LAUNCH_BLACKOUT_TURNS = 10







NEUTRAL_HARD_CAP_ENABLED = os.environ.get("V128_NEUTRAL_CAP", "1") != "0"
NEUTRAL_HARD_CAP_4P = 40          
NEUTRAL_HARD_CAP_2P = 61          
NEUTRAL_WATCHLIST_MIN_DROP = 5  





LOW_PROD_NEUTRAL_SKIP_ENABLED = True
LOW_PROD_NEUTRAL_SKIP_PROD = 1       
LOW_PROD_NEUTRAL_SKIP_GARRISON = 14  







WEAKEST_TARGET_ENABLED = os.environ.get("V128_WEAKEST_TARGET", "1") != "0"
WEAKEST_TARGET_BONUS = 2.0      
WEAKEST_TARGET_MIN_STEP = 60    
WEAKEST_DONT_FINISH_SHARE = 0.05
WEAKEST_DONT_FINISH_PENALTY = 12.0  





LEADER_BASH_ENABLED = os.environ.get("V128_LEADER_BASH", "1") != "0"
LEADER_BASH_RATIO = 1.3
LEADER_BASH_BONUS = 4.0
LEADER_BASH_MIN_STEP = 60   





COALITION_ENABLED = True
COALITION_MAX_PARTICIPANTS = 3   
COALITION_NEUTRALS_ONLY = False  
COALITION_MAX_TRAVEL_BONUS = 2   
COALITION_MIN_PER_CONTRIBUTOR = 15   
COALITION_MIN_PER_CONTRIBUTOR_2P = 15    
COALITION_MIN_PER_CONTRIBUTOR_4P = 5    
COALITION_MIN_TARGET_SHIPS = 20      


HAMMER_ENABLED = True
HAMMER_STOCKPILE_MIN = 50
HAMMER_TARGET_PROD_MIN = 2
HAMMER_PROD_SHARE_TRIGGER = 0.40
HAMMER_OVERKILL_RATIO = 1.30
HAMMER_SURROUNDED_PROMOTE_TURNS = 10  
HAMMER_MAX_TRAVEL = 24                
HAMMER_ABORT_OVERRUN_RATIO = 1.329521     
HAMMER_PLAN_REVALIDATE_INTERVAL = 1   
HAMMER_MIN_PER_CONTRIBUTOR = 9        









MEGA_HAMMER_ENABLED = True



MEGA_HAMMER_4P_ONLY = True
MEGA_HAMMER_SHIPS_MIN = 300           
MEGA_HAMMER_TARGET_GARRISON_MAX = 80  
MEGA_HAMMER_MAX_TRAVEL = 40           









PROD_RESERVE_ENABLED = False          


MEGA_HAMMER_THRESHOLD_BY_PROD = {5: 200, 4: 250, 3: 300, 2: 350, 1: 400}







FRESH_CAPTURE_INHERITANCE_ENABLED = True
FRESH_CAPTURE_MAX_AGE = 5                  
MEGA_HAMMER_SHIPS_MIN_FRESH = 200          





MEGA_HAMMER_CONCENTRATE_ENABLED = True
MEGA_HAMMER_MAX_PER_TURN = 1               




MEGA_HAMMER_MELIS_VERIFY = True




MEGA_HAMMER_VERIFY_OPP_EMIT = 0.30









HAMMER_NO_THREAT_OVERSEND_ENABLED = True
HAMMER_NO_THREAT_OVERSEND_2P_ONLY = True


HAMMER_ALWAYS_OVERSEND_2P = False





HAMMER_SAFE_SURPLUS_OVERSEND_ENABLED = True
HAMMER_SAFE_SURPLUS_RATIO = 2.0  
HAMMER_OVERSEND_MAX_THREAT_RATIO = 0.3  






ACCUMULATOR_ENABLED = True
ACCUMULATOR_4P_ONLY = True                  
ACCUMULATOR_TURN_MIN = 15                   
ACCUMULATOR_LEAD_MIN_SHIPS = 100            
ACCUMULATOR_LEAD_THREAT_RATIO = 0.5         
ACCUMULATOR_FEEDER_MIN_SURPLUS = 30         
ACCUMULATOR_FEEDER_KEEP_RESERVE = 30        
ACCUMULATOR_FEEDER_MAX_TRAVEL = 30          
ACCUMULATOR_MAX_FEEDS_PER_TURN = 3          





BRAIN_LEAD_RESERVE_ENABLED = True
BRAIN_LEAD_RESERVE_4P_ONLY = True            






BRAIN_LEAD_RESERVE_MIN_SHIPS = 200




BRAIN_LEAD_RESERVE_REQUIRE_TARGET = False



BRAIN_LEAD_PREFER_FRONTIER = False
BRAIN_LEAD_FRONTIER_WEIGHT = 2.0


MEGA_HAMMER_TARGET_GARRISON_MAX_ITER_H = 100  





MULTIPRONG_ENABLED = False  
MULTIPRONG_2P_ONLY = True


MULTIPRONG_REINFORCER_MIN_RATIO = 1.0


MULTIPRONG_E_OVERKILL = 1.05

MULTIPRONG_CREDIBILITY_FACTOR = 0.6
MULTIPRONG_MAX_TRAVEL = 40       
MULTIPRONG_MIN_PER_CONTRIBUTOR = 8
MULTIPRONG_MAX_PARTICIPANTS = 3


LATE_FLUSH_REMAINING_TURNS = 25  
LATE_FLUSH_OVERKILL_RATIO = 1.05      


SOFT_DEADLINE_FRACTION = 0.82


RACE_ENABLED = True
RACE_HORIZON_TURNS = 18          
RACE_MAX_NEUTRAL_DIST = 20     
RACE_TIE_GOES_TO_LARGER = True   


PERSONALITY_ENABLED = True
PERSONALITY_AGG_HIGH = 0.30      
PERSONALITY_AGG_LOW = 0.10       
PERSONALITY_MIN_SAMPLE = 50      

MODE_PARAMS = {
    "patient": {
        "expand_k_opening": 2,            
        "expand_max_travel_opening": 22,  
        "expand_k_mid": 1,
        "expand_max_travel_mid": 14,
        "hammer_prod_share": 0.2,
        "hammer_overkill": 1.30,
        "hammer_stockpile_min": 50,       
    },
    "opportunistic": {
        "expand_k_opening": 3,            
        "expand_max_travel_opening": 22,  
        "expand_k_mid": 2,                
        "expand_max_travel_mid": 18,      
        "hammer_prod_share": 0.35,        
        "hammer_overkill": 1.30,
        "hammer_stockpile_min": 50,
    },
    "pressure": {
        "expand_k_opening": 3,            
        "expand_max_travel_opening": 22,  
        "expand_k_mid": 0,
        "expand_max_travel_mid": 9,      
        "hammer_prod_share": 0.30,        
        "hammer_overkill": 1.20,          
        "hammer_stockpile_min": 50,
    },
}










MODE_PARAMS_2P = {
    "patient": {
        "expand_k_opening": 5,            
        "expand_max_travel_opening": 35,  
        "expand_k_mid": 4,                
        "expand_max_travel_mid": 28,      
        "hammer_prod_share": 0.30,        
        "hammer_overkill": 1.15,          
        "hammer_stockpile_min": 25,       
    },
    "opportunistic": {
        "expand_k_opening": 5,
        "expand_max_travel_opening": 35,
        "expand_k_mid": 6,
        "expand_max_travel_mid": 30,
        "hammer_prod_share": 0.28,
        "hammer_overkill": 1.15,
        "hammer_stockpile_min": 25,
    },
    "pressure": {
        "expand_k_opening": 5,
        "expand_max_travel_opening": 35,
        "expand_k_mid": 2,
        "expand_max_travel_mid": 52,      
        "hammer_prod_share": 0.25,        
        "hammer_overkill": 1.177645,
        "hammer_stockpile_min": 25,
    },
}




TWO_P_PATIENT_NUDGE_TURNS = 10
TWO_P_PATIENT_ESCALATE_TURNS = 20
TWO_P_PROD_SHARE_HISTORY = 10
TWO_P_PROD_SHARE_PROGRESS_EPS = 0.005   





STOP_EXPAND_2P_ENABLED = True




STOP_EXPAND_PROD_SHARE_2P = 0.65    
STOP_EXPAND_TURN_MIN_2P = 30        






COMBAT_STOP_EXPAND_ENABLED = False      
COMBAT_STOP_EXPAND_4P_ONLY = True
COMBAT_STOP_EXPAND_TURN_MIN = 25
COMBAT_CONTACT_MIN_SHIPS = 15
COMBAT_CHEAP_GARRISON = 10              
COMBAT_CHEAP_DIST = 12.0






PROD_LAG_STOP_EXPAND_ENABLED = True
PROD_LAG_STOP_EXPAND_TURN_MIN = 25
PROD_LAG_STOP_EXPAND_THRESH_2P = 0.40   
PROD_LAG_STOP_EXPAND_THRESH_4P = 0.22   





ENEMY_TEMPO_STOP_EXPAND_ENABLED = True
ENEMY_TEMPO_STOP_EXPAND_TURN_MIN = 20
ENEMY_TEMPO_STOP_EXPAND_MIN_LAUNCHES = 2






EASY_ENEMY_STOP_EXPAND_ENABLED = False
EASY_ENEMY_STOP_EXPAND_TURN_MIN = 15
EASY_ENEMY_MAX_GARRISON = 20
EASY_ENEMY_MAX_DIST = 25.0
EASY_ENEMY_MIN_COUNT = 1





TURN_CUTOFF_STOP_EXPAND_ENABLED = True
TURN_CUTOFF_STOP_EXPAND_TURN = 80   







PROD_LEAD_STOP_EXPAND_4P_ENABLED = True
PROD_LEAD_STOP_EXPAND_4P_TURN_MIN = 25
PROD_LEAD_STOP_EXPAND_4P_THRESH = 0.35   






STOCKPILE_STOP_EXPAND_ENABLED = True
STOCKPILE_STOP_EXPAND_TURN_MIN = 20
STOCKPILE_STOP_EXPAND_MAX_GARRISON = 250  







NEUTRAL_SATURATION_STOP_EXPAND_ENABLED = False  
NEUTRAL_SATURATION_2P_ONLY = True
NEUTRAL_SATURATION_TURN_MIN = 20
NEUTRAL_SATURATION_CHEAP_GARRISON = 10
NEUTRAL_SATURATION_REACH_DIST = 30.0






Planet = namedtuple("Planet", ["id", "owner", "x", "y", "radius", "ships", "production"])
Fleet = namedtuple("Fleet", ["id", "owner", "x", "y", "angle", "from_planet_id", "ships"])






def dist(ax, ay, bx, by):
    return math.hypot(ax - bx, ay - by)


def fleet_speed(ships):
    if ships <= 1:
        return 1.0
    ratio = math.log(ships) / math.log(1000.0)
    ratio = max(0.0, min(1.0, ratio))
    return 1.0 + (MAX_SPEED - 1.0) * (ratio ** 1.5)


def orbital_radius(p):
    return dist(p.x, p.y, CENTER_X, CENTER_Y)


def is_static_planet(p):
    return orbital_radius(p) + p.radius >= ROTATION_LIMIT


def point_to_segment_distance(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    seg_sq = dx * dx + dy * dy
    if seg_sq <= 1e-9:
        return dist(px, py, x1, y1)
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / seg_sq))
    return dist(px, py, x1 + t * dx, y1 + t * dy)


def segment_hits_sun(x1, y1, x2, y2):
    return point_to_segment_distance(CENTER_X, CENTER_Y, x1, y1, x2, y2) < SUN_R + SUN_SAFETY


def launch_point(sx, sy, sr, angle):
    c = sr + LAUNCH_CLEARANCE
    return sx + math.cos(angle) * c, sy + math.sin(angle) * c


def safe_geometry(sx, sy, sr, tx, ty, tr):
    """Direct-line angle + clear travel distance, or None if the path crosses the sun."""
    angle = math.atan2(ty - sy, tx - sx)
    lx, ly = launch_point(sx, sy, sr, angle)
    hit_d = max(0.0, dist(sx, sy, tx, ty) - (sr + LAUNCH_CLEARANCE) - tr)
    ex = lx + math.cos(angle) * hit_d
    ey = ly + math.sin(angle) * hit_d
    if segment_hits_sun(lx, ly, ex, ey):
        return None
    return angle, hit_d


def estimate_arrival(sx, sy, sr, tx, ty, tr, ships):
    safe = safe_geometry(sx, sy, sr, tx, ty, tr)
    if safe is None:
        return None
    angle, total_d = safe
    turns = max(1, int(math.ceil(total_d / fleet_speed(max(1, ships)))))
    return angle, turns


def predict_planet_position(planet, initial_by_id, ang_vel, turns):
    init = initial_by_id.get(planet.id)
    if init is None:
        return planet.x, planet.y
    r = dist(init.x, init.y, CENTER_X, CENTER_Y)
    if r + init.radius >= ROTATION_LIMIT:
        return planet.x, planet.y
    cur = math.atan2(planet.y - CENTER_Y, planet.x - CENTER_X)
    new = cur + ang_vel * turns
    return CENTER_X + r * math.cos(new), CENTER_Y + r * math.sin(new)






R4_BEHIND_SUN_WAIT_ENABLED = True
R4_FUTURE_HORIZON = 10   







def predict_comet_position(planet_id, comets, turns):
    for group in comets:
        pids = group.get("planet_ids", []) if isinstance(group, dict) else []
        if planet_id not in pids:
            continue
        idx = pids.index(planet_id)
        paths = group.get("paths", []) if isinstance(group, dict) else []
        path_index = group.get("path_index", 0) if isinstance(group, dict) else 0
        if idx >= len(paths):
            return None
        path = paths[idx]
        future_idx = int(path_index) + int(turns)
        if 0 <= future_idx < len(path):
            return float(path[future_idx][0]), float(path[future_idx][1])
        return None
    return None


def predict_target_position(target, world, turns):
    """Dispatch: comets use their precomputed path; orbital planets use angular
    extrapolation; static planets stay put. Returns (x, y) or None if a comet
    has expired by `turns`."""
    if target.id in world.comet_ids:
        pos = predict_comet_position(target.id, world.comets, turns)
        if pos is not None:
            return pos
        
    return predict_planet_position(target, world.initial_by_id, world.ang_vel, turns)


AIM_MAX_ITERS = 6          
AIM_CONVERGE_TURNS = 2
AIM_CONVERGE_DIST = 0.6


def aim_at_target(src, target, ships, initial_by_id, ang_vel, world=None):
    """Returns (angle, turns) for sending `ships` from src to hit target.
    Iterates orbital prediction. Returns None if the path is blocked by the
    sun OR if convergence isn't reached — better to skip a target than fire
    a fleet that wanders past it because our aim didn't settle.

    V13.3 Q1: when target is a comet AND world is passed, use comet path for
    future-position; otherwise existing orbital extrapolation.

    V13.3 R4 (behind-sun wait): if the FIRST estimate fails (current path
    blocked by sun), try aiming at projected future positions of the target
    where the orbital motion may have cleared the path. We launch NOW aiming
    at where the target WILL be — fleet flies straight, target swings into
    place. Better than rejecting the shot entirely."""
    est = estimate_arrival(src.x, src.y, src.radius, target.x, target.y, target.radius, ships)
    if est is None and R4_BEHIND_SUN_WAIT_ENABLED and world is not None:
        
        for future_t in range(2, R4_FUTURE_HORIZON, 2):
            if target.id in world.comet_ids:
                pos = predict_comet_position(target.id, world.comets, future_t)
            else:
                init = initial_by_id.get(target.id)
                if init is None:
                    pos = None
                elif dist(init.x, init.y, CENTER_X, CENTER_Y) + init.radius >= ROTATION_LIMIT:
                    pos = None  
                else:
                    pos = predict_planet_position(target, initial_by_id, ang_vel, future_t)
            if pos is None:
                continue
            est = estimate_arrival(src.x, src.y, src.radius, pos[0], pos[1], target.radius, ships)
            if est is not None:
                break
    if est is None:
        return None
    
    is_comet = world is not None and target.id in world.comet_ids
    if not is_comet:
        init = initial_by_id.get(target.id)
        if init is None:
            return est
        if dist(init.x, init.y, CENTER_X, CENTER_Y) + init.radius >= ROTATION_LIMIT:
            return est

    angle, turns = est
    tx, ty = target.x, target.y
    for _ in range(AIM_MAX_ITERS):
        if is_comet:
            pos = predict_comet_position(target.id, world.comets, turns)
            if pos is None:
                
                return None
            ntx, nty = pos
        else:
            ntx, nty = predict_planet_position(target, initial_by_id, ang_vel, turns)
        nest = estimate_arrival(src.x, src.y, src.radius, ntx, nty, target.radius, ships)
        if nest is None:
            return None
        nangle, nturns = nest
        if (abs(ntx - tx) < AIM_CONVERGE_DIST
                and abs(nty - ty) < AIM_CONVERGE_DIST
                and abs(nturns - turns) <= AIM_CONVERGE_TURNS):
            return nangle, nturns
        angle, turns = nangle, nturns
        tx, ty = ntx, nty
    
    return None


def fleet_target_planet(fleet, planets, initial_by_id=None, ang_vel=0.0):
    """Which planet this in-flight fleet hits, and when (in turns from now).

    Two-pass: static planets via cheap straight-line intersection, orbital
    planets via per-turn forward simulation. The naive straight-line check
    against the planet's CURRENT position misses orbital targets — the
    planet has rotated since the fleet launched, so the ray won't intersect
    its current XY but WILL intersect its future orbital position. Without
    accounting for this, incoming hostile fleets at our orbital planets
    don't show up in arrivals_by_planet, and the reservation walk wrongly
    decides our planet is safe and lets it fire offensively.
    """
    dx_dir = math.cos(fleet.angle)
    dy_dir = math.sin(fleet.angle)
    speed = fleet_speed(fleet.ships)

    def _is_orbital(p):
        if initial_by_id is None:
            return False
        init = initial_by_id.get(p.id)
        if init is None:
            return False
        return dist(init.x, init.y, CENTER_X, CENTER_Y) + init.radius < ROTATION_LIMIT

    best_p, best_t = None, float(SIM_HORIZON) + 1.0

    
    
    
    for p in planets:
        if _is_orbital(p):
            continue
        dx = p.x - fleet.x
        dy = p.y - fleet.y
        proj = dx * dx_dir + dy * dy_dir
        if proj < 0:
            continue
        perp_sq = dx * dx + dy * dy - proj * proj
        rr = p.radius * p.radius
        if perp_sq >= rr:
            continue
        hit_d = max(0.0, proj - math.sqrt(max(0.0, rr - perp_sq)))
        t = hit_d / speed
        if t <= SIM_HORIZON and t < best_t:
            best_t, best_p = t, p

    
    
    
    if initial_by_id is not None:
        best_dsq = None
        max_t = int(math.ceil(min(best_t, float(SIM_HORIZON))))
        for t in range(1, max_t + 1):
            fx = fleet.x + dx_dir * speed * t
            fy = fleet.y + dy_dir * speed * t
            for p in planets:
                if not _is_orbital(p):
                    continue
                px, py = predict_planet_position(p, initial_by_id, ang_vel, t)
                rr = p.radius * p.radius
                dsq = (fx - px) ** 2 + (fy - py) ** 2
                if dsq < rr:
                    if t < best_t or (t == best_t and (best_dsq is None or dsq < best_dsq)):
                        best_t, best_p, best_dsq = float(t), p, dsq
            if best_p is not None and best_t <= t:
                break

    if best_p is None:
        return None, None
    return best_p, max(1, int(math.ceil(best_t)))






def garrison_at_arrival(target, travel_turns):
    """Defender ship count at the moment our fleet lands."""
    if target.owner == -1:
        return int(target.ships)  
    return int(target.ships) + int(target.production) * int(travel_turns)


def needed_to_capture(target, travel_turns):
    """Ships required at arrival to flip ownership (combat: survivor > garrison)."""
    return garrison_at_arrival(target, travel_turns) + 1









EFFECTIVE_GARRISON_ENABLED = True

def effective_garrison_at_arrival(target, travel_turns, world):
    """Defender count at our arrival, accounting for pre-arrival enemy fleets.
    Returns (projected_owner, projected_ships) at travel_turns."""
    if not EFFECTIVE_GARRISON_ENABLED:
        return target.owner, garrison_at_arrival(target, travel_turns)
    arrivals = world.arrivals_by_planet.get(target.id, [])
    
    
    
    if world.is_2p:
        relevant = sorted(
            ((eta, owner, ships) for eta, owner, ships in arrivals
             if 1 <= eta <= travel_turns and ships > 0 and owner != -1),
            key=lambda x: x[0],
        )
    else:
        relevant = sorted(
            ((eta, owner, ships) for eta, owner, ships in arrivals
             if 1 <= eta <= travel_turns and owner != world.player and ships > 0
             and owner != -1),
            key=lambda x: x[0],
        )
    if not relevant:
        return target.owner, garrison_at_arrival(target, travel_turns)
    owner = int(target.owner)
    ships = int(target.ships)
    prod = max(0, int(target.production))
    last_t = 0
    for eta, fleet_owner, fleet_ships in relevant:
        
        if owner != -1:
            ships += prod * (eta - last_t)
        if fleet_owner == owner:
            ships += fleet_ships  
        else:
            if fleet_ships > ships:
                owner = int(fleet_owner)
                ships = fleet_ships - ships
            elif fleet_ships < ships:
                ships -= fleet_ships
            else:
                ships = 0  
        last_t = eta
    
    if owner != -1:
        ships += prod * (travel_turns - last_t)
    return owner, ships


def effective_needed_to_capture(target, travel_turns, world):
    """needed_to_capture with effective_garrison_at_arrival projection."""
    _, defender_ships = effective_garrison_at_arrival(target, travel_turns, world)
    return defender_ships + 1






def collect_arrivals(planet_id, fleets, planets, initial_by_id=None, ang_vel=0.0):
    """For a given planet, return [(eta, owner, ships)] of all fleets converging on it."""
    out = []
    for f in fleets:
        if int(f.ships) <= 0:
            continue
        target, eta = fleet_target_planet(f, planets, initial_by_id, ang_vel)
        if target is None or target.id != planet_id:
            continue
        out.append((eta, int(f.owner), int(f.ships)))
    return out


def compute_planet_reserve(planet, arrivals, player):
    """The minimum ships we must keep on the surface so the running balance never
    dips below ABSORB_PROJECTION_MARGIN through every incoming fleet's arrival,
    factoring production growth and friendly reinforcements.

    Returns (reserve, holds, deficit, deadline).
        reserve   int, ships that must NOT be sent out this turn.
        holds     True if reserve <= planet.ships (planet survives on its own).
        deficit   ships we still need from outside if !holds (else 0).
        deadline  earliest turn balance dips below margin if !holds (else None).

    V12.3c4 (2.4 redesign): per-fleet ABSORB_MIN_THREAT filter replaced
    with window-aggregated check. Window = garrison/production (the
    planet's natural absorb cycle). If sum(hostile_in_window) < threshold,
    ignore all hostile fleets within the window. Hostile fleets outside
    the window are always counted (they're far out enough that natural
    growth doesn't cover them and they aren't simple noise). Closes the
    Stackelberg-leader exploit (firing many sub-threshold fleets) without
    triggering absorb on transient noise the planet would have absorbed.
    """
    if planet.owner != player:
        return 0, True, 0, None

    prod = max(0, int(planet.production))
    ships_now = max(0, int(planet.ships))
    if prod > 0:
        absorb_window = max(1, ships_now // prod)
    else:
        absorb_window = SIM_HORIZON

    hostile_in_window = 0
    for eta, owner, ships in arrivals:
        if ships <= 0 or owner == player or owner == -1:
            continue
        if int(eta) <= absorb_window:
            hostile_in_window += int(ships)
    
    
    
    
    
    absorb_min_threat = max(1, min(ABSORB_MIN_THREAT, ships_now // 3))
    skip_in_window_hostiles = hostile_in_window < absorb_min_threat

    
    
    
    
    
    friendly_events = defaultdict(int)
    hostile_by_owner = defaultdict(lambda: defaultdict(int))
    for eta, owner, ships in arrivals:
        if ships <= 0:
            continue
        if owner == player:
            friendly_events[eta] += ships
        elif owner == -1:
            continue
        else:
            if skip_in_window_hostiles and int(eta) <= absorb_window:
                continue
            hostile_by_owner[eta][owner] += int(ships)

    events = defaultdict(int)
    for eta, ships in friendly_events.items():
        events[eta] += ships
    for eta, owner_totals in hostile_by_owner.items():
        
        
        sorted_h = sorted(owner_totals.values(), reverse=True)
        if len(sorted_h) == 1:
            survivor = sorted_h[0]
        elif sorted_h[0] == sorted_h[1]:
            survivor = 0
        else:
            survivor = sorted_h[0] - sorted_h[1]
        events[eta] -= survivor

    if not events:
        return 0, True, 0, None

    growth = int(planet.production)
    bal = int(planet.ships)
    last_t = 0
    min_bal = bal
    deadline = None

    for turn in sorted(events):
        bal += growth * (turn - last_t)
        bal += events[turn]
        if bal < min_bal:
            min_bal = bal
        if bal < ABSORB_PROJECTION_MARGIN and deadline is None:
            deadline = turn
        last_t = turn

    if min_bal >= ABSORB_PROJECTION_MARGIN:
        excess = min_bal - ABSORB_PROJECTION_MARGIN
        reserve = max(0, int(planet.ships) - excess)
        return reserve, True, 0, None

    deficit = ABSORB_PROJECTION_MARGIN - min_bal
    return int(planet.ships), False, int(deficit), deadline






def forward_project(world, our_capture_target=None, our_capture_turn=None,
                    our_capture_ships=None, horizon=20,
                    project_opponent_moves=False,
                    opponent_emit_fraction=0.4,
                    snapshot_turns=None):
    """Project every planet's owner+ship count forward `horizon` turns.

    Inputs:
      world — current World snapshot.
      our_capture_target/turn/ships — optional our planned capture (treated
        as a hypothetical friendly fleet arrival).
      horizon — how many turns to project.
      project_opponent_moves — if True, each enemy planet launches a fraction
        of its CURRENT surplus toward its closest non-friendly target every
        few turns. Increases accuracy at cost of pessimism for our holdings.
      opponent_emit_fraction — fraction of surplus the projected launch sends.
    Returns:
      dict planet_id -> (owner_at_H, ships_at_H).

    Model:
      - Existing in-flight fleets arrive at their projected ETA (engine
        combat math: attackers fight each other top-minus-second, then
        survivor reinforces or attacks defender garrison).
      - Production accumulates each turn for owned planets.
      - Phantom launches: each enemy planet within max-speed reach of
        our_capture_target projects a fleet of size phantom_factor*ships
        with optimistic ETA. This catches the dominant snipe risk that
        existing arrivals_by_planet misses (the enemy hasn't launched yet
        but COULD before our planet stabilises).
    """
    
    by_pid = defaultdict(list)
    for pid, arrs in world.arrivals_by_planet.items():
        for eta, owner, ships in arrs:
            if 0 < eta <= horizon:
                by_pid[pid].append((int(eta), int(owner), int(ships)))

    

    
    if our_capture_target is not None and our_capture_turn is not None:
        by_pid[our_capture_target].append(
            (int(our_capture_turn), int(world.player), int(our_capture_ships))
        )

    
    state = {}
    for p in world.planets:
        state[p.id] = [int(p.owner), int(p.ships), int(p.production)]

    
    
    
    planet_pos_map = {p.id: (float(p.x), float(p.y)) for p in world.planets}
    pid_list = list(state.keys())

    
    prod_by_pid = {p.id: max(0, int(p.production)) for p in world.planets}

    snapshots = {} if snapshot_turns else None
    snapshot_set = set(snapshot_turns) if snapshot_turns else None
    for t in range(1, horizon + 1):
        
        for pid, st in state.items():
            if st[0] != -1:
                st[1] += st[2]
        
        
        
        if project_opponent_moves and t % 4 == 0:
            for pid, st in state.items():
                if st[0] == -1 or st[1] < 10:
                    continue
                src_x, src_y = planet_pos_map[pid]
                src_owner = st[0]
                best_d = float("inf")
                best_op = None
                for opid, ost in state.items():
                    if opid == pid or ost[0] == src_owner:
                        continue
                    ox, oy = planet_pos_map[opid]
                    d = ((src_x - ox) ** 2 + (src_y - oy) ** 2) ** 0.5
                    if d < best_d:
                        best_d, best_op = d, opid
                if best_op is None:
                    continue
                
                if src_owner == world.player:
                    frac = opponent_emit_fraction * 0.5
                else:
                    frac = opponent_emit_fraction
                emit = int(st[1] * frac)
                if emit < 5:
                    continue
                ratio = math.log(max(2, emit)) / math.log(1000.0)
                speed = 1.0 + (MAX_SPEED - 1.0) * (ratio ** 1.5)
                eta_arrive = max(1, int(math.ceil(best_d / speed)))
                arrival_t = t + eta_arrive
                if arrival_t > horizon:
                    continue
                by_pid[best_op].append((arrival_t, src_owner, emit))
                st[1] -= emit
        
        
        
        
        
        for pid, arrs in by_pid.items():
            this_turn = [(o, s) for et, o, s in arrs if et == t]
            if not this_turn:
                continue
            st = state[pid]
            defender_owner, garrison = st[0], st[1]
            from_owner = defaultdict(int)
            for o, s in this_turn:
                from_owner[o] += s
            sorted_owners = sorted(from_owner.items(), key=lambda x: -x[1])
            top_owner, top_ships = sorted_owners[0]
            if len(sorted_owners) >= 2:
                second_ships = sorted_owners[1][1]
                if top_ships == second_ships:
                    survivor_ships = 0
                    survivor_owner = -1
                else:
                    survivor_ships = top_ships - second_ships
                    survivor_owner = top_owner
            else:
                survivor_ships = top_ships
                survivor_owner = top_owner
            if survivor_ships > 0:
                if defender_owner == survivor_owner:
                    st[1] = garrison + survivor_ships
                else:
                    new_garrison = garrison - survivor_ships
                    if new_garrison < 0:
                        st[0] = survivor_owner
                        st[1] = -new_garrison
                    else:
                        st[1] = new_garrison
        if snapshot_set is not None and t in snapshot_set:
            snapshots[t] = {pid: (st[0], st[1]) for pid, st in state.items()}

    final = {pid: (st[0], st[1]) for pid, st in state.items()}
    if snapshot_turns is not None:
        return final, snapshots
    return final


def _depth2_penalty(world, our_action, top_opp_actions=2):
    """For our action, project worst-case opponent reply.
    Each enemy planet within reach of our_action's target tries to launch a
    counter-snipe. Returns the WORST (lowest from our POV) Melis score among
    those counter-snipe scenarios.

    Used to penalize our actions that invite easy counter-snipes.
    """
    target_id = our_action["target_id"]
    tgt = world.planet_by_id.get(target_id)
    if tgt is None:
        return 0.0
    worst_delta = 0.0
    candidates_evaluated = 0
    for ep in world.planets:
        if ep.owner == world.player or ep.owner == -1:
            continue
        if int(ep.ships) < 9:
            continue
        d = ((tgt.x - ep.x) ** 2 + (tgt.y - ep.y) ** 2) ** 0.5
        if d > 30.0:
            continue
        
        opp_ships = max(8, int(ep.ships) - 5)
        ratio = math.log(max(2, opp_ships)) / math.log(1000.0)
        speed = 1.0 + (MAX_SPEED - 1.0) * (ratio ** 1.5)
        opp_eta = max(1, int(math.ceil(d / speed)))
        if opp_eta > FWD_SIM_HORIZON + 4:
            continue
        
        proj = forward_project(
            world,
            our_capture_target=our_action["target_id"],
            our_capture_turn=our_action["arrival_turn"],
            our_capture_ships=our_action["ships"],
            horizon=FWD_SIM_HORIZON + 6,
            project_opponent_moves=True,
            opponent_emit_fraction=0.30,
        )
        
        
        
        end_owner, end_ships = proj.get(target_id, (-1, 0))
        
        if end_owner != world.player and opp_ships > end_ships:
            worst_delta = min(worst_delta, -opp_ships)
        candidates_evaluated += 1
        if candidates_evaluated >= top_opp_actions:
            break
    return worst_delta


def search_step_action(world, max_per_source=3, max_actions_to_eval=10,
                       use_depth2=False):
    """Depth-1 alpha-beta over step actions.

    1. Generate candidate step actions via generate_step_actions.
    2. Evaluate each via melis_evaluate (sim+score).
    3. Return list sorted by score (highest first), up to `max_actions_to_eval`.

    Each action has additional key "score". Caller picks top action(s) and
    commits via _commit_fleet.
    """
    actions = generate_step_actions(world, max_per_source=max_per_source)
    if not actions:
        return []
    baseline_score = melis_evaluate(world, our_step_action=None)
    
    
    
    apply_decay = world.is_2p
    scored = []
    for act in actions[:max_actions_to_eval]:
        act_score = melis_evaluate(world, our_step_action=act)
        gain = act_score - baseline_score
        if apply_decay and gain > 0:
            gain *= 0.97 ** int(act["arrival_turn"])
        act["score"] = gain
        scored.append(act)
    scored.sort(key=lambda a: (-a["score"], a.get("raw_dist", 0.0)))
    if use_depth2:
        
        for act in scored[:3]:
            act["score"] += _depth2_penalty(world, act)
        scored.sort(key=lambda a: (-a["score"], a.get("raw_dist", 0.0)))
    
    
    if MELIS_SANITY_ENABLED and world.is_2p and scored and scored[0]["score"] < MELIS_SANITY_THETA:
        return []
    return scored


def generate_step_actions(world, max_per_source=3):
    """Generate candidate "step actions" — Melis style. Each step action is
    a single capture targeting one planet, sourced from one of our planets.

    Returns list of dicts: {"target_id", "source_id", "angle", "arrival_turn",
                            "ships", "raw_dist"}.

    Pruning:
      - Skip targets that aren't reachable within max_travel + 4
      - Skip neutral targets blocked by NEUTRAL_HARD_CAP
      - Take top `max_per_source` per source (closest by raw distance)
    """
    actions = []
    if not world.my_planets:
        return actions
    
    is_opening = world.is_opening
    if is_opening:
        max_travel = world.mode_params.get(
            "expand_max_travel_opening", EXPAND_MAX_TRAVEL_OPENING)
    else:
        max_travel = world.mode_params["expand_max_travel_mid"]

    for src in world.my_planets:
        avail = max(0, int(src.ships))
        if avail < MIN_DISPATCH_SHIPS:
            continue
        targets = []
        for t in world.planets:
            if t.owner == world.player:
                continue
            if not is_targetable(world, t):
                continue
            if _neutral_blocked_by_cap(world, t):
                continue
            raw = dist(src.x, src.y, t.x, t.y)
            if raw / MAX_SPEED > max_travel + 4:
                continue
            targets.append((raw, t))
        targets.sort(key=lambda x: x[0])
        
        if F16_DIVERSITY_ENABLED:
            n_close = min(F16_CLOSEST_PICKS, max_per_source)
            picks = list(targets[:n_close])
            picked_ids = {p[1].id for p in picks}
            extras = [(raw, t) for raw, t in targets if t.id not in picked_ids]
            extras.sort(key=lambda x: (-int(x[1].production), x[0]))
            picks.extend(extras[:F16_PROD_PICKS])
        else:
            picks = targets[:max_per_source]
        for raw, t in picks:
            plan = plan_solo_capture(world, src, t, avail, max_travel)
            if plan is None:
                continue
            angle, turns, ships = plan
            actions.append({
                "target_id": int(t.id),
                "source_id": int(src.id),
                "angle": float(angle),
                "arrival_turn": int(turns),
                "ships": int(ships),
                "raw_dist": float(raw),
            })
    return actions


def melis_evaluate(world, our_step_action=None, horizon=12, future_horizon=8,
                   opp_emit=0.20):
    """Melis full-attack-future evaluator.

    Inputs:
      world — current World snapshot.
      our_step_action — optional dict {"target_id", "arrival_turn", "ships"}.
        If provided, simulates our planned capture as part of the projection.
      horizon — short-term sim horizon for our action's effect.
      future_horizon — additional "all-attack-future" projection turns where
        every planet (us + opponents) keeps emitting surplus toward closest
        non-friendly. Captures position quality beyond the immediate move.
      opp_emit — fraction of surplus opponents launch in projection. 0.30
        is the calibrated default; lower = more capture-friendly.

    Returns: scalar score from our player's POV (higher = better).
    """
    target = arrival = ships = None
    if our_step_action is not None:
        target = our_step_action.get("target_id")
        arrival = our_step_action.get("arrival_turn")
        ships = our_step_action.get("ships")
    H = horizon + future_horizon
    n = 2 if world.is_2p else 4
    if FWD_SCORE_AGG_ENABLED:
        snap_turns = tuple(t for t in FWD_SCORE_AGG_TURNS if t <= H)
        if not snap_turns:
            snap_turns = (H,)
        final, snaps = forward_project(
            world,
            our_capture_target=target,
            our_capture_turn=arrival,
            our_capture_ships=ships,
            horizon=H,
            project_opponent_moves=True,
            opponent_emit_fraction=opp_emit,
            snapshot_turns=snap_turns,
        )
        total = 0.0
        count = 0
        for t in snap_turns:
            snap = snaps.get(t)
            if snap is None:
                continue
            total += forward_score(snap, world.player, n, world)
            count += 1
        if H not in snap_turns:
            total += forward_score(final, world.player, n, world)
            count += 1
        return total / max(1, count)
    state = forward_project(
        world,
        our_capture_target=target,
        our_capture_turn=arrival,
        our_capture_ships=ships,
        horizon=H,
        project_opponent_moves=True,
        opponent_emit_fraction=opp_emit,
    )
    return forward_score(state, world.player, n, world)


def forward_score(state, player, n_seats, world=None):
    """Score a forward-projected state from `player`'s POV.

    Combines: ship advantage + 5×planet-count advantage + 8×production advantage.
    Weights chosen so an extra owned planet is worth ~5 ships (a typical garrison)
    and an extra production unit is worth ~8 ships (≈2 turns of growth)."""
    n_planets = [0] * n_seats
    n_prod = [0] * n_seats
    n_ships = [0] * n_seats
    for pid, (o, s) in state.items():
        if 0 <= o < n_seats:
            n_ships[o] += s
            n_planets[o] += 1
            if world is not None:
                p = world.planet_by_id.get(pid)
                if p is not None:
                    n_prod[o] += int(p.production)
    if n_seats <= 1:
        return n_ships[player]
    others = [i for i in range(n_seats) if i != player]
    leader_ships = max(n_ships[i] for i in others)
    leader_planets = max(n_planets[i] for i in others)
    leader_prod = max(n_prod[i] for i in others)
    return ((n_ships[player] - leader_ships)
            + 5 * (n_planets[player] - leader_planets)
            + 8 * (n_prod[player] - leader_prod))






class World:
    def __init__(self, obs, inferred_step=None):
        
        
        global COALITION_MIN_PER_CONTRIBUTOR, DEFENSE_OVERSEND, PSM_OPENING_TURN, SO1_STATIC_BONUS
        self.player = _read(obs, "player", 0)
        obs_step = _read(obs, "step", 0) or 0
        self.step = max(obs_step, inferred_step or 0)
        raw_planets = _read(obs, "planets", []) or []
        raw_fleets = _read(obs, "fleets", []) or []
        raw_init = _read(obs, "initial_planets", []) or []
        self.ang_vel = _read(obs, "angular_velocity", 0.0) or 0.0

        self.planets = [Planet(*p) for p in raw_planets]
        self.fleets = [Fleet(*f) for f in raw_fleets]
        self.initial_by_id = {Planet(*p).id: Planet(*p) for p in raw_init}

        
        
        
        raw_comet_ids = _read(obs, "comet_planet_ids", []) or []
        self.comet_ids = set(int(x) for x in raw_comet_ids)
        
        
        
        self.comet_remaining = {}
        raw_comet_groups = _read(obs, "comets", []) or []
        
        
        
        self.comets = raw_comet_groups
        for grp in raw_comet_groups:
            try:
                idx = int(grp.get("path_index", 0))
                pids = grp.get("planet_ids", []) or []
                paths = grp.get("paths", []) or []
                for i, pid in enumerate(pids):
                    if i < len(paths):
                        rem = max(0, len(paths[i]) - idx)
                        self.comet_remaining[int(pid)] = rem
            except (AttributeError, TypeError, IndexError):
                continue

        self.planet_by_id = {p.id: p for p in self.planets}
        self.my_planets = [p for p in self.planets if p.owner == self.player]
        self.enemy_planets = [p for p in self.planets if p.owner not in (-1, self.player)]
        self.neutral_planets = [p for p in self.planets if p.owner == -1]

        self.remaining_steps = max(1, TOTAL_STEPS - self.step)
        self.is_opening = self.step < PSM_OPENING_TURN
        self.is_late = self.remaining_steps < LATE_FLUSH_REMAINING_TURNS

        
        self.owner_strength = defaultdict(int)
        self.owner_production = defaultdict(int)
        for p in self.planets:
            if p.owner != -1:
                self.owner_strength[p.owner] += int(p.ships)
                self.owner_production[p.owner] += int(p.production)
        for f in self.fleets:
            self.owner_strength[f.owner] += int(f.ships)

        self.my_prod = self.owner_production.get(self.player, 0)
        self.total_prod = sum(self.owner_production.values())
        self.my_prod_share = (self.my_prod / self.total_prod) if self.total_prod else 0.0
        
        if self.remaining_steps < 80 and self.my_prod_share > 0.55:
            self.is_late = True

        
        self.leader_id = None
        self.contest_leader = False

        
        
        
        
        self.owner_planet_count = defaultdict(int)
        for p in self.planets:
            if p.owner not in (-1,):
                self.owner_planet_count[p.owner] += 1
        self.weakest_enemy = None
        self.weakest_enemy_prod_share = 0.0
        if self.total_prod > 0:
            best_score = None
            for owner in self.owner_production.keys():
                if owner in (-1, self.player):
                    continue
                score = (
                    self.owner_production.get(owner, 0) * 0.5
                    + self.owner_strength.get(owner, 0) * 0.3
                    + self.owner_planet_count.get(owner, 0) * 0.2
                )
                if best_score is None or score < best_score:
                    best_score = score
                    self.weakest_enemy = owner
            if self.weakest_enemy is not None:
                their_prod = self.owner_production.get(self.weakest_enemy, 0)
                self.weakest_enemy_prod_share = (
                    their_prod / self.total_prod if self.total_prod else 0.0
                )

        
        
        
        
        
        self.arrivals_by_planet = defaultdict(list)
        for f in self.fleets:
            target, eta = fleet_target_planet(f, self.planets, self.initial_by_id, self.ang_vel)
            if target is None:
                continue
            self.arrivals_by_planet[target.id].append((eta, int(f.owner), int(f.ships)))

        
        
        
        
        self.enemy_race_eta = _compute_enemy_race_eta(self) if RACE_ENABLED else {}

        
        
        
        
        global _game_num_players
        if _game_num_players is None and self.planets:
            _game_num_players = self.num_players
        self.is_2p = (_game_num_players == 2)

        
        
        if self.is_2p:
            COALITION_MIN_PER_CONTRIBUTOR = COALITION_MIN_PER_CONTRIBUTOR_2P
            DEFENSE_OVERSEND = DEFENSE_OVERSEND_2P
            PSM_OPENING_TURN = PSM_OPENING_TURN_2P
            SO1_STATIC_BONUS = SO1_STATIC_BONUS_2P
        else:
            COALITION_MIN_PER_CONTRIBUTOR = COALITION_MIN_PER_CONTRIBUTOR_4P
            DEFENSE_OVERSEND = DEFENSE_OVERSEND_4P
            PSM_OPENING_TURN = PSM_OPENING_TURN_4P
            SO1_STATIC_BONUS = SO1_STATIC_BONUS_4P
        
        
        
        if LEADER_BASH_ENABLED and not self.is_2p:
            lead_scores = {}
            for owner in self.owner_production.keys():
                if owner == -1:
                    continue
                lead_scores[owner] = (
                    self.owner_strength.get(owner, 0) * 0.5
                    + self.owner_production.get(owner, 0) * 0.5
                )
            if lead_scores:
                top_owner = max(lead_scores, key=lambda k: lead_scores[k])
                self.leader_id = top_owner
                my_score = lead_scores.get(self.player, 0)
                top_score = lead_scores.get(top_owner, 0)
                if (
                    top_owner != self.player
                    and my_score > 0
                    and (top_score / my_score) >= LEADER_BASH_RATIO
                ):
                    self.contest_leader = True

        
        
        
        
        self.mode = _detect_mode(self) if PERSONALITY_ENABLED else "patient"
        
        
        
        if TERMINAL_PHASE_ENABLED and self.remaining_steps < TERMINAL_PHASE_TURNS:
            self.mode = "pressure"
        params_table = MODE_PARAMS_2P if self.is_2p else MODE_PARAMS
        self.mode_params = params_table[self.mode]

        
        
        self.stop_expanding_2p = (
            STOP_EXPAND_2P_ENABLED
            and self.is_2p
            and self.step >= STOP_EXPAND_TURN_MIN_2P
            and self.my_prod_share >= STOP_EXPAND_PROD_SHARE_2P
        )

        
        
        
        
        self.in_combat_contact = False
        if COMBAT_STOP_EXPAND_ENABLED:
            my_ids = {p.id for p in self.my_planets}
            enemy_ids = {p.id for p in self.enemy_planets}
            for pid, arrs in self.arrivals_by_planet.items():
                if pid in my_ids:
                    for _eta, owner, ships in arrs:
                        if owner != self.player and owner != -1 and ships >= COMBAT_CONTACT_MIN_SHIPS:
                            self.in_combat_contact = True
                            break
                elif pid in enemy_ids:
                    for _eta, owner, ships in arrs:
                        if owner == self.player and ships >= COMBAT_CONTACT_MIN_SHIPS:
                            self.in_combat_contact = True
                            break
                if self.in_combat_contact:
                    break
        self.combat_stop_expand = (
            COMBAT_STOP_EXPAND_ENABLED
            and self.in_combat_contact
            and self.step >= COMBAT_STOP_EXPAND_TURN_MIN
            and (not COMBAT_STOP_EXPAND_4P_ONLY or not self.is_2p)
        )

        
        
        
        prod_lag_thresh = (
            PROD_LAG_STOP_EXPAND_THRESH_2P if self.is_2p
            else PROD_LAG_STOP_EXPAND_THRESH_4P
        )
        self.prod_lag_stop_expand = (
            PROD_LAG_STOP_EXPAND_ENABLED
            and self.step >= PROD_LAG_STOP_EXPAND_TURN_MIN
            and self.my_prod_share < prod_lag_thresh
        )

        
        self.enemy_tempo_stop_expand = (
            ENEMY_TEMPO_STOP_EXPAND_ENABLED
            and self.step >= ENEMY_TEMPO_STOP_EXPAND_TURN_MIN
            and FLEET_INTENT_ENABLED
            and len(_enemy_recently_launched) >= ENEMY_TEMPO_STOP_EXPAND_MIN_LAUNCHES
        )

        
        self.easy_enemy_stop_expand = False
        if EASY_ENEMY_STOP_EXPAND_ENABLED and self.step >= EASY_ENEMY_STOP_EXPAND_TURN_MIN:
            easy_count = 0
            for ep in self.enemy_planets:
                if int(ep.ships) > EASY_ENEMY_MAX_GARRISON:
                    continue
                for mp in self.my_planets:
                    if dist(mp.x, mp.y, ep.x, ep.y) <= EASY_ENEMY_MAX_DIST:
                        easy_count += 1
                        break
                if easy_count >= EASY_ENEMY_MIN_COUNT:
                    break
            self.easy_enemy_stop_expand = (easy_count >= EASY_ENEMY_MIN_COUNT)

        
        self.stockpile_stop_expand = False
        if STOCKPILE_STOP_EXPAND_ENABLED and self.step >= STOCKPILE_STOP_EXPAND_TURN_MIN:
            for mp in self.my_planets:
                if int(mp.ships) >= STOCKPILE_STOP_EXPAND_MAX_GARRISON:
                    self.stockpile_stop_expand = True
                    break

        
        self.prod_lead_stop_expand_4p = (
            PROD_LEAD_STOP_EXPAND_4P_ENABLED
            and not self.is_2p
            and self.step >= PROD_LEAD_STOP_EXPAND_4P_TURN_MIN
            and self.my_prod_share >= PROD_LEAD_STOP_EXPAND_4P_THRESH
        )

        
        self.turn_cutoff_stop_expand = (
            TURN_CUTOFF_STOP_EXPAND_ENABLED
            and self.step >= TURN_CUTOFF_STOP_EXPAND_TURN
        )

        
        self.neutral_saturation_stop_expand = False
        if (
            NEUTRAL_SATURATION_STOP_EXPAND_ENABLED
            and self.step >= NEUTRAL_SATURATION_TURN_MIN
            and (not NEUTRAL_SATURATION_2P_ONLY or self.is_2p)
        ):
            any_cheap = False
            for n in self.planets:
                if n.owner != -1 or n.id in self.comet_ids:
                    continue
                if int(n.ships) > NEUTRAL_SATURATION_CHEAP_GARRISON:
                    continue
                for mp in self.my_planets:
                    if dist(mp.x, mp.y, n.x, n.y) <= NEUTRAL_SATURATION_REACH_DIST:
                        any_cheap = True
                        break
                if any_cheap:
                    break
            self.neutral_saturation_stop_expand = not any_cheap

        
        
        self.stop_expand_lax = (
            self.combat_stop_expand
            or self.prod_lag_stop_expand
            or self.enemy_tempo_stop_expand
            or self.easy_enemy_stop_expand
            or self.neutral_saturation_stop_expand
            or self.stockpile_stop_expand
        )

        
        
        
        self.focus_enemy_2p = None
        if F14_4A_2P_FOCUS_ENABLED and self.is_2p:
            for o in self.owner_production.keys():
                if o not in (-1, self.player):
                    self.focus_enemy_2p = o
                    break

    @property
    def num_players(self):
        owners = set()
        for p in self.planets:
            if p.owner != -1:
                owners.add(p.owner)
        for f in self.fleets:
            owners.add(f.owner)
        return max(2, len(owners))


def _read(obs, key, default=None):
    if isinstance(obs, dict):
        return obs.get(key, default)
    return getattr(obs, key, default)


def _compute_enemy_race_eta(world):
    """For each neutral, return earliest turn an enemy could land a capturing
    fleet. Considers (a) enemy fleets already in flight aimed at this neutral,
    and (b) enemy planets that have enough ships and are within reach.
    Returns {neutral_id: eta_int}. Neutrals with no credible threat omitted.

    Used to prioritize uncontested-but-soon-to-be-contested neutrals AND to
    skip targets we'd lose the race for (saving ships for next turn).
    """
    out = {}
    if not world.neutral_planets:
        return out

    for n in world.neutral_planets:
        needed = int(n.ships) + 1
        earliest = None

        
        for eta, owner, ships in world.arrivals_by_planet.get(n.id, []):
            if owner == world.player or owner == -1:
                continue
            if ships < needed:
                continue
            if earliest is None or eta < earliest:
                earliest = int(eta)

        
        for ep in world.enemy_planets:
            if int(ep.ships) < needed:
                continue
            d = dist(ep.x, ep.y, n.x, n.y)
            if d > RACE_MAX_NEUTRAL_DIST:
                continue
            
            
            
            
            
            if safe_geometry(ep.x, ep.y, ep.radius, n.x, n.y, n.radius) is None:
                continue
            
            
            
            min_turns = max(1, int(math.ceil(d / fleet_speed(int(ep.ships)))))
            if min_turns > RACE_HORIZON_TURNS:
                continue
            if earliest is None or min_turns < earliest:
                earliest = min_turns

        if earliest is not None:
            out[n.id] = earliest
    return out


def _detect_mode(world):
    """Pick a personality mode from the current snapshot.

    Aggression score = (enemy ships in flight) / (total enemy ships, in flight
    or on planets). A high ratio means enemies are committing to attacks; a
    low ratio means they're stockpiling / quiet. We stay PATIENT during the
    opening since initial expansions look like aggression but aren't.

    V12.2 R2: in 2P, sustained PATIENT with no production-share gain forces
    escalation (10 turns → OPPORTUNISTIC, 20 turns → PRESSURE). This is the
    Bocsimacko "value action over inaction" principle — patient-vs-patient
    1v1 is a stable equilibrium the bot otherwise can't leave.
    """
    if world.is_opening:
        if world.is_2p:
            _record_2p_progress(world.my_prod_share, intended_patient=True, reset=True)
        return "patient"

    enemy_planet_ships = 0
    for p in world.planets:
        if p.owner not in (-1, world.player):
            enemy_planet_ships += int(p.ships)
    enemy_fleet_ships = 0
    for f in world.fleets:
        if f.owner != world.player and f.owner != -1:
            enemy_fleet_ships += int(f.ships)

    enemy_total = enemy_planet_ships + enemy_fleet_ships
    if enemy_total < PERSONALITY_MIN_SAMPLE:
        intended = "patient"
    else:
        aggression = enemy_fleet_ships / float(enemy_total)
        if aggression >= PERSONALITY_AGG_HIGH:
            intended = "pressure"
        elif aggression <= PERSONALITY_AGG_LOW:
            intended = "opportunistic"
        else:
            intended = "patient"

    if not world.is_2p:
        return intended

    
    
    
    _record_2p_progress(world.my_prod_share, intended_patient=(intended == "patient"))
    return "pressure"


def _record_2p_progress(my_prod_share, intended_patient, reset=False):
    """Track production-share trend in 2P. Increment streak whenever the bot
    intends to stay PATIENT and prod-share hasn't grown >EPS over the rolling
    window. Reset streak on opening, on non-PATIENT intent, or on real progress.
    Returns current streak length.
    """
    global _2p_patient_streak, _2p_prod_share_history
    if reset:
        _2p_patient_streak = 0
        _2p_prod_share_history = []
        return 0
    _2p_prod_share_history.append(float(my_prod_share))
    if len(_2p_prod_share_history) > TWO_P_PROD_SHARE_HISTORY:
        _2p_prod_share_history.pop(0)
    if not intended_patient:
        _2p_patient_streak = 0
        return 0
    if len(_2p_prod_share_history) >= TWO_P_PROD_SHARE_HISTORY:
        delta = _2p_prod_share_history[-1] - _2p_prod_share_history[0]
        if delta > TWO_P_PROD_SHARE_PROGRESS_EPS:
            _2p_patient_streak = 0
            return 0
    _2p_patient_streak += 1
    return _2p_patient_streak






_agent_step = 0
_hammer_plan = None             
_planet_idle_counts = {}        
_promoted_stockpiles = set()    
_game_num_players = None        
_2p_patient_streak = 0          
_2p_prod_share_history = []     






_neutral_prev_ships = {}
_neutral_wounded = set()




_enemy_prev_ships = {}
_enemy_recently_launched = set()  



_planet_prev_owner = {}        
_freshly_lost_planets = set()  

_freshly_captured_planets = set()  
_planet_capture_age = {}       






_pending_commitments = []






OPP_PROFILE_WINDOW = 20
_opp_profile = {}


def _update_opp_profile_4p(world):
    """V12.8et: collect rolling per-enemy behavioral signals. 4P-only;
    caller must check world.is_2p first to avoid 2P side effects.
    """
    global _opp_profile
    if world.step == 0:
        _opp_profile = {}

    plan_ships = defaultdict(int)
    plan_max = defaultdict(int)
    plan_count = defaultdict(int)
    for p in world.planets:
        if p.owner == world.player or p.owner == -1:
            continue
        s = int(p.ships)
        plan_ships[p.owner] += s
        plan_count[p.owner] += 1
        if s > plan_max[p.owner]:
            plan_max[p.owner] = s
    fleet_ships = defaultdict(int)
    for f in world.fleets:
        if f.owner == world.player or f.owner == -1:
            continue
        fleet_ships[f.owner] += int(f.ships)

    enemies = set(plan_count.keys()) | set(fleet_ships.keys())
    for owner in enemies:
        ps = plan_ships.get(owner, 0)
        fs = fleet_ships.get(owner, 0)
        total = ps + fs
        emit = (fs / total) if total else 0.0
        prof = _opp_profile.setdefault(owner, {"emit": [], "stock": [], "plan": []})
        prof["emit"].append(emit)
        prof["stock"].append(plan_max.get(owner, 0))
        prof["plan"].append(plan_count.get(owner, 0))
        if len(prof["emit"]) > OPP_PROFILE_WINDOW:
            prof["emit"] = prof["emit"][-OPP_PROFILE_WINDOW:]
            prof["stock"] = prof["stock"][-OPP_PROFILE_WINDOW:]
            prof["plan"] = prof["plan"][-OPP_PROFILE_WINDOW:]

    world.opp_profile = _opp_profile






def predict_defender_at_arrival(world, target, arrival_turn):
    """Owner + ship count on `target` at `arrival_turn` (turns from now), using
    the same combat rules as the env: each turn growth, then resolve arrivals."""
    arrivals = world.arrivals_by_planet.get(target.id, [])
    by_turn = defaultdict(list)
    for eta, owner, ships in arrivals:
        if ships <= 0:
            continue
        by_turn[eta].append((owner, ships))

    owner = target.owner
    garrison = float(target.ships)
    horizon = max(1, int(math.ceil(arrival_turn)))

    for t in range(1, horizon + 1):
        if owner != -1:
            garrison += int(target.production)
        group = by_turn.get(t)
        if group:
            owner, garrison = _resolve_combat(owner, garrison, group)
    return owner, max(0.0, garrison)


def _resolve_combat(owner, garrison, arrivals):
    """Match the env's resolve rule: top-attacker minus second-attacker wins; ties = neutral."""
    by_owner = defaultdict(int)
    for o, s in arrivals:
        by_owner[o] += s
    if not by_owner:
        return owner, max(0.0, garrison)
    sorted_o = sorted(by_owner.items(), key=lambda kv: kv[1], reverse=True)
    top_o, top_s = sorted_o[0]
    if len(sorted_o) > 1 and top_s == sorted_o[1][1]:
        survivor_o, survivor_s = -1, 0
    elif len(sorted_o) > 1:
        survivor_o, survivor_s = top_o, top_s - sorted_o[1][1]
    else:
        survivor_o, survivor_s = top_o, top_s

    if survivor_s <= 0:
        return owner, max(0.0, garrison)
    if owner == survivor_o:
        return owner, garrison + survivor_s
    garrison -= survivor_s
    if garrison < 0:
        return survivor_o, -garrison
    return owner, garrison





FWD_SIM_ENABLED = os.environ.get("V128_FWD_SIM", "1") != "0"
FWD_LOOKAHEAD_HORIZON = 25
FWD_LOOKAHEAD_TOP_K = 6          
FWD_MAX_FLEETS = 80


def _fwd_clone(world):
    planet_ids = []
    planet_owner = {}
    planet_ships = {}
    planet_xy = {}
    planet_radius = {}
    planet_prod = {}
    orbital = {}
    for p in world.planets:
        if p.id in world.comet_ids:
            continue
        planet_ids.append(p.id)
        planet_owner[p.id] = int(p.owner)
        planet_ships[p.id] = float(p.ships)
        planet_xy[p.id] = (float(p.x), float(p.y))
        planet_radius[p.id] = float(p.radius)
        planet_prod[p.id] = int(p.production)
        init = world.initial_by_id.get(p.id)
        if init is not None:
            dx = float(init.x) - CENTER_X
            dy = float(init.y) - CENTER_Y
            r = math.sqrt(dx * dx + dy * dy)
            if r + p.radius < ROTATION_LIMIT:
                orbital[p.id] = (r, math.atan2(dy, dx))
    fleets = []
    next_id = 0
    for f in world.fleets:
        fleets.append([int(f.id), int(f.owner), float(f.x), float(f.y),
                       float(f.angle), int(f.ships)])
        next_id = max(next_id, int(f.id))
    return {
        "planet_ids": planet_ids,
        "planet_owner": planet_owner,
        "planet_ships": planet_ships,
        "planet_xy": planet_xy,
        "planet_radius": planet_radius,
        "planet_prod": planet_prod,
        "orbital": orbital,
        "fleets": fleets,
        "step": int(world.step),
        "ang_vel": float(world.ang_vel),
        "next_fleet_id": next_id + 1,
    }


def _fwd_inject_launch(state, src_id, angle, ships):
    if src_id not in state["planet_xy"]:
        return False
    if state["planet_ships"][src_id] < ships:
        return False
    state["planet_ships"][src_id] -= ships
    radius = state["planet_radius"][src_id]
    sx, sy = state["planet_xy"][src_id]
    fx = sx + math.cos(angle) * (radius + 0.1)
    fy = sy + math.sin(angle) * (radius + 0.1)
    owner = state["planet_owner"][src_id]
    state["fleets"].append([state["next_fleet_id"], int(owner), fx, fy,
                            float(angle), int(ships)])
    state["next_fleet_id"] += 1
    return True


def _fwd_step(state):
    for pid in state["planet_ids"]:
        if state["planet_owner"][pid] != -1:
            state["planet_ships"][pid] += state["planet_prod"][pid]
    combat = {pid: [] for pid in state["planet_ids"]}
    surviving = []
    radii = state["planet_radius"]
    xy = state["planet_xy"]
    pids = state["planet_ids"]
    for fl in state["fleets"]:
        ships = fl[5]
        if ships <= 0:
            continue
        speed = fleet_speed(ships)
        old_x, old_y = fl[2], fl[3]
        new_x = old_x + math.cos(fl[4]) * speed
        new_y = old_y + math.sin(fl[4]) * speed
        fl[2] = new_x
        fl[3] = new_y
        if not (0.0 <= new_x <= BOARD and 0.0 <= new_y <= BOARD):
            continue
        if point_to_segment_distance(CENTER_X, CENTER_Y, old_x, old_y, new_x, new_y) < SUN_R:
            continue
        hit_pid = -1
        for pid in pids:
            px, py = xy[pid]
            if point_to_segment_distance(px, py, old_x, old_y, new_x, new_y) < radii[pid]:
                hit_pid = pid
                break
        if hit_pid >= 0:
            combat[hit_pid].append(fl)
        else:
            surviving.append(fl)
    state["step"] += 1
    new_xy = dict(xy)
    for pid, (r, a0) in state["orbital"].items():
        a = a0 + state["ang_vel"] * state["step"]
        new_xy[pid] = (CENTER_X + r * math.cos(a), CENTER_Y + r * math.sin(a))
    still = []
    for fl in surviving:
        hit_pid = -1
        for pid in pids:
            if pid not in state["orbital"]:
                continue
            old_px, old_py = xy[pid]
            new_px, new_py = new_xy[pid]
            if point_to_segment_distance(fl[2], fl[3], old_px, old_py, new_px, new_py) < radii[pid]:
                hit_pid = pid
                break
        if hit_pid >= 0:
            combat[hit_pid].append(fl)
        else:
            still.append(fl)
    state["planet_xy"] = new_xy
    state["fleets"] = still
    for pid, arrivals in combat.items():
        if not arrivals:
            continue
        per_owner = defaultdict(int)
        for fl in arrivals:
            per_owner[fl[1]] += fl[5]
        sorted_o = sorted(per_owner.items(), key=lambda kv: kv[1], reverse=True)
        top_o, top_s = sorted_o[0]
        if len(sorted_o) > 1:
            second_s = sorted_o[1][1]
            if top_s == second_s:
                surv_s, surv_o = 0, -1
            else:
                surv_s, surv_o = top_s - second_s, top_o
        else:
            surv_o, surv_s = top_o, top_s
        if surv_s > 0:
            cur = state["planet_owner"][pid]
            if cur == surv_o:
                state["planet_ships"][pid] += surv_s
            else:
                state["planet_ships"][pid] -= surv_s
                if state["planet_ships"][pid] < 0:
                    state["planet_owner"][pid] = surv_o
                    state["planet_ships"][pid] = -state["planet_ships"][pid]


def _fwd_simulate(state, horizon):
    for _ in range(horizon):
        if len(state["fleets"]) > FWD_MAX_FLEETS:
            break
        _fwd_step(state)
    return state


def _fwd_my_score(state, player):
    total = 0.0
    for pid in state["planet_ids"]:
        if state["planet_owner"][pid] == player:
            total += state["planet_ships"][pid]
    for fl in state["fleets"]:
        if fl[1] == player:
            total += fl[5]
    return total


def _fwd_marginal(world, src_id, angle, ships, player, horizon):
    """V12.8ay: Δ score (with-launch − without-launch) at horizon."""
    state_no = _fwd_clone(world)
    _fwd_simulate(state_no, horizon)
    base = _fwd_my_score(state_no, player)
    state_yes = _fwd_clone(world)
    if not _fwd_inject_launch(state_yes, src_id, angle, int(ships)):
        return 0.0
    _fwd_simulate(state_yes, horizon)
    return _fwd_my_score(state_yes, player) - base


def _fwd_capture_holds_2p(world, src, target, angle, turns, ships, my_player):
    """V12.8av: simulate launching this fleet now; verify the captured
    target is still ours `turns + FWD_STAB_HORIZON` turns later. Returns
    True if capture sticks, False if predicted to flip."""
    state = _fwd_clone(world)
    if not _fwd_inject_launch(state, src.id, angle, int(ships)):
        return True  
    horizon = int(turns) + 15  
    _fwd_simulate(state, horizon)
    return state["planet_owner"].get(target.id) == my_player






def is_targetable(world, target):
    """Comets travel along non-orbital elliptical paths that aim_at_target can't
    predict. Aiming at them produces fleets that wander and often hit the sun.
    Skip them entirely as expansion / hammer targets.

    V12.9 redundant-launch fix: also skip NEUTRAL targets where one of OUR
    fleets is already in flight with enough ships to flip the planet on
    arrival. Prevents wasted small follow-up fleets piling on a neutral that
    is already being captured.

    V12.9 cap55: enforce the neutral hard cap (2P >=55, 4P legacy) here so
    every targeting code path obeys it — the previous per-call check at
    generate_step_actions/handle_expand missed cheap-pickup, multiprong, and
    other paths."""
    if target.id in world.comet_ids:
        return False
    if target.owner == -1:
        
        
        
        my_arrivals = sorted(
            ((eta, ships) for eta, owner, ships
             in world.arrivals_by_planet.get(target.id, [])
             if owner == world.player),
            key=lambda x: x[0],
        )
        if my_arrivals:
            total_ships = sum(s for _, s in my_arrivals)
            last_eta = my_arrivals[-1][0]
            if total_ships > garrison_at_arrival(target, last_eta):
                return False
        if _neutral_blocked_by_cap(world, target):
            return False
        
        
        
        
        
        
        
        if (LOW_PROD_NEUTRAL_SKIP_ENABLED
                and int(target.production) <= LOW_PROD_NEUTRAL_SKIP_PROD
                and int(target.ships) >= LOW_PROD_NEUTRAL_SKIP_GARRISON):
            return False
    return True


def _update_neutral_watchlist(world):
    """V12.8c: rebuild the wounded-neutral set from this turn's deltas.
    A neutral that lost >= NEUTRAL_WATCHLIST_MIN_DROP ships since last
    turn is considered wounded — someone else attacked it, so it's now
    cheaper for us to take. _neutral_prev_ships is then refreshed.

    V13.3 F1: also track enemy planet ship-drops as 'recently launched'
    signal. A drop > FLEET_INTENT_MIN_DROP indicates the source committed
    a fleet outward; the source is in a brief vulnerable state."""
    _neutral_wounded.clear()
    if NEUTRAL_HARD_CAP_ENABLED:
        for p in world.neutral_planets:
            prev = _neutral_prev_ships.get(p.id)
            cur = int(p.ships)
            if prev is not None and (prev - cur) >= NEUTRAL_WATCHLIST_MIN_DROP:
                _neutral_wounded.add(p.id)
    _neutral_prev_ships.clear()
    for p in world.neutral_planets:
        _neutral_prev_ships[p.id] = int(p.ships)
    
    if FLEET_INTENT_ENABLED:
        _enemy_recently_launched.clear()
        for p in world.enemy_planets:
            prev = _enemy_prev_ships.get(p.id)
            cur = int(p.ships)
            if prev is not None:
                
                
                expected = prev + int(p.production)
                if expected - cur >= FLEET_INTENT_MIN_DROP:
                    _enemy_recently_launched.add(p.id)
        _enemy_prev_ships.clear()
        for p in world.enemy_planets:
            _enemy_prev_ships[p.id] = int(p.ships)
    
    
    
    
    if R1_RECAPTURE_PRIORITY_ENABLED:
        _freshly_lost_planets.clear()
        _freshly_captured_planets.clear()
        for p in world.planets:
            prev_owner = _planet_prev_owner.get(p.id)
            if prev_owner == world.player and p.owner != -1 and p.owner != world.player:
                _freshly_lost_planets.add(p.id)
            
            if (
                FRESH_CAPTURE_INHERITANCE_ENABLED
                and prev_owner is not None
                and prev_owner != world.player
                and p.owner == world.player
            ):
                _freshly_captured_planets.add(p.id)
                _planet_capture_age[p.id] = 0
        
        if FRESH_CAPTURE_INHERITANCE_ENABLED:
            for pid in list(_planet_capture_age.keys()):
                if pid in _freshly_captured_planets:
                    continue
                pp = world.planet_by_id.get(pid)
                if pp is None or pp.owner != world.player:
                    del _planet_capture_age[pid]
                else:
                    _planet_capture_age[pid] += 1
                    if _planet_capture_age[pid] > FRESH_CAPTURE_MAX_AGE:
                        del _planet_capture_age[pid]
        _planet_prev_owner.clear()
        for p in world.planets:
            _planet_prev_owner[p.id] = int(p.owner)


def _neutral_blocked_by_cap(world, target):
    """V12.9 cap55: ignore neutrals with high garrison. V13.3 N4: use
    effective_garrison_at_arrival projection (estimated 10-turn lookahead)
    so a 60-ship neutral about to be hit by enemy 8 → effective 52 → unblocks."""
    if not NEUTRAL_HARD_CAP_ENABLED:
        return False
    if target.owner != -1:
        return False
    
    if NEUTRAL_CAP_USES_EFFECTIVE_GARRISON:
        eff_owner, eff_ships = effective_garrison_at_arrival(target, NEUTRAL_CAP_LOOKAHEAD, world)
        if eff_owner != -1:
            
            return False
        if world.is_2p:
            return eff_ships >= NEUTRAL_HARD_CAP_2P
        if eff_ships <= NEUTRAL_HARD_CAP_4P:
            return False
        return target.id not in _neutral_wounded
    
    if world.is_2p:
        return int(target.ships) >= NEUTRAL_HARD_CAP_2P
    if int(target.ships) <= NEUTRAL_HARD_CAP_4P:
        return False
    return target.id not in _neutral_wounded


def _neutral_tempo_ok(world, target, ships, turns):
    """V12.8cq: skip neutral captures whose expected production gain over
    remaining turns doesn't beat the ship cost by NEUTRAL_TEMPO_THRESHOLD.
    4P-only (2P duels make every neutral worth it). Refuses captures that
    repay slowly even if technically positive (kovi-inspired patience)."""
    if not NEUTRAL_TEMPO_FILTER_ENABLED:
        return True
    if world.is_2p:
        return True
    if target.owner != -1:
        return True
    remaining_after = max(0, int(world.remaining_steps) - int(turns))
    net = float(target.production) * remaining_after - float(ships)
    return net >= NEUTRAL_TEMPO_THRESHOLD


def _ti1_extra_margin(world):
    """V13.3 TI1: returns extra margin to require on captures when we're
    trailing the leader in the late game. Tie counts as a win (engine reward=1
    for max-sum players); low-margin failed attacks drop our absolute sum but
    not our enemies' enough to help. Conserve when behind."""
    if not TI1_TIE_FOR_WIN_ENABLED:
        return 0
    if world.remaining_steps > TI1_HORIZON_TURNS:
        return 0
    my_sum = world.owner_strength.get(world.player, 0)
    leader_sum = my_sum
    for owner, ships in world.owner_strength.items():
        if owner == world.player or owner == -1:
            continue
        if ships > leader_sum:
            leader_sum = ships
    if leader_sum - my_sum < TI1_TRAILING_GAP_MIN:
        return 0  
    return TI1_REQUIRED_EXTRA_MARGIN


def _endgame_roi_ok(world, target, ships, turns):
    """V12.8b: in the last ENDGAME_ROI_TURNS (4P only), refuse neutral captures
    whose expected production growth doesn't repay the ships spent. 4P-only
    because in 2P the differential-value of denying the neutral to the single
    opponent makes marginal late grabs still net-positive at this threshold;
    n=384 test of the un-gated version showed -38 wins 2P, +17pp 4P. Hostile
    targets always allowed. Returns True if firing is OK."""
    if not ENDGAME_ROI_ENABLED:
        return True
    if world.is_2p:
        return True
    if target.owner != -1:
        return True
    if world.step < TOTAL_STEPS - ENDGAME_ROI_TURNS:
        return True
    remaining_after = max(0, int(world.remaining_steps) - int(turns))
    expected_growth = float(target.production) * remaining_after
    
    
    
    
    threshold = float(target.ships) if E2_USE_GARRISON_THRESHOLD else float(ships)
    return expected_growth > threshold


def friendly_already_committed(world, target_id):
    """Patient ethos: ONE main fleet per target — UNLESS the target is enemy
    and our in-flight fleet undershoots its growing garrison.

    Neutrals don't grow, so a correctly-sized fleet wins or loses on arrival;
    a follow-up there is wasted ships (Bocsimacko/zvold canonical rule). For
    enemy targets, the planet grows by its production rate every turn the
    fleet is in flight, so a single source from long range can fail to
    capture; allow a sequenced follow-up only when no single pending fleet
    is sufficient at its own arrival turn.
    """
    target = world.planet_by_id.get(target_id)
    if target is None:
        return False
    pending = [c for c in _pending_commitments if c["target_id"] == target_id]
    if not pending:
        return False
    
    if target.owner == -1 or target.owner == world.player:
        return sum(c["ships"] for c in pending) > 0
    
    
    
    for c in pending:
        eta = int(c["arrival_abs"]) - int(world.step)
        if eta <= 0:
            continue
        if int(c["ships"]) >= needed_to_capture(target, eta):
            return True
    return False


def _commit_fleet(world, moves, spent, target_locked,
                  src_id, target_id, angle, turns, ships):
    """Single point of truth for firing a fleet: appends move, charges spent,
    locks target this turn, and records the persistent commitment so future
    turns know we already engaged this target."""
    moves.append([src_id, float(angle), int(ships)])
    spent[src_id] += int(ships)
    target_locked.add(target_id)
    
    
    target_obj = world.planet_by_id.get(int(target_id))
    owner_at_commit = int(target_obj.owner) if target_obj is not None else -2
    _pending_commitments.append({
        "target_id": int(target_id),
        "ships": int(ships),
        "arrival_abs": int(world.step) + int(turns),
        "owner_at_commit": owner_at_commit,
    })
    if os.environ.get("ORBIT_TRACE"):
        try:
            with open(os.environ["ORBIT_TRACE"], "a") as fh:
                fh.write(
                    f"t={world.step} src={src_id} tgt={target_id} ships={ships} eta={turns}\n"
                )
        except Exception:
            pass


def plan_solo_capture(world, src, tgt, max_avail, max_travel):
    """Plan a single-fleet capture (angle, turns, ships) honoring all the
    fleet-quality rules. Returns None if no viable shot exists.

    Critical: aiming uses fleet_speed(ships), so a different ship count than
    we end up sending produces a wrong angle and the fleet wanders / hits the
    sun. We aim, decide ships, then RE-AIM with the exact ship count.
    """
    
    
    raw_dist = dist(src.x, src.y, tgt.x, tgt.y)
    if F3_THREE_BUCKET_ENABLED:
        if tgt.owner == -1 and raw_dist < F3_SAFE_DIST:
            min_floor = F3_SAFE_FLOOR
        elif (tgt.owner != -1 and tgt.owner != world.player
              and int(tgt.ships) >= F3_HARD_GARRISON):
            min_floor = F3_HARD_FLOOR
        else:
            min_floor = MIN_DISPATCH_SHIPS
    else:
        min_floor = 5 if (world.is_2p and raw_dist < 12.0) else MIN_DISPATCH_SHIPS
    if max_avail < min_floor:
        return None
    aim = aim_at_target(src, tgt, max_avail, world.initial_by_id, world.ang_vel, world=world)
    if aim is None:
        return None
    angle, turns = aim
    if turns > max_travel:
        return None
    need = effective_needed_to_capture(tgt, turns, world)  
    margin = EXPAND_MIN_MARGIN_4P if not world.is_2p else EXPAND_MIN_MARGIN
    
    
    
    
    extra = X8B_2P_EXTRA if world.is_2p else 0
    
    
    
    
    extra += _ti1_extra_margin(world)
    preferred = max(min_floor, need + margin + extra)
    
    
    
    if SP1_SPEED_AWARE_ENABLED:
        raw_dist = dist(src.x, src.y, tgt.x, tgt.y)
        if raw_dist >= SP1_LONG_DIST_THRESHOLD:
            preferred = max(preferred, min(SP1_LONG_DIST_SHIPS, max_avail))
    if preferred <= max_avail:
        ships = preferred
    else:
        ships = max(min_floor, need + margin)
        if ships > max_avail:
            ships = max(min_floor, need)  
    if ships < min_floor or ships > max_avail:
        return None
    aim2 = aim_at_target(src, tgt, ships, world.initial_by_id, world.ang_vel, world=world)
    if aim2 is None:
        return None
    angle, turns = aim2
    if turns > max_travel:
        return None
    need2 = effective_needed_to_capture(tgt, turns, world)  
    if ships < need2 + margin:
        ships = need2 + margin
        if ships > max_avail:
            return None
        aim3 = aim_at_target(src, tgt, ships, world.initial_by_id, world.ang_vel, world=world)
        if aim3 is None:
            return None
        angle, turns = aim3
        if turns > max_travel:
            return None
    
    
    
    
    
    if AS1_ANTI_SECOND_ENABLED and not world.is_2p:
        for eta, owner, e_ships in world.arrivals_by_planet.get(tgt.id, []):
            if int(eta) != int(turns):
                continue
            if owner == world.player or owner == -1:
                continue
            if int(e_ships) >= int(ships):
                return None  
    
    
    
    
    
    if FWD_SIM_FILTER_ENABLED and not world.is_2p and tgt.owner == -1:
        proj = forward_project(
            world,
            our_capture_target=tgt.id,
            our_capture_turn=int(turns),
            our_capture_ships=int(ships),
            horizon=FWD_SIM_HORIZON,
            project_opponent_moves=True,
            opponent_emit_fraction=0.30,
        )
        end_owner, end_ships = proj.get(tgt.id, (-1, 0))
        
        
        
        if end_owner != world.player and end_owner != -1 and end_ships > 5:
            return None
    return angle, turns, int(ships)






def handle_defense(world, rescue_needs, available, spent, target_locked,
                   moves, mode_log):
    """Rescue siblings flagged by absorb. Single source preferred; 2-source
    coalition fallback. Each rescuer respects its own reserve and arrives by
    deadline. Locked rescue targets prevent over-rescue.

    V14.2 (Phase 3.8): preemptive doom-evac. When total incoming enemy
    ships overwhelm garrison+future_production, the planet is definitely
    doomed even with rescue. Skip rescue (which wastes ships) and evac
    directly. User-observed scenario: 40 garrison, 10+49 incoming → solo
    rescue would send a sub-need fleet and still lose; better to evac.
    """
    if not rescue_needs:
        return

    for victim_id, (deficit, deadline, victim) in rescue_needs.items():
        if victim_id in target_locked:
            continue
        need = deficit + DEFENSE_OVERSEND

        
        
        
        
        
        if PREEMPTIVE_DOOM_EVAC_ENABLED and (not PREEMPTIVE_DOOM_EVAC_2P_ONLY or world.is_2p):
            enemy_arrivals = [
                (eta, owner, int(ships)) for eta, owner, ships
                in world.arrivals_by_planet.get(victim_id, [])
                if owner != world.player and owner != -1
            ]
            if world.is_2p or not PREEMPTIVE_EVAC_USE_LARGEST_SINGLE_ENEMY_4P:
                threat_metric = sum(ships for _eta, _owner, ships in enemy_arrivals)
            else:
                
                by_owner = defaultdict(int)
                for _eta, owner, ships in enemy_arrivals:
                    by_owner[owner] += ships
                threat_metric = max(by_owner.values()) if by_owner else 0
            window = deadline if deadline is not None else PREEMPTIVE_EVAC_DEFAULT_WINDOW
            garrison_at_deadline = int(victim.ships) + int(victim.production) * int(window)
            if threat_metric > garrison_at_deadline * PREEMPTIVE_EVAC_DOOM_RATIO:
                if _try_doom_evac(world, victim, available, spent, target_locked, moves, mode_log):
                    continue
                
                

        
        solo = []
        for src in world.my_planets:
            if src.id == victim_id:
                continue
            avail = available[src.id] - spent[src.id]
            if avail < need:
                continue
            aim = aim_at_target(src, victim, avail, world.initial_by_id, world.ang_vel, world=world)
            if aim is None:
                continue
            angle, turns = aim
            if deadline is not None and turns > deadline:
                continue
            solo.append((turns, src.id, src, angle, avail))

        if solo:
            solo.sort()  
            
            
            
            fired_solo = False
            last_fail = None
            for _t, src_id, src, _angle_est, avail in solo:
                send = min(avail, need)
                send = max(send, deficit + 1)
                if send < MIN_DISPATCH_SHIPS:
                    send = MIN_DISPATCH_SHIPS if avail >= MIN_DISPATCH_SHIPS else 0
                if send <= 0:
                    last_fail = "doomed-too-poor"
                    continue
                aim_final = aim_at_target(src, victim, send, world.initial_by_id, world.ang_vel, world=world)
                if aim_final is None:
                    last_fail = "doomed-aim-blocked"
                    continue
                angle, turns = aim_final
                if deadline is not None and turns > deadline:
                    last_fail = "doomed-too-slow"
                    continue
                
                
                if FWD_SIM_DEFENSE_CHECK and not world.is_2p:
                    proj = forward_project(
                        world,
                        our_capture_target=victim_id,
                        our_capture_turn=int(turns),
                        our_capture_ships=int(send),
                        horizon=FWD_SIM_HORIZON,
                        project_opponent_moves=True,
                        opponent_emit_fraction=0.30,
                    )
                    end_owner, _ = proj.get(victim_id, (-1, 0))
                    if end_owner != world.player:
                        last_fail = "fwd-sim-victim-still-lost"
                        continue
                _commit_fleet(world, moves, spent, target_locked,
                              src_id, victim_id, angle, turns, int(send))
                mode_log[victim_id] = "defended-by-solo"
                mode_log[src_id] = "defense"
                fired_solo = True
                break
            if fired_solo:
                continue
            if last_fail is not None:
                mode_log[victim_id] = last_fail
                

        
        if not COALITION_ENABLED:
            
            if _try_doom_evac(world, victim, available, spent, target_locked, moves, mode_log):
                continue
            mode_log[victim_id] = "doomed"
            continue
        coalition = _find_defense_coalition(
            world, victim, deadline, need, available, spent
        )
        if coalition is None:
            
            if _try_doom_evac(world, victim, available, spent, target_locked, moves, mode_log):
                continue
            mode_log[victim_id] = "doomed"
            continue
        for src_id, src, angle, ships, turns in coalition:
            _commit_fleet(world, moves, spent, target_locked,
                          src_id, victim_id, angle, turns, int(ships))
            mode_log[src_id] = "defense-coalition"
        mode_log[victim_id] = "defended-by-coalition"


def _try_doom_evac(world, victim, available, spent, target_locked, moves, mode_log):
    """V14.1b (Phase 3.2 V2): doomed planet evacuation.

    When rescue attempts have failed and the planet is about to flip, send
    its garrison to our highest-production friendly within reach. Preserves
    ships that would otherwise be captured. Returns True if a fleet was
    committed.

    V14.2 (Phase 3.6, Idea 5): attack-fallback. If no friendly destination,
    try sending the garrison to a winnable enemy/neutral target instead of
    letting the ships die with the planet. Prioritizes enemy planets in
    _enemy_recently_launched (they just emptied → weakly defended).
    """
    if not DOOM_EVAC_ENABLED:
        return False
    garrison = available[victim.id] - spent[victim.id]
    if garrison < DOOM_EVAC_MIN_SHIPS:
        return False

    
    
    
    friendly_candidates = []
    for dst in world.my_planets:
        if dst.id == victim.id:
            continue
        aim = aim_at_target(victim, dst, garrison, world.initial_by_id,
                            world.ang_vel, world=world)
        if aim is None:
            continue
        angle, turns = aim
        if turns > DOOM_EVAC_MAX_TRAVEL:
            continue
        
        
        score = int(dst.ships) + int(dst.production) * 5
        friendly_candidates.append((-score, int(turns), dst, angle))
    if friendly_candidates:
        friendly_candidates.sort()
        _score, turns, dst, angle = friendly_candidates[0]
        _commit_fleet(world, moves, spent, target_locked,
                      victim.id, dst.id, angle, turns, int(garrison))
        mode_log[victim.id] = "doom-evac-launched"
        mode_log[dst.id] = "doom-evac-recipient"
        return True

    
    if not DOOM_EVAC_ATTACK_FALLBACK_ENABLED:
        return False
    if DOOM_EVAC_ATTACK_FALLBACK_4P_ONLY and world.is_2p:
        return False
    attack_candidates = []
    for dst in world.planets:
        if dst.id == victim.id or dst.owner == world.player:
            continue
        if dst.id in target_locked:
            continue
        if not is_targetable(world, dst):
            continue
        aim = aim_at_target(victim, dst, garrison, world.initial_by_id,
                            world.ang_vel, world=world)
        if aim is None:
            continue
        angle, turns = aim
        if turns > DOOM_EVAC_MAX_TRAVEL:
            continue
        
        
        
        is_enemy = dst.owner != -1
        prod = int(dst.production) if is_enemy else 0
        arrival_garrison = int(dst.ships) + prod * int(turns)
        required = arrival_garrison + DOOM_EVAC_ATTACK_OVERKILL
        if int(garrison) < required:
            continue
        
        recently_launched_bonus = (
            -DOOM_EVAC_ATTACK_PREFER_LAUNCHED_BONUS
            if (is_enemy and dst.id in _enemy_recently_launched) else 0
        )
        rank = (
            recently_launched_bonus,
            -int(dst.production),
            int(turns),
            int(required),
        )
        attack_candidates.append((rank, dst, angle, turns))
    if not attack_candidates:
        return False
    attack_candidates.sort(key=lambda x: x[0])
    _rank, dst, angle, turns = attack_candidates[0]
    _commit_fleet(world, moves, spent, target_locked,
                  victim.id, dst.id, angle, turns, int(garrison))
    mode_log[victim.id] = "doom-evac-attack"
    mode_log[dst.id] = "doom-evac-attack-target"
    return True


def _find_defense_coalition(world, victim, deadline, need, available, spent):
    """Pick the closest pair of siblings whose combined ships meet `need`, both
    arrive by `deadline`, AND each contributes >= COALITION_MIN_PER_CONTRIBUTOR.
    Re-aims each contributor with its exact ship count.
    Returns [(src_id, src, angle, ships), ...] or None.
    """
    options = []
    for src in world.my_planets:
        if src.id == victim.id:
            continue
        avail = available[src.id] - spent[src.id]
        if avail < COALITION_MIN_PER_CONTRIBUTOR:
            continue
        aim = aim_at_target(src, victim, avail, world.initial_by_id, world.ang_vel, world=world)
        if aim is None:
            continue
        _angle_est, turns = aim
        if deadline is not None and turns > deadline:
            continue
        options.append((turns, src.id, src, avail))

    if len(options) < 2:
        return None
    options.sort()  

    for i in range(len(options)):
        for j in range(i + 1, len(options)):
            t_i, sid_i, s_i, a_i = options[i]
            t_j, sid_j, s_j, a_j = options[j]
            if a_i + a_j < need:
                continue
            ratio = a_i / float(a_i + a_j)
            ship_i = max(COALITION_MIN_PER_CONTRIBUTOR,
                         min(a_i, int(round(need * ratio))))
            ship_j = max(COALITION_MIN_PER_CONTRIBUTOR,
                         min(a_j, need - ship_i))
            while ship_i + ship_j < need:
                if ship_i < a_i:
                    ship_i += 1
                elif ship_j < a_j:
                    ship_j += 1
                else:
                    break
            if (ship_i + ship_j < need
                    or ship_i < COALITION_MIN_PER_CONTRIBUTOR
                    or ship_j < COALITION_MIN_PER_CONTRIBUTOR):
                continue
            
            aim_i = aim_at_target(s_i, victim, ship_i, world.initial_by_id, world.ang_vel, world=world)
            aim_j = aim_at_target(s_j, victim, ship_j, world.initial_by_id, world.ang_vel, world=world)
            if aim_i is None or aim_j is None:
                continue
            ang_i, turns_i = aim_i
            ang_j, turns_j = aim_j
            if (deadline is not None
                    and (turns_i > deadline or turns_j > deadline)):
                continue
            return [
                (sid_i, s_i, ang_i, ship_i, turns_i),
                (sid_j, s_j, ang_j, ship_j, turns_j),
            ]
    return None






COMET_EVAC_REMAINING_TURNS = 3   
COMET_EVAC_MIN_SHIPS = 5          






DOOM_EVAC_ENABLED = True
DOOM_EVAC_MIN_SHIPS = 5           
DOOM_EVAC_MAX_TRAVEL = 40         







DOOM_EVAC_ATTACK_FALLBACK_ENABLED = True
DOOM_EVAC_ATTACK_FALLBACK_4P_ONLY = True  
DOOM_EVAC_ATTACK_OVERKILL = 2     
DOOM_EVAC_ATTACK_PREFER_LAUNCHED_BONUS = 3  






PREEMPTIVE_DOOM_EVAC_ENABLED = True
PREEMPTIVE_DOOM_EVAC_2P_ONLY = False  

PREEMPTIVE_EVAC_DOOM_RATIO = 1.20  
PREEMPTIVE_EVAC_DEFAULT_WINDOW = 15  





PREEMPTIVE_EVAC_USE_LARGEST_SINGLE_ENEMY_4P = True


def handle_comet_evac(world, available, spent, target_locked, moves, mode_log):
    """For each owned comet about to expire, send ALL its ships to the nearest
    non-comet friendly planet (or neutral fallback). Ships left on a comet
    that exits the system are lost permanently — evacuation preserves them.
    """
    if not world.comet_remaining:
        return
    
    
    own_non_comet = [p for p in world.my_planets if p.id not in world.comet_ids]
    if not own_non_comet:
        
        
        own_non_comet = [p for p in world.planets
                         if p.owner == -1 and p.id not in world.comet_ids]
        if not own_non_comet:
            return
    for src in world.my_planets:
        rem = world.comet_remaining.get(src.id)
        if rem is None or rem > COMET_EVAC_REMAINING_TURNS:
            continue
        if src.id in mode_log:
            continue
        avail = max(0, available[src.id] - spent.get(src.id, 0))
        if avail < COMET_EVAC_MIN_SHIPS:
            continue
        
        
        
        
        
        best = None
        best_d = float("inf")
        for dst in own_non_comet:
            if dst.id == src.id:
                continue
            d_now = dist(src.x, src.y, dst.x, dst.y)
            est_turns = max(1, int(math.ceil(d_now / fleet_speed(max(1, int(avail))))))
            dst_px, dst_py = predict_target_position(dst, world, est_turns)
            d = dist(src.x, src.y, dst_px, dst_py)
            if d < best_d:
                best_d = d
                best = dst
        if best is None:
            continue
        aim = aim_at_target(src, best, avail, world.initial_by_id, world.ang_vel, world=world)
        if aim is None:
            continue
        angle, turns = aim
        
        
        if turns >= rem:
            
            
            pass
        _commit_fleet(world, moves, spent, target_locked,
                      src.id, best.id, angle, turns, int(avail))
        mode_log[src.id] = "comet-evac"






def handle_cheap_pickup(world, available, spent, target_locked, moves, mode_log):
    """V12.4d (4P-only): each idle source fires on the cheapest reachable
    low-garrison neutral if it can solo it. Bypasses the K=1 mid-game
    starvation where small free planets sit ignored because the source's
    K=1 nearest is a higher-garrison target. 4P-only — see CHEAP_PICKUP_4P_ONLY.
    """
    if not CHEAP_PICKUP_ENABLED:
        return
    if CHEAP_PICKUP_4P_ONLY and world.is_2p:
        return
    
    
    if LAUNCH_BLACKOUT_ENABLED and world.step >= TOTAL_STEPS - LAUNCH_BLACKOUT_TURNS:
        return
    if world.is_opening:
        max_travel = world.mode_params.get("expand_max_travel_opening", EXPAND_MAX_TRAVEL_OPENING)
    else:
        max_travel = world.mode_params["expand_max_travel_mid"]

    cheap_neutrals = [
        p for p in world.neutral_planets
        if int(p.ships) <= CHEAP_PICKUP_MAX_GARRISON
        and p.id not in target_locked
        and is_targetable(world, p)
    ]
    if not cheap_neutrals:
        return
    
    if CHEAP_PICKUP_MIN_PROD >= 2 and any(int(p.production) >= CHEAP_PICKUP_MIN_PROD for p in cheap_neutrals):
        cheap_neutrals = [p for p in cheap_neutrals if int(p.production) >= CHEAP_PICKUP_MIN_PROD]

    sources = sorted(world.my_planets,
                     key=lambda s: -(available[s.id] - spent[s.id]))
    for src in sources:
        avail = available[src.id] - spent[src.id]
        if avail < MIN_DISPATCH_SHIPS:
            continue
        if mode_log.get(src.id):
            continue
        candidates = []
        for n in cheap_neutrals:
            if n.id in target_locked:
                continue
            if friendly_already_committed(world, n.id):
                continue
            cost = int(n.ships) + 1
            if cost > avail:
                continue
            raw = dist(src.x, src.y, n.x, n.y)
            if raw / MAX_SPEED > max_travel + 4:
                continue
            eff = _effective_target_dist(src, n, world)
            candidates.append((cost, eff, n))
        if not candidates:
            continue
        candidates.sort(key=lambda kv: (kv[0], kv[1]))
        for _cost, _eff, n in candidates:
            plan = plan_solo_capture(world, src, n, avail, max_travel)
            if plan is None:
                continue
            angle, turns, ships = plan
            if RACE_ENABLED:
                enemy_eta = world.enemy_race_eta.get(n.id)
                if enemy_eta is not None and turns > enemy_eta:
                    continue
            if not _capture_holds_against_snipe(world, n, turns, int(ships)):
                continue
            if not _endgame_roi_ok(world, n, int(ships), turns):
                continue
            if not _neutral_tempo_ok(world, n, int(ships), turns):
                continue
            _commit_fleet(world, moves, spent, target_locked,
                          src.id, n.id, angle, turns, int(ships))
            mode_log[src.id] = "cheap-pickup"
            break


def _is_cheap_neutral_pick(world, target):
    """V14.1f (Phase 3.5, Idea 4): cheap-pick predicate for combat-contact gate.

    Returns True if the neutral target has small garrison AND there exists
    one of our planets within COMBAT_CHEAP_DIST. Used to preserve free
    pickups while dropping expensive neutrals during active combat.
    """
    if target.owner != -1:
        return True  
    if int(target.ships) > COMBAT_CHEAP_GARRISON:
        return False
    for mp in world.my_planets:
        if dist(mp.x, mp.y, target.x, target.y) <= COMBAT_CHEAP_DIST:
            return True
    return False


def _handle_search_expand_4p(world, available, spent, target_locked, moves, mode_log):
    """V12.9 Melis search-based expansion (4P only). Generates candidate step
    actions via generate_step_actions, ranks by melis_evaluate gain, commits
    top SEARCH_MAX_ACTIONS_TO_PICK that don't conflict (different targets +
    sources). Returns list of committed source ids so caller can skip them.
    """
    actions = search_step_action(
        world, max_per_source=SEARCH_MAX_PER_SOURCE,
        max_actions_to_eval=12,
        use_depth2=SEARCH_DEPTH2_ENABLED,
    )
    committed_sources = set()
    committed_targets = set()
    for act in actions[:SEARCH_MAX_ACTIONS_TO_PICK * 2]:
        if act["score"] <= 0:
            continue
        src_id = act["source_id"]
        tgt_id = act["target_id"]
        if src_id in committed_sources or tgt_id in committed_targets:
            continue
        if tgt_id in target_locked:
            continue
        
        src_status = mode_log.get(src_id)
        if src_status == "brain-reserved-lead":
            continue
        avail = available[src_id] - spent[src_id]
        if avail < act["ships"]:
            continue
        
        
        
        
        tgt = world.planet_by_id.get(tgt_id)
        
        if (world.stop_expanding_2p or world.prod_lead_stop_expand_4p or world.turn_cutoff_stop_expand) and tgt is not None and tgt.owner == -1:
            continue
        
        if world.stop_expand_lax and tgt is not None and tgt.owner == -1:
            if not _is_cheap_neutral_pick(world, tgt):
                continue
        if tgt is not None and tgt.owner == -1:
            turns_act = int(act["arrival_turn"])
            ships_act = int(act["ships"])
            if not _capture_holds_against_snipe(world, tgt, turns_act, ships_act):
                continue
            if not _endgame_roi_ok(world, tgt, ships_act, turns_act):
                continue
            if not _neutral_tempo_ok(world, tgt, ships_act, turns_act):
                continue
        _commit_fleet(world, moves, spent, target_locked,
                      src_id, tgt_id, act["angle"], act["arrival_turn"], act["ships"])
        mode_log[src_id] = "search-expand"
        committed_sources.add(src_id)
        committed_targets.add(tgt_id)
        if len(committed_sources) >= SEARCH_MAX_ACTIONS_TO_PICK:
            break
    return committed_sources


def handle_expand(world, available, spent, target_locked, moves, mode_log):
    
    if LAUNCH_BLACKOUT_ENABLED and world.step >= TOTAL_STEPS - LAUNCH_BLACKOUT_TURNS:
        return
    
    if (SEARCH_EXPAND_4P_ENABLED and not world.is_2p) or \
       (SEARCH_EXPAND_2P_ENABLED and world.is_2p):
        _handle_search_expand_4p(world, available, spent, target_locked, moves, mode_log)
        
    if world.is_opening:
        
        
        K = world.mode_params.get("expand_k_opening", EXPAND_K_OPENING)
        max_travel = world.mode_params.get("expand_max_travel_opening", EXPAND_MAX_TRAVEL_OPENING)
    else:
        K = world.mode_params["expand_k_mid"]
        max_travel = world.mode_params["expand_max_travel_mid"]

    nonfriendly = [
        p for p in world.planets
        if p.owner != world.player and is_targetable(world, p)
    ]
    
    
    
    if world.stop_expanding_2p or world.prod_lead_stop_expand_4p or world.turn_cutoff_stop_expand:
        nonfriendly = [p for p in nonfriendly if p.owner != -1]
    
    elif world.stop_expand_lax:
        nonfriendly = [
            p for p in nonfriendly
            if p.owner != -1 or _is_cheap_neutral_pick(world, p)
        ]
    if not nonfriendly:
        return

    def frontier_key(src):
        return min(dist(src.x, src.y, t.x, t.y) for t in nonfriendly)

    sources = sorted(world.my_planets, key=frontier_key)

    for src in sources:
        
        avail = _routine_avail(world, src, available[src.id] - spent[src.id])
        if avail < MIN_DISPATCH_SHIPS:
            continue
        
        
        
        status = mode_log.get(src.id)
        if status and status != "cheap-pickup":
            continue  

        candidates = _nearest_targets(src, world, K, max_travel, target_locked)
        fired_solo = False
        for tgt, _approx_dist in candidates:
            if friendly_already_committed(world, tgt.id):
                continue
            plan = plan_solo_capture(world, src, tgt, avail, max_travel)
            if plan is None:
                continue
            angle, turns, ships = plan
            if RACE_ENABLED and tgt.owner == -1:
                enemy_eta = world.enemy_race_eta.get(tgt.id)
                if enemy_eta is not None and turns > enemy_eta:
                    snipe = _plan_counter_snipe(world, src, tgt, avail, max_travel)
                    if snipe is None:
                        continue
                    angle, turns, ships = snipe
            if tgt.owner == -1 and not _capture_holds_against_snipe(world, tgt, turns, int(ships)):
                continue
            if not _endgame_roi_ok(world, tgt, int(ships), turns):
                continue
            if not _neutral_tempo_ok(world, tgt, int(ships), turns):
                continue
            
            
            
            if (
                FWD_SIM_ENABLED
                and world.is_2p
                and tgt.owner != world.player
                and not _fwd_capture_holds_2p(world, src, tgt, angle, turns, int(ships), world.player)
            ):
                continue
            _commit_fleet(world, moves, spent, target_locked,
                          src.id, tgt.id, angle, turns, int(ships))
            mode_log[src.id] = "expand-solo"
            fired_solo = True
            break

        if fired_solo:
            continue
        if not COALITION_ENABLED:
            continue

        coalition_max_travel = max_travel + COALITION_MAX_TRAVEL_BONUS
        for tgt, _ in candidates:
            if tgt.id in target_locked:
                continue
            if COALITION_NEUTRALS_ONLY and tgt.owner != -1:
                continue
            if friendly_already_committed(world, tgt.id):
                continue
            ok = _try_coalition_expand(
                world, src, tgt, coalition_max_travel, available, spent,
                target_locked, moves, mode_log,
            )
            if ok:
                break


def _effective_target_dist(src, tgt, world):
    """V12.4a rotation-aware distance proxy for target prefilter ranking.

    Predicts target position at expected travel time and returns distance
    to that future position. Static planets unchanged. Orbital planets
    rotating toward us get a shorter effective distance (promote);
    rotating away get longer (demote). One-step approximation — cheap;
    real arrival is computed later by aim_at_target inside plan_solo_capture.
    Affects WHICH targets get inspected when K is small, not which fleets fly.
    """
    raw = dist(src.x, src.y, tgt.x, tgt.y)
    if not ROT_AWARE_RANK_ENABLED:
        return raw
    init = world.initial_by_id.get(tgt.id)
    if init is None:
        return raw
    if dist(init.x, init.y, CENTER_X, CENTER_Y) + init.radius >= ROTATION_LIMIT:
        return raw
    speed = fleet_speed(50)
    travel = max(1, int(math.ceil(raw / speed)))
    if travel > 60:
        return raw
    px, py = predict_planet_position(tgt, world.initial_by_id, world.ang_vel, travel)
    return dist(src.x, src.y, px, py)


def _counter_snipe_candidates(world, src, max_travel, target_locked):
    """V12.4c: neutrals where a known enemy fleet will capture before us, and
    we can re-flip cheaply on a short follow-up. Returns [(target, raw_dist)]
    sorted by re-flip cost ascending. 2P-only — see COUNTER_SNIPE_2P_ONLY note.
    """
    if not COUNTER_SNIPE_ENABLED:
        return []
    if COUNTER_SNIPE_2P_ONLY and not world.is_2p:
        return []
    out = []
    for n in world.neutral_planets:
        if n.id in target_locked:
            continue
        if not is_targetable(world, n):
            continue
        enemy_eta = None
        enemy_remaining = None
        needed = int(n.ships) + 1
        for eta, owner, ships in world.arrivals_by_planet.get(n.id, []):
            if owner == world.player or owner == -1:
                continue
            if ships < needed:
                continue
            if enemy_eta is None or eta < enemy_eta:
                enemy_eta = int(eta)
                enemy_remaining = ships - int(n.ships)
        if enemy_eta is None:
            continue
        d = dist(src.x, src.y, n.x, n.y)
        speed = fleet_speed(50)
        my_eta_est = max(1, int(math.ceil(d / speed)))
        if my_eta_est > max_travel + 4:
            continue
        delay = my_eta_est - enemy_eta
        if delay < COUNTER_SNIPE_MIN_DELAY or delay > COUNTER_SNIPE_MAX_DELAY:
            continue
        prod = max(0, int(n.production))
        defender_at_my_arrival = max(0, int(enemy_remaining)) + prod * delay
        flip_cost = defender_at_my_arrival + 1
        if flip_cost > COUNTER_SNIPE_MAX_COST:
            continue
        out.append((flip_cost, n, d))
    out.sort(key=lambda kv: kv[0])
    return [(n, d) for _cost, n, d in out]


def _plan_counter_snipe(world, src, tgt, max_avail, max_travel):
    """V12.4c: size a small fleet to re-flip a neutral AFTER a known enemy
    fleet captures it. Returns (angle, turns, ships) or None. 2P-only.
    """
    if not COUNTER_SNIPE_ENABLED or tgt.owner != -1:
        return None
    if COUNTER_SNIPE_2P_ONLY and not world.is_2p:
        return None
    if max_avail < MIN_DISPATCH_SHIPS:
        return None
    enemy_eta = None
    enemy_remaining = None
    needed_to_take = int(tgt.ships) + 1
    for eta, owner, ships in world.arrivals_by_planet.get(tgt.id, []):
        if owner == world.player or owner == -1:
            continue
        if ships < needed_to_take:
            continue
        if enemy_eta is None or eta < enemy_eta:
            enemy_eta = int(eta)
            enemy_remaining = ships - int(tgt.ships)
    if enemy_eta is None:
        return None

    aim = aim_at_target(src, tgt, max_avail, world.initial_by_id, world.ang_vel, world=world)
    if aim is None:
        return None
    angle, turns = aim
    if turns > max_travel:
        return None
    delay = turns - enemy_eta
    if delay < COUNTER_SNIPE_MIN_DELAY or delay > COUNTER_SNIPE_MAX_DELAY:
        return None
    prod = max(0, int(tgt.production))
    defender = max(0, int(enemy_remaining)) + prod * delay
    ships = max(MIN_DISPATCH_SHIPS, defender + 1)
    if ships > max_avail or ships > COUNTER_SNIPE_MAX_COST:
        return None
    aim2 = aim_at_target(src, tgt, ships, world.initial_by_id, world.ang_vel, world=world)
    if aim2 is None:
        return None
    angle, turns = aim2
    if turns > max_travel:
        return None
    delay2 = turns - enemy_eta
    if delay2 < COUNTER_SNIPE_MIN_DELAY or delay2 > COUNTER_SNIPE_MAX_DELAY:
        return None
    defender2 = max(0, int(enemy_remaining)) + prod * delay2
    if ships < defender2 + 1:
        ships = defender2 + 1
        if ships > max_avail or ships > COUNTER_SNIPE_MAX_COST:
            return None
        aim3 = aim_at_target(src, tgt, ships, world.initial_by_id, world.ang_vel, world=world)
        if aim3 is None:
            return None
        angle, turns = aim3
        if turns > max_travel:
            return None
    return angle, turns, int(ships)


def _capture_holds_against_snipe(world, target, arrival_turn, ships_sent):
    """V12.4b: returns True if our post-capture garrison stays >0 through every
    KNOWN enemy fleet arriving within ANTI_SNIPE_HORIZON. Walks surplus +
    production growth between events; subtracts each enemy fleet at its eta;
    refuses if balance ever drops <=0. Friendly follow-ups credited.

    Gated to 2P only (ANTI_SNIPE_2P_ONLY): in 4P with 3 enemies the veto
    fires too often, starving expansion (192-game test: 55 third-place
    finishes vs 12_4a's 4). 2P has only one snipe source so the veto
    targets actual snipe traps without paralyzing expansion.
    """
    if not ANTI_SNIPE_ENABLED:
        return True
    if ANTI_SNIPE_2P_ONLY and not world.is_2p:
        return True
    if target.owner != -1:
        return True
    arrivals = world.arrivals_by_planet.get(target.id, [])
    enemy_after = []
    friendly_after = []
    for eta, owner, ships in arrivals:
        if ships <= 0:
            continue
        if eta <= arrival_turn:
            continue
        if eta - arrival_turn > ANTI_SNIPE_HORIZON:
            continue
        if owner == world.player:
            friendly_after.append((eta, ships))
        elif owner != -1:
            enemy_after.append((eta, ships))

    
    
    
    
    
    if REACTIVE_SNIPE_PROJECTION_ENABLED:
        for enemy_p in world.enemy_planets:
            e_ships = int(enemy_p.ships)
            if e_ships < REACTIVE_MIN_ENEMY_SHIPS:
                continue
            
            
            
            
            
            if SUN_SHADOW_REACTIVE_FILTER and not world.is_2p and segment_hits_sun(
                enemy_p.x, enemy_p.y, target.x, target.y
            ):
                continue
            d = dist(enemy_p.x, enemy_p.y, target.x, target.y)
            projected_force = max(REACTIVE_MIN_PROJECTED, int(e_ships * REACTIVE_EMIT_FRAC))
            speed = fleet_speed(projected_force)
            travel = max(1, int(math.ceil(d / speed)))
            
            snipe_eta = travel
            if snipe_eta <= arrival_turn:
                continue  
            if snipe_eta - arrival_turn > ANTI_SNIPE_HORIZON:
                continue
            enemy_after.append((snipe_eta, projected_force))

    if not enemy_after:
        return True

    
    if N6_USE_EFFECTIVE_PRE_GARRISON:
        _, pre_garrison = effective_garrison_at_arrival(target, arrival_turn, world)
    else:
        pre_garrison = garrison_at_arrival(target, arrival_turn)
    if ships_sent <= pre_garrison:
        return True
    surplus = ships_sent - pre_garrison
    prod = max(0, int(target.production))
    by_turn = defaultdict(int)
    for eta, ships in enemy_after:
        by_turn[eta] -= ships
    for eta, ships in friendly_after:
        by_turn[eta] += ships

    bal = surplus
    last_t = arrival_turn
    for eta in sorted(by_turn):
        bal += prod * (eta - last_t)
        bal += by_turn[eta]
        if bal <= 0:
            return False
        last_t = eta
    return True


def _tiebreak_hash(world, src_id, target_id):
    """Deterministic, replayable hash for breaking near-equal-distance ties.
    Salts on (player, step, src, target) so different turns / sources don't
    produce identical perturbations. Multiplicative mix instead of Python's
    hash() because PYTHONHASHSEED randomizes hash() across processes."""
    h = (int(world.player) * 2654435761) & 0xFFFFFFFF
    h ^= (int(world.step) * 1664525) & 0xFFFFFFFF
    h ^= (int(src_id) * 16777619) & 0xFFFFFFFF
    h ^= (int(target_id) * 2246822519) & 0xFFFFFFFF
    return h & 0xFFFF


def _nearest_targets(src, world, K, max_travel, target_locked):
    """Top-K nearest non-friendly, non-comet planets, plus any race-winnable
    contested neutrals appended at the FRONT regardless of K (V12.1a).

    Final travel-time and capture cost happen inside plan_solo_capture; the
    race-loss skip in handle_expand vetoes any target where we'd arrive after
    the enemy.

    V12.3c5 (2.5): in 2P, near-equal-distance candidates (within
    TIEBREAK_EPS_FRAC of best) are reordered by a deterministic
    (player, step, src, target) hash. Cracks symmetric-Nash mirror lock
    where two PATIENT bots otherwise pick the same target deterministically.
    Replayable via hash construction.
    """
    
    
    
    _f31_has_better = (
        world.is_2p
        and EXPAND_MIN_PROD_2P >= 2
        and any(int(n.production) >= EXPAND_MIN_PROD_2P for n in world.neutral_planets
                if n.id not in target_locked)
    )
    candidates = []
    for t in world.planets:
        if t.owner == world.player:
            continue
        if t.id in target_locked:
            continue
        if not is_targetable(world, t):
            continue
        if _neutral_blocked_by_cap(world, t):
            continue
        
        if _f31_has_better and t.owner == -1 and int(t.production) < EXPAND_MIN_PROD_2P:
            continue
        
        
        
        raw = dist(src.x, src.y, t.x, t.y)
        if raw / MAX_SPEED > max_travel + 4:
            continue
        eff = _effective_target_dist(src, t, world)
        
        
        weight = VALUE_WEIGHT_2P if world.is_2p else VALUE_WEIGHT_4P
        weighted = eff - max(0, int(t.production)) * weight
        
        
        
        if F1B_EXPAND_BONUS_ENABLED and t.owner != world.player and t.owner != -1:
            if t.id in _enemy_recently_launched:
                weighted -= F1B_EXPAND_BONUS
        
        
        
        if SO1_STATIC_PREFERENCE_ENABLED:
            init_t = world.initial_by_id.get(t.id)
            if init_t is not None:
                r_t = dist(init_t.x, init_t.y, CENTER_X, CENTER_Y)
                if r_t + init_t.radius >= ROTATION_LIMIT:
                    weighted -= SO1_STATIC_BONUS
        
        
        if (
            LEADER_BASH_ENABLED
            and not world.is_2p
            and world.contest_leader
            and world.step >= LEADER_BASH_MIN_STEP
            and world.leader_id is not None
            and t.owner == world.leader_id
        ):
            weighted -= LEADER_BASH_BONUS
        
        
        
        
        
        if (
            not world.is_2p
            and t.owner != -1
            and t.owner != world.player
            and world.opp_profile
            and t.owner in world.opp_profile
        ):
            prof = world.opp_profile[t.owner]
            if len(prof["emit"]) >= 5:
                avg_emit = sum(prof["emit"]) / len(prof["emit"])
                if avg_emit > 0.35:
                    weighted -= 5.0  
        
        
        
        if (
            WEAKEST_TARGET_ENABLED
            and not world.is_2p
            and world.step >= WEAKEST_TARGET_MIN_STEP
            and world.mode == "pressure"
            and world.weakest_enemy is not None
            and t.owner == world.weakest_enemy
        ):
            if world.weakest_enemy_prod_share < WEAKEST_DONT_FINISH_SHARE:
                weighted += WEAKEST_DONT_FINISH_PENALTY
            else:
                weighted -= WEAKEST_TARGET_BONUS
        
        if (
            F14_4A_2P_FOCUS_ENABLED
            and world.is_2p
            and world.focus_enemy_2p is not None
            and t.owner == world.focus_enemy_2p
        ):
            weighted -= F14_4A_2P_FOCUS_DIST_BONUS
        candidates.append((t, weighted, raw))
    if not candidates:
        return []
    candidates.sort(key=lambda kv: kv[1])
    
    
    
    
    if (FWD_SIM_RANK_BONUS_4P > 0 and not world.is_2p and len(candidates) > 1):
        baseline_proj = forward_project(
            world, horizon=FWD_SIM_HORIZON,
            project_opponent_moves=True, opponent_emit_fraction=0.30
        )
        baseline_score = forward_score(baseline_proj, world.player, 4, world)
        rerank = []
        topN = min(K + 2, len(candidates))
        for idx, (t, w, raw) in enumerate(candidates[:topN]):
            est_eta = max(1, int(math.ceil(raw / MAX_SPEED)))
            est_ships = needed_to_capture(t, est_eta) + 1
            proj = forward_project(
                world, our_capture_target=t.id, our_capture_turn=est_eta,
                our_capture_ships=est_ships, horizon=FWD_SIM_HORIZON,
                project_opponent_moves=True, opponent_emit_fraction=0.30
            )
            score_gain = forward_score(proj, world.player, 4, world) - baseline_score
            adjusted = w - FWD_SIM_RANK_BONUS_4P * score_gain
            rerank.append((t, adjusted, raw))
        candidates = rerank + candidates[topN:]
        candidates.sort(key=lambda kv: kv[1])
    if world.is_2p and TIEBREAK_ENABLED and len(candidates) > 1:
        best_d = candidates[0][1]
        eps = max(TIEBREAK_EPS_MIN, TIEBREAK_EPS_FRAC * best_d)
        def _k(kv):
            tgt, weighted_d, _raw = kv
            bucket = int(weighted_d / eps) if eps > 0 else 0
            return (bucket, _tiebreak_hash(world, src.id, tgt.id), weighted_d)
        candidates.sort(key=_k)

    counter_snipe = _counter_snipe_candidates(world, src, max_travel, target_locked)

    if not RACE_ENABLED or not world.enemy_race_eta:
        head = counter_snipe + [(t, raw) for t, _eff, raw in candidates[:K]]
        return _dedupe_targets(head)

    race_priority = []
    normal = []
    for t, _eff, raw in candidates:
        enemy_eta = world.enemy_race_eta.get(t.id)
        if enemy_eta is None or t.owner != -1:
            normal.append((t, raw))
            continue
        my_min = max(1, int(math.ceil(raw / fleet_speed(max(1, int(src.ships))))))
        if my_min <= enemy_eta:
            race_priority.append((t, raw))
        else:
            normal.append((t, raw))

    return _dedupe_targets(counter_snipe + race_priority + normal[:K])


def _dedupe_targets(seq):
    """V12.4c: preserve order, drop duplicates by target id (counter-snipe and
    race-priority can overlap with the K window)."""
    seen = set()
    out = []
    for tgt, d in seq:
        if tgt.id in seen:
            continue
        seen.add(tgt.id)
        out.append((tgt, d))
    return out


def _aim_partner(world, partner, tgt, ships, max_travel):
    """Aim a coalition partner with EXACT `ships` count. Returns (angle, turns) or None."""
    if ships < COALITION_MIN_PER_CONTRIBUTOR:
        return None
    aim = aim_at_target(partner, tgt, ships, world.initial_by_id, world.ang_vel, world=world)
    if aim is None:
        return None
    angle, turns = aim
    if turns > max_travel:
        return None
    return angle, turns


def _try_coalition_expand(world, src, tgt, max_travel, available, spent,
                          target_locked, moves, mode_log):
    """src can't take tgt alone; find a partner whose combined ships flip it.
    Each contributor must send >= COALITION_MIN_PER_CONTRIBUTOR (no tiny
    pieces). For tiny targets we DON'T split — the patient ethos prefers
    waiting for a solo fleet over showering a small target with two halves.
    """
    src_avail = available[src.id] - spent[src.id]
    if src_avail < COALITION_MIN_PER_CONTRIBUTOR:
        return False
    
    
    if int(tgt.ships) < COALITION_MIN_TARGET_SHIPS:
        return False

    
    
    
    
    partners = []
    for p in world.my_planets:
        if p.id == src.id:
            continue
        avail = available[p.id] - spent[p.id]
        if avail < COALITION_MIN_PER_CONTRIBUTOR:
            continue
        
        est = aim_at_target(p, tgt, avail, world.initial_by_id, world.ang_vel, world=world)
        if est is None:
            continue
        _, est_turns = est
        if est_turns > max_travel:
            continue
        partners.append((est_turns, p, avail))
    if not partners:
        return False
    partners.sort(key=lambda kv: kv[0])

    
    for est_turns, p, p_avail in partners:
        combined = src_avail + p_avail
        
        
        
        
        
        
        
        est_src = aim_at_target(src, tgt, src_avail, world.initial_by_id, world.ang_vel, world=world)
        if est_src is None:
            continue
        worst = max(est_src[1], est_turns)
        total_needed = needed_to_capture(tgt, worst)
        if combined < total_needed:
            continue

        
        ratio = src_avail / float(combined)
        s_src = max(COALITION_MIN_PER_CONTRIBUTOR,
                    min(src_avail, int(round(total_needed * ratio))))
        s_p = max(COALITION_MIN_PER_CONTRIBUTOR,
                  min(p_avail, total_needed - s_src))
        
        while s_src + s_p < total_needed:
            if s_src < src_avail:
                s_src += 1
            elif s_p < p_avail:
                s_p += 1
            else:
                break
        if s_src + s_p < total_needed:
            continue
        if s_src < COALITION_MIN_PER_CONTRIBUTOR or s_p < COALITION_MIN_PER_CONTRIBUTOR:
            continue
        if s_src > src_avail or s_p > p_avail:
            continue

        
        aim_src = aim_at_target(src, tgt, s_src, world.initial_by_id, world.ang_vel, world=world)
        aim_p = aim_at_target(p, tgt, s_p, world.initial_by_id, world.ang_vel, world=world)
        if aim_src is None or aim_p is None:
            continue
        a_src, t_src = aim_src
        a_p, t_p = aim_p
        if t_src > max_travel or t_p > max_travel:
            continue

        
        
        
        
        
        
        
        
        
        
        if world.is_2p and abs(t_src - t_p) > 1:
            continue

        
        
        
        post_eta = max(t_src, t_p)
        post_needed = needed_to_capture(tgt, post_eta)
        if s_src + s_p < post_needed:
            continue

        _commit_fleet(world, moves, spent, target_locked,
                      src.id, tgt.id, a_src, t_src, int(s_src))
        _commit_fleet(world, moves, spent, target_locked,
                      p.id, tgt.id, a_p, t_p, int(s_p))
        mode_log[src.id] = "expand-coalition"
        mode_log[p.id] = "expand-coalition"
        return True

    return False






def _routine_avail(world, planet, base_avail):
    """V14.1d iter g: production-tier reserve. Subtract a fraction of high-prod
    planet garrison from routine expand/hammer spending. The reserve grows
    naturally via production and is available to mega-hammer.
    """
    if not PROD_RESERVE_ENABLED:
        return base_avail
    if PROD_RESERVE_4P_ONLY and world.is_2p:
        return base_avail
    if world.step < PROD_RESERVE_TURN_MIN:
        return base_avail
    if int(planet.production) < PROD_RESERVE_MIN_PROD:
        return base_avail
    reserve = int(int(planet.ships) * PROD_RESERVE_FRAC)
    return max(0, base_avail - reserve)


def _brain_pick_lead(world, available, spent, mode_log, min_ships=None):
    """Shared lead-picker used by both _brain_reserve_lead (pre-pass) and
    handle_accumulator (post-defense). Returns Planet or None.

    Identical logic to handle_accumulator's original lead-selection so the
    reservation and the actual feeder-target agree. min_ships defaults to
    the accumulator's threshold; the brain pre-pass passes a higher value.

    B3b: when BRAIN_LEAD_PREFER_FRONTIER, score = avail - frontier_dist*weight
    so a frontier planet beats a deep-back-corner one even if the back has
    slightly more ships — a closer lead delivers strikes faster.
    """
    if min_ships is None:
        min_ships = ACCUMULATOR_LEAD_MIN_SHIPS
    enemies = world.enemy_planets
    candidates = []
    for p in world.my_planets:
        status = mode_log.get(p.id)
        
        if status and status != "brain-reserved-lead":
            continue
        avail = available[p.id] - spent[p.id]
        if avail < min_ships:
            continue
        threat = sum(int(ships) for eta, owner, ships
                     in world.arrivals_by_planet.get(p.id, [])
                     if owner != world.player and owner != -1)
        if threat >= avail * ACCUMULATOR_LEAD_THREAT_RATIO:
            continue
        if BRAIN_LEAD_PREFER_FRONTIER and enemies:
            frontier_dist = min(dist(p.x, p.y, e.x, e.y) for e in enemies)
            score = float(avail) - frontier_dist * BRAIN_LEAD_FRONTIER_WEIGHT
        else:
            score = float(avail)
        candidates.append((score, p))
    if not candidates:
        return None
    candidates.sort(key=lambda x: -x[0])
    return candidates[0][1]


def _brain_reserve_lead(world, available, spent, mode_log):
    """B1 (one-brain pre-pass): mark the future accumulator-lead with a
    sentinel so handle_expand can't drain it into small-ship pickups before
    handle_accumulator / handle_mega_hammer run.

    Runs after defense (which doesn't gate on mode_log status of sources)
    and before the expand → accumulator → mega-hammer chain. If defense
    later commits the same planet, defense overwrites mode_log[p.id] = 'defense'
    and the chain naturally skips it — life beats lead."""
    if not BRAIN_LEAD_RESERVE_ENABLED:
        return
    if not ACCUMULATOR_ENABLED:
        return
    if BRAIN_LEAD_RESERVE_4P_ONLY and world.is_2p:
        return
    if ACCUMULATOR_4P_ONLY and world.is_2p:
        return
    if world.step < ACCUMULATOR_TURN_MIN:
        return
    lead = _brain_pick_lead(world, available, spent, mode_log,
                            min_ships=BRAIN_LEAD_RESERVE_MIN_SHIPS)
    if lead is None:
        return
    
    
    if BRAIN_LEAD_RESERVE_REQUIRE_TARGET:
        has_target = False
        for tgt in world.enemy_planets:
            if int(tgt.ships) > MEGA_HAMMER_TARGET_GARRISON_MAX_ITER_H:
                continue
            aim = aim_at_target(lead, tgt, available[lead.id] - spent[lead.id],
                                world.initial_by_id, world.ang_vel, world=world)
            if aim is None:
                continue
            _, turns = aim
            if turns > MEGA_HAMMER_MAX_TRAVEL:
                continue
            has_target = True
            break
        if not has_target:
            return
    mode_log[lead.id] = "brain-reserved-lead"


def handle_accumulator(world, available, spent, target_locked, moves, mode_log):
    """V14.2 (Phase 3.7, Idea 6c): accumulator — feed surplus from safe
    backline planets to the lead stockpile each turn.

    Engine: fleet speed = 1 + 5×(log(ships)/log(1000))^1.5. One big fleet
    (1000 ships, speed 6) arrives faster AND survives tied-combat better
    than 4 fleets of 250 ships. Concentration > spread.

    Strategy: each turn, identify our planet with the most ships ("lead").
    For other planets in the safe backline (no incoming enemy threat AND
    surplus above reserve), send their surplus TO the lead. Over multiple
    turns, the lead accumulates a massive stockpile and handle_mega_hammer
    fires it as one overwhelming strike.

    Runs BEFORE handle_mega_hammer so accumulated ships are visible to
    mega-hammer this turn (but in-flight feeds arrive on later turns).
    """
    if not ACCUMULATOR_ENABLED:
        return
    if ACCUMULATOR_4P_ONLY and world.is_2p:
        return
    if world.step < ACCUMULATOR_TURN_MIN:
        return

    
    
    
    
    
    lead_candidates = []
    for p in world.my_planets:
        status = mode_log.get(p.id)
        if status and status != "brain-reserved-lead":
            continue
        avail = available[p.id] - spent[p.id]
        if avail < ACCUMULATOR_LEAD_MIN_SHIPS:
            continue
        
        threat = sum(int(ships) for eta, owner, ships
                     in world.arrivals_by_planet.get(p.id, [])
                     if owner != world.player and owner != -1)
        if threat >= avail * ACCUMULATOR_LEAD_THREAT_RATIO:
            continue
        lead_candidates.append((avail, p))
    if not lead_candidates:
        return
    lead_candidates.sort(key=lambda x: -x[0])
    lead_avail, lead = lead_candidates[0]

    
    feeders = []
    for p in world.my_planets:
        if p.id == lead.id or p.id in mode_log:
            continue
        
        threat = sum(int(ships) for eta, owner, ships
                     in world.arrivals_by_planet.get(p.id, [])
                     if owner != world.player and owner != -1)
        if threat > 0:
            continue
        avail = available[p.id] - spent[p.id]
        surplus = avail - ACCUMULATOR_FEEDER_KEEP_RESERVE
        if surplus < ACCUMULATOR_FEEDER_MIN_SURPLUS:
            continue
        
        aim = aim_at_target(p, lead, surplus, world.initial_by_id,
                            world.ang_vel, world=world)
        if aim is None:
            continue
        angle, turns = aim
        if turns > ACCUMULATOR_FEEDER_MAX_TRAVEL:
            continue
        feeders.append((turns, surplus, p, angle))

    if not feeders:
        return
    
    feeders.sort(key=lambda x: (x[0], -x[1]))
    fed_count = 0
    for turns, surplus, src, angle in feeders:
        if fed_count >= ACCUMULATOR_MAX_FEEDS_PER_TURN:
            break
        _commit_fleet(world, moves, spent, target_locked,
                      src.id, lead.id, angle, turns, int(surplus))
        mode_log[src.id] = "accumulator-feeder"
        fed_count += 1
    if fed_count > 0:
        
        if lead.id not in mode_log:
            mode_log[lead.id] = "accumulator-lead"


def handle_mega_hammer(world, available, spent, target_locked, moves, mode_log):
    """V14.1c (Phase 3.3): single-source overwhelming strike.

    For each of our planets with avail >= MEGA_HAMMER_SHIPS_MIN, find an
    enemy target whose garrison (after projected arrivals) is <=
    MEGA_HAMMER_TARGET_GARRISON_MAX and is within MEGA_HAMMER_MAX_TRAVEL
    turns. Launch the ENTIRE garrison as a single huge fleet — exploits
    the fleet-speed log formula (bigger = faster) and overwhelms
    reactive defense.

    Runs BEFORE handle_hammer so a successful mega strike isn't dissolved
    into the multi-stockpile coalition logic.
    """
    if not MEGA_HAMMER_ENABLED:
        return
    if MEGA_HAMMER_4P_ONLY and world.is_2p:
        return
    
    
    sources = sorted(world.my_planets,
                     key=lambda p: -(available[p.id] - spent[p.id]))
    fired_targets = set()
    fired_count = 0
    for src in sources:
        
        if MEGA_HAMMER_CONCENTRATE_ENABLED and fired_count >= MEGA_HAMMER_MAX_PER_TURN:
            break
        avail = available[src.id] - spent[src.id]
        
        
        
        prod = int(src.production)
        if FRESH_CAPTURE_INHERITANCE_ENABLED and src.id in _planet_capture_age:
            threshold = MEGA_HAMMER_SHIPS_MIN_FRESH
        else:
            threshold = MEGA_HAMMER_THRESHOLD_BY_PROD.get(prod, MEGA_HAMMER_SHIPS_MIN)
        if avail < threshold:
            continue  
        
        
        status = mode_log.get(src.id)
        if status and status not in ("cheap-pickup", "brain-reserved-lead"):
            continue
        
        best = None
        for tgt in world.enemy_planets:
            if tgt.id in target_locked or tgt.id in fired_targets:
                continue
            if int(tgt.ships) > MEGA_HAMMER_TARGET_GARRISON_MAX_ITER_H:
                continue
            aim = aim_at_target(src, tgt, avail, world.initial_by_id,
                                world.ang_vel, world=world)
            if aim is None:
                continue
            angle, turns = aim
            if turns > MEGA_HAMMER_MAX_TRAVEL:
                continue
            
            
            focus_bonus = 0
            if (F14_4A_2P_FOCUS_ENABLED and world.is_2p
                    and getattr(world, "focus_enemy_2p", None) is not None
                    and tgt.owner == world.focus_enemy_2p):
                focus_bonus = F14_4A_2P_FOCUS_MEGA_BONUS
            score = (int(tgt.production) + focus_bonus, -int(turns))
            if best is None or score > best[0]:
                best = (score, tgt, angle, turns)
        if best is None:
            continue
        _, tgt, angle, turns = best
        
        
        
        
        if MEGA_HAMMER_MELIS_VERIFY and turns > 0:
            proj = forward_project(
                world,
                our_capture_target=tgt.id,
                our_capture_turn=int(turns),
                our_capture_ships=int(avail),
                horizon=FWD_SIM_HORIZON + int(turns),
                project_opponent_moves=True,
                opponent_emit_fraction=MEGA_HAMMER_VERIFY_OPP_EMIT,
            )
            end_owner, _ = proj.get(tgt.id, (-1, 0))
            if end_owner != world.player:
                continue
        _commit_fleet(world, moves, spent, target_locked,
                      src.id, tgt.id, angle, turns, int(avail))
        mode_log[src.id] = "mega-hammer-launched"
        mode_log[tgt.id] = "mega-hammer-target"
        fired_targets.add(tgt.id)
        fired_count += 1


def handle_hammer(world, available, spent, target_locked, moves, mode_log):
    """One persistent plan at a time. Plan picks a strong-production enemy
    target and a set of stockpiles whose combined fleet arriving simultaneously
    beats defender_at_arrival × overkill. Launches stagger so all fleets land
    on the same turn. Plan aborts if defender reinforces past committed strength.
    """
    global _hammer_plan
    if not HAMMER_ENABLED:
        return
    if not world.enemy_planets:
        _hammer_plan = None
        return

    if _hammer_plan is not None:
        
        target = world.planet_by_id.get(_hammer_plan["target_id"])
        if target is None or target.owner == world.player:
            _hammer_plan = None
        else:
            
            arrival_rel = _hammer_plan["target_arrival_abs"] - world.step
            if arrival_rel <= 0:
                _hammer_plan = None
            else:
                d_owner, d_ships = predict_defender_at_arrival(world, target, arrival_rel)
                if d_ships > _hammer_plan["committed_strength"] / HAMMER_ABORT_OVERRUN_RATIO:
                    _hammer_plan = None

    if _hammer_plan is None:
        
        if not _hammer_should_fire(world):
            return
        plan = _build_hammer_plan(world, available, spent)
        if plan is None:
            return
        
        
        
        if HAMMER_MELIS_VERIFY:
            target = world.planet_by_id.get(plan["target_id"])
            if target is not None:
                arrival_rel = plan["target_arrival_abs"] - world.step
                if arrival_rel > 0:
                    proj = forward_project(
                        world,
                        our_capture_target=plan["target_id"],
                        our_capture_turn=int(arrival_rel),
                        our_capture_ships=int(plan["committed_strength"]),
                        horizon=FWD_SIM_HORIZON + arrival_rel,
                        project_opponent_moves=True,
                        opponent_emit_fraction=0.30,
                    )
                    end_owner, _ = proj.get(plan["target_id"], (-1, 0))
                    if end_owner != world.player:
                        return  
        _hammer_plan = plan

    
    plan = _hammer_plan
    completed_launches = []
    for src_id, launch in list(plan["launches"].items()):
        if launch.get("fired"):
            continue
        if launch["fire_turn_abs"] > world.step:
            continue  
        src = world.planet_by_id.get(src_id)
        if src is None or src.owner != world.player:
            completed_launches.append(src_id)
            continue
        ships = launch["ships"]
        if ships < HAMMER_MIN_PER_CONTRIBUTOR:
            completed_launches.append(src_id)
            continue
        avail = available[src_id] - spent[src_id]
        if avail < ships:
            completed_launches.append(src_id)
            continue
        target = world.planet_by_id[plan["target_id"]]
        
        aim = aim_at_target(src, target, ships, world.initial_by_id, world.ang_vel, world=world)
        if aim is None:
            completed_launches.append(src_id)
            continue
        angle, turns = aim
        _commit_fleet(world, moves, spent, target_locked,
                      src_id, plan["target_id"], angle, turns, int(ships))
        mode_log[src_id] = "hammer"
        launch["fired"] = True

    
    for sid in completed_launches:
        plan["launches"].pop(sid, None)
    if not plan["launches"] or all(l.get("fired") for l in plan["launches"].values()):
        _hammer_plan = None


def _hammer_should_fire(world):
    """Trigger condition: my prod share >= mode-specific threshold AND a strong
    enemy production target is reachable, OR we're in late-flush mode."""
    if world.is_late:
        return True
    threshold = world.mode_params["hammer_prod_share"]
    if world.my_prod_share < threshold:
        return False
    return True


def _build_hammer_plan(world, available, spent):
    """Pick best target + stockpile set. Stockpiles are planets with ships >= MIN
    or promoted-by-idle. Combined arrival fleet must beat defender × overkill.
    Returns plan dict or None."""
    
    
    
    stockpile_min = world.mode_params.get("hammer_stockpile_min", HAMMER_STOCKPILE_MIN)
    stockpiles = []
    for p in world.my_planets:
        
        avail = _routine_avail(world, p, available[p.id] - spent[p.id])
        if avail < HAMMER_MIN_PER_CONTRIBUTOR:
            continue
        promoted = p.id in _promoted_stockpiles
        if avail < stockpile_min and not promoted:
            continue
        stockpiles.append((p, avail))
    if not stockpiles:
        return None

    overkill = LATE_FLUSH_OVERKILL_RATIO if world.is_late else world.mode_params["hammer_overkill"]

    targets = [
        p for p in world.enemy_planets
        if is_targetable(world, p) and p.production >= HAMMER_TARGET_PROD_MIN
    ]
    if not targets:
        if world.is_late:
            targets = [p for p in world.enemy_planets if is_targetable(world, p)]
        if not targets:
            return None

    best = None
    for tgt in targets:
        
        per_src = []
        for src, avail in stockpiles:
            aim = aim_at_target(src, tgt, max(1, avail), world.initial_by_id, world.ang_vel, world=world)
            if aim is None:
                continue
            angle, turns = aim
            if turns > HAMMER_MAX_TRAVEL:
                continue
            per_src.append((turns, src, avail, angle))
        if not per_src:
            continue
        
        per_src.sort()  
        target_arrival = per_src[-1][0]
        d_owner, d_ships = predict_defender_at_arrival(world, tgt, target_arrival)
        if d_owner == world.player:
            continue
        required = int(math.ceil(d_ships * overkill)) + 1

        
        accum = 0
        chosen = []
        for turns, src, avail, angle in per_src:
            chosen.append((turns, src, avail, angle))
            accum += avail
            if accum >= required:
                break
        if accum < required:
            continue

        
        
        
        
        
        
        
        slack = accum - required
        if slack > 0 and chosen:
            last_turn, last_src, last_avail, last_angle = chosen[-1]
            
            
            
            
            
            
            oversend_active = (
                HAMMER_NO_THREAT_OVERSEND_ENABLED
                and (not HAMMER_NO_THREAT_OVERSEND_2P_ONLY or world.is_2p)
            )
            
            last_src_threat = sum(
                int(ships) for eta, owner, ships
                in world.arrivals_by_planet.get(last_src.id, [])
                if owner != world.player and owner != -1
            )
            
            
            safe_surplus_ok = (
                HAMMER_SAFE_SURPLUS_OVERSEND_ENABLED
                and last_avail >= required * HAMMER_SAFE_SURPLUS_RATIO
                and last_src_threat <= last_avail * HAMMER_OVERSEND_MAX_THREAT_RATIO
            )
            if safe_surplus_ok:
                
                pass
            elif oversend_active and HAMMER_ALWAYS_OVERSEND_2P and world.is_2p:
                
                pass
            elif oversend_active and last_src_threat == 0:
                
                pass
            else:
                trimmed = last_avail - slack
                if trimmed < HAMMER_MIN_PER_CONTRIBUTOR:
                    chosen.pop()
                    if not chosen or sum(c[2] for c in chosen) < required - last_avail:
                        chosen.append((last_turn, last_src, last_avail, last_angle))
                else:
                    chosen[-1] = (last_turn, last_src, trimmed, last_angle)

        score = required - target_arrival * 0.5  
        
        if (F14_4A_2P_FOCUS_ENABLED and world.is_2p
                and getattr(world, "focus_enemy_2p", None) is not None
                and tgt.owner == world.focus_enemy_2p):
            score += F14_4A_2P_FOCUS_HAMMER_BONUS
        
        
        if FLEET_INTENT_ENABLED and tgt.id in _enemy_recently_launched:
            score += FLEET_INTENT_HAMMER_BONUS
        
        
        
        if R1_RECAPTURE_PRIORITY_ENABLED and tgt.id in _freshly_lost_planets:
            score += R1_RECAPTURE_HAMMER_BONUS
        
        
        
        
        
        
        
        if not world.is_2p:
            my_strength = world.owner_strength.get(world.player, 0)
            enemy_strengths = [
                (world.owner_strength[o], o)
                for o in world.owner_strength
                if o not in (-1, world.player) and world.owner_strength[o] > 0
            ]
            if enemy_strengths:
                max_enemy_strength, max_enemy_owner = max(enemy_strengths)
                if max_enemy_strength > my_strength and tgt.owner == max_enemy_owner:
                    score = score - abs(score) * 0.3
        cand = {
            "target_id": tgt.id,
            "target_arrival_abs": world.step + target_arrival,
            "committed_strength": sum(c[2] for c in chosen),
            "score": score,
            "launches": {},
        }
        for turns, src, ships, angle in chosen:
            fire_turn_rel = target_arrival - turns
            cand["launches"][src.id] = {
                "fire_turn_abs": world.step + fire_turn_rel,
                "ships": int(ships),
                "angle": float(angle),
                "fired": False,
            }
        if best is None or cand["score"] > best["score"]:
            best = cand
    return best






def handle_multiprong(world, available, spent, target_locked, moves, mode_log):
    """If a hammer is committed at target T and a credible enemy reinforcer E
    is pumping ships into T, open a same-turn second prong at E using surplus
    ships. Strict credibility gates: 2P only, real-reinforcement gate, post-
    launch garrison gate, prong-credibility gate.

    The picture-1 failure: bot fed all output into one stream against an
    actively-reinforced target. Two prongs force the opponent to choose:
    defend T -> we take E (no more reinforcements -> hammer lands clean);
    defend E -> they pull ships off T (hammer lands clean).
    """
    if not MULTIPRONG_ENABLED:
        return
    if MULTIPRONG_2P_ONLY and not world.is_2p:
        return
    if _hammer_plan is None:
        return

    target_id = _hammer_plan.get("target_id")
    target = world.planet_by_id.get(target_id)
    if target is None or target.owner == world.player or target.owner == -1:
        return
    arrival_rel = _hammer_plan.get("target_arrival_abs", world.step) - world.step
    if arrival_rel <= 0:
        return
    committed = int(_hammer_plan.get("committed_strength", 0))
    if committed <= 0:
        return

    
    
    reinforcer_ships = defaultdict(int)
    for f in world.fleets:
        if int(f.ships) <= 0:
            continue
        if f.owner == world.player or f.owner == -1:
            continue
        ftarget, _eta = fleet_target_planet(
            f, world.planets, world.initial_by_id, world.ang_vel
        )
        if ftarget is None or ftarget.id != target_id:
            continue
        reinforcer_ships[int(f.from_planet_id)] += int(f.ships)
    if not reinforcer_ships:
        return

    
    _, defender_at_arrival = predict_defender_at_arrival(world, target, arrival_rel)
    needed_t = int(math.ceil(defender_at_arrival)) + 1
    deficit = max(0, needed_t - committed)

    
    
    
    
    min_reinforce = max(1, int(math.ceil(deficit * MULTIPRONG_REINFORCER_MIN_RATIO)))

    
    candidates = []
    for src_id, ship_count in reinforcer_ships.items():
        src = world.planet_by_id.get(src_id)
        if src is None:
            continue
        if src.owner == world.player or src.owner == -1:
            continue
        if ship_count < min_reinforce:
            continue
        candidates.append((src, ship_count))
    if not candidates:
        return
    
    candidates.sort(key=lambda kv: kv[1], reverse=True)

    
    for reinforcer, in_flight in candidates:
        if reinforcer.id in target_locked:
            continue
        if not is_targetable(world, reinforcer):
            continue
        
        prong = _build_multiprong_attack(
            world, reinforcer, available, spent, target_locked
        )
        if prong is None:
            continue
        prong_strength, prong_arrival, prong_landings, e_at_arrival = prong

        
        
        
        
        if prong_strength <= e_at_arrival * MULTIPRONG_E_OVERKILL:
            continue
        
        needed_e = int(math.ceil(e_at_arrival)) + 1
        if committed + prong_strength < needed_t + int(round(needed_e * MULTIPRONG_CREDIBILITY_FACTOR)):
            continue

        
        for src_id, src, angle, ships, turns in prong_landings:
            _commit_fleet(
                world, moves, spent, target_locked,
                src_id, reinforcer.id, angle, turns, int(ships),
            )
            mode_log[src_id] = "multiprong"
        mode_log[reinforcer.id] = "multiprong-target"
        return  


def _build_multiprong_attack(world, target, available, spent, target_locked):
    """Plan a 1-3 source attack on `target` from surplus ships (post-hammer,
    post-expand, post-defense). Returns (strength, arrival_turn, landings, e_at_arrival) or None.

    Each landing: (src_id, src, angle, ships, turns).
    """
    sources = []
    for src in world.my_planets:
        avail = available[src.id] - spent[src.id]
        if avail < MULTIPRONG_MIN_PER_CONTRIBUTOR:
            continue
        
        aim = aim_at_target(src, target, max(MULTIPRONG_MIN_PER_CONTRIBUTOR, avail), world.initial_by_id, world.ang_vel, world=world)
        if aim is None:
            continue
        _angle, est_turns = aim
        if est_turns > MULTIPRONG_MAX_TRAVEL:
            continue
        sources.append((est_turns, src, avail))
    if not sources:
        return None
    sources.sort(key=lambda kv: kv[0])  

    
    
    chosen = []
    for est_turns, src, avail in sources[:MULTIPRONG_MAX_PARTICIPANTS]:
        chosen.append((est_turns, src, avail))
        common_arrival = max(t for t, _, _ in chosen)
        _, e_at_arrival = predict_defender_at_arrival(world, target, common_arrival)
        total_avail = sum(a for _, _, a in chosen)
        required = int(math.ceil(e_at_arrival * MULTIPRONG_E_OVERKILL)) + 1
        if total_avail >= required:
            break
    common_arrival = max(t for t, _, _ in chosen)
    _, e_at_arrival = predict_defender_at_arrival(world, target, common_arrival)
    required = int(math.ceil(e_at_arrival * MULTIPRONG_E_OVERKILL)) + 1
    total_avail = sum(a for _, _, a in chosen)
    if total_avail < required:
        return None

    
    slack = total_avail - required
    if slack > 0 and chosen:
        last_turn, last_src, last_avail = chosen[-1]
        trimmed = last_avail - slack
        if trimmed >= MULTIPRONG_MIN_PER_CONTRIBUTOR:
            chosen[-1] = (last_turn, last_src, trimmed)

    
    landings = []
    final_strength = 0
    for est_turns, src, ships in chosen:
        if ships < MULTIPRONG_MIN_PER_CONTRIBUTOR:
            return None
        aim = aim_at_target(src, target, ships, world.initial_by_id, world.ang_vel, world=world)
        if aim is None:
            return None
        angle, turns = aim
        if turns > MULTIPRONG_MAX_TRAVEL:
            return None
        landings.append((src.id, src, angle, int(ships), int(turns)))
        final_strength += int(ships)

    
    final_arrival = max(turns for _, _, _, _, turns in landings)
    _, final_defender = predict_defender_at_arrival(world, target, final_arrival)
    final_required = int(math.ceil(final_defender * MULTIPRONG_E_OVERKILL)) + 1
    if final_strength < final_required:
        return None

    return final_strength, final_arrival, landings, final_defender






def plan_moves(world, deadline=None):
    global _planet_idle_counts, _promoted_stockpiles, _pending_commitments

    
    
    
    
    
    
    def _commitment_viable(c):
        if c["arrival_abs"] <= world.step:
            return False
        target = world.planet_by_id.get(c["target_id"])
        if target is None:
            return False
        if target.owner == world.player:
            return False
        if FAILTOLERANT_ENABLED:
            owner_at_commit = c.get("owner_at_commit")
            if owner_at_commit is not None and int(target.owner) != int(owner_at_commit):
                return False
        return True
    _pending_commitments[:] = [c for c in _pending_commitments if _commitment_viable(c)]

    
    _update_neutral_watchlist(world)

    moves = []
    spent = defaultdict(int)
    target_locked = set()
    mode_log = {}

    
    rescue_needs = {}
    available = {}
    for p in world.my_planets:
        arrivals = world.arrivals_by_planet.get(p.id, [])
        reserve, holds, deficit, dline = compute_planet_reserve(
            p, arrivals, world.player
        )
        available[p.id] = max(0, int(p.ships) - reserve)
        if not holds:
            rescue_needs[p.id] = (deficit, dline, p)
            mode_log[p.id] = "absorb-need-rescue"
        elif arrivals:
            mode_log[p.id] = "absorb"

    
    
    
    def _over_budget():
        return deadline is not None and time.perf_counter() >= deadline

    
    
    
    handle_comet_evac(world, available, spent, target_locked, moves, mode_log)

    
    handle_defense(world, rescue_needs, available, spent, target_locked,
                   moves, mode_log)

    
    
    
    
    _brain_reserve_lead(world, available, spent, mode_log)

    
    
    if not _over_budget():
        if not (SEARCH_EXPAND_4P_ENABLED and not world.is_2p
                and SEARCH_DISABLES_CHEAP_PICKUP):
            handle_cheap_pickup(world, available, spent, target_locked, moves, mode_log)

    
    if not _over_budget():
        handle_expand(world, available, spent, target_locked, moves, mode_log)

    
    
    
    
    if not _over_budget():
        handle_accumulator(world, available, spent, target_locked, moves, mode_log)

    
    
    if not _over_budget():
        handle_mega_hammer(world, available, spent, target_locked, moves, mode_log)

    
    if not _over_budget():
        handle_hammer(world, available, spent, target_locked, moves, mode_log)

    
    if not _over_budget():
        handle_multiprong(world, available, spent, target_locked, moves, mode_log)

    

    
    for p in world.my_planets:
        if mode_log.get(p.id) and "absorb" not in mode_log[p.id]:
            _planet_idle_counts[p.id] = 0
        else:
            _planet_idle_counts[p.id] = _planet_idle_counts.get(p.id, 0) + 1
            if _planet_idle_counts[p.id] >= HAMMER_SURROUNDED_PROMOTE_TURNS:
                _promoted_stockpiles.add(p.id)

    return moves






def agent(obs, config=None):
    global _agent_step, _hammer_plan, _planet_idle_counts, _promoted_stockpiles, _pending_commitments
    global _game_num_players, _2p_patient_streak, _2p_prod_share_history

    global _opp_profile  
    obs_step = _read(obs, "step", 0) or 0
    if obs_step == 0:
        _agent_step = 0
        _hammer_plan = None
        _planet_idle_counts = {}
        _promoted_stockpiles = set()
        _pending_commitments = []
        _game_num_players = None
        _2p_patient_streak = 0
        _2p_prod_share_history = []
        _neutral_prev_ships.clear()
        _neutral_wounded.clear()
        _enemy_prev_ships.clear()
        _enemy_recently_launched.clear()
        _planet_prev_owner.clear()
        _freshly_lost_planets.clear()
        _opp_profile = {}
    _agent_step += 1

    start = time.perf_counter()
    world = World(obs, inferred_step=_agent_step - 1)
    if not world.my_planets:
        return []

    
    if not world.is_2p:
        _update_opp_profile_4p(world)

    act_timeout = _read(config, "actTimeout", 1.0) if config is not None else 1.0
    soft_budget = max(0.5, act_timeout * SOFT_DEADLINE_FRACTION)
    deadline = start + soft_budget

    return plan_moves(world, deadline=deadline)


__all__ = ["agent", "Planet", "Fleet"]