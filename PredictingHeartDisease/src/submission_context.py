"""Build submission context from Kaggle history + local files for NIM analysis."""
import json
import re
from pathlib import Path

from .config import ATTEMPT_LOG, SUBMISSIONS_DIR

# Map fileName patterns to action names
ACTION_FROM_FILE = {
    "baseline_only": "baseline_only",
    "remove_features": "remove_features",
    "baseline_xgboost": "baseline_only",
    "improved": "improved",
    "single_seed": "single_seed",
    "lightgbm": "lightgbm",
    "optuna_tune": "optuna_tune",
    "xgboost_tuned": "xgboost_tuned",
}


def load_attempt_log(max_entries: int = 20) -> list[dict]:
    """Read last N entries from attempt_log.jsonl."""
    if not ATTEMPT_LOG.exists():
        return []
    lines = ATTEMPT_LOG.read_text(encoding="utf-8").strip().splitlines()
    entries = []
    for line in lines[-max_entries:]:
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return entries


def parse_action_from_submission(file_name: str, description: str) -> str:
    """Extract action from fileName or description. E.g. submission_remove_features.csv -> remove_features."""
    name = (file_name or "").replace(".csv", "").lower()
    desc = (description or "").lower()
    for key, action in ACTION_FROM_FILE.items():
        if key in name or key.replace("_", " ") in desc:
            return action
    # Try pattern: "Auto iter N - ACTION CV X.XXXX" or "ACTION CV X.XXXX"
    m = re.search(r"auto iter \d+ - ([\w_]+) cv", desc)
    if m:
        return m.group(1).lower()
    m = re.search(r"([\w_]+)\s+cv\s+[\d.]+", desc)
    if m:
        return m.group(1).lower()
    if "baseline" in name or "baseline" in desc:
        return "baseline_only"
    if "improved" in name or "improved" in desc:
        return "improved"
    return "unknown"


def _fetch_kaggle_submissions(page_size: int = 20) -> list[dict]:
    from kaggle.api.kaggle_api_extended import KaggleApi
    api = KaggleApi()
    api.authenticate()
    subs = api.competition_submissions("playground-series-s6e2", page_size=page_size)
    results = []
    for s in subs:
        pub = getattr(s, "publicScore", None) or getattr(s, "public_score", None)
        desc = getattr(s, "description", None) or ""
        fname = getattr(s, "fileName", None) or getattr(s, "file_name", None) or getattr(s, "ref", None) or ""
        status = getattr(s, "status", "")
        if pub is not None and "complete" in str(status).lower():
            try:
                results.append({"fileName": str(fname), "description": str(desc), "publicScore": float(pub)})
            except (TypeError, ValueError):
                pass
    return results


def get_submission_context(page_size: int = 20) -> dict:
    """
    Fetch Kaggle submissions, check local files, build tried_actions and context for NIM.
    Returns:
        tried_actions: {action: best_score} - best score per action (deduplicated)
        submission_history: list of {fileName, description, publicScore, action, has_local}
        best_score: current best public score
    """
    subs = _fetch_kaggle_submissions(page_size)
    tried_actions: dict[str, float] = {}
    history = []
    best_score = 0.0

    for s in subs:
        fname = s.get("fileName", "")
        desc = s.get("description", "")
        score = s.get("publicScore", 0.0)
        best_score = max(best_score, score)

        action = parse_action_from_submission(fname, desc)
        local_path = SUBMISSIONS_DIR / fname if fname else None
        has_local = local_path.exists() if local_path else False

        # Keep best score per action (in case we submitted same action multiple times)
        if action not in tried_actions or score > tried_actions[action]:
            tried_actions[action] = score

        history.append({
            "fileName": fname or "(no filename)",
            "description": (desc or "")[:80],
            "publicScore": score,
            "action": action,
            "has_local": has_local,
        })

    attempt_log = load_attempt_log(max_entries=20)

    return {
        "tried_actions": tried_actions,
        "submission_history": history,
        "attempt_log": attempt_log,
        "best_score": best_score,
    }
