"""
Automated improvement loop: analyze -> train -> submit -> wait -> update baseline -> repeat.
Open-ended: NIM suggests any action; we attempt execution and log results for future context.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / ".env")

COMPETITION = "playground-series-s6e2"
BASELINE_FILE = project_root / "research" / "baseline.json"
ATTEMPT_LOG_FILE = project_root / "research" / "attempt_log.jsonl"
SUBMISSIONS_DIR = project_root / "submissions"


def load_baseline() -> dict:
    if BASELINE_FILE.exists():
        return json.loads(BASELINE_FILE.read_text())
    return {"best_public_score": 0.0, "best_submission": "", "best_description": ""}


def save_baseline(data: dict):
    BASELINE_FILE.parent.mkdir(parents=True, exist_ok=True)
    BASELINE_FILE.write_text(json.dumps(data, indent=2))


def _suggestion_hash(suggestion: dict) -> str:
    """Hash of action + sorted params for duplicate detection."""
    action = suggestion.get("action", "")
    params = suggestion.get("params") or {}
    canonical = json.dumps({"action": action, "params": dict(sorted(params.items()))}, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()[:12]


def append_attempt_log(entry: dict):
    """Append one entry to attempt_log.jsonl."""
    ATTEMPT_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ATTEMPT_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def get_submission_scores(page_size: int = 20):
    from kaggle.api.kaggle_api_extended import KaggleApi
    api = KaggleApi()
    api.authenticate()
    subs = api.competition_submissions(COMPETITION, page_size=page_size)
    results = []
    for s in subs:
        pub = getattr(s, "publicScore", None) or getattr(s, "public_score", None)
        desc = getattr(s, "description", None) or ""
        fname = getattr(s, "fileName", None) or getattr(s, "file_name", None) or ""
        status = getattr(s, "status", "")
        if pub is not None and "complete" in str(status).lower():
            try:
                results.append({
                    "fileName": str(fname),
                    "description": str(desc),
                    "publicScore": float(pub),
                })
            except (TypeError, ValueError):
                pass
    return results


def ask_nim_for_suggestion(
    baseline_score: float,
    submission_context: dict,
) -> tuple[str, dict]:
    """
    Get open-ended suggestion from NIM.
    Returns (analysis_text, suggestion_dict) where suggestion_dict has action, params, rationale.
    """
    from src.nim_client import chat

    history = submission_context.get("submission_history", [])
    attempt_log = submission_context.get("attempt_log", [])

    history_str = "\n".join(
        f"  - {h.get('fileName', '?')}: {h['publicScore']:.5f} | {(h.get('description') or '')[:50]} | local={h.get('has_local', False)}"
        for h in history[:15]
    )

    attempt_str = "\n".join(
        f"  - {e.get('action', '?')} params={e.get('params', {})} -> cv={e.get('cv_auc')} pub={e.get('public_score')} improvement={e.get('improvement')} error={e.get('error')}"
        for e in attempt_log[-15:]
    ) if attempt_log else "  (none yet)"

    tried_hashes = [e.get("config_hash", "") for e in attempt_log if e.get("config_hash")]

    prompt = f"""You are a Kaggle competition expert. Analyze our submission history and attempt log, then suggest ONE improvement to try next.

**Competition:** Playground S6E2 - Predicting Heart Disease (binary classification, ROC AUC metric)

**Best score so far:** {baseline_score:.5f}

**Full submission history (from Kaggle):**
{history_str}

**Attempt log (what we have tried and results):**
{attempt_str}

**Capabilities (what we can execute):**
- XGBoost: action "baseline_only" or "xgboost_tuned", params: learning_rate, n_estimators, max_depth, min_child_weight, subsample, colsample_bytree, reg_alpha, reg_lambda, gamma
- LightGBM: action "lightgbm", params: learning_rate, n_estimators, max_depth, num_leaves, min_child_samples, subsample, colsample_bytree, reg_alpha, reg_lambda
- Feature flags: params use_features (bool), seeds ("single" or list of ints)
- Optuna tuning: action "optuna_tune", params: n_trials (int, default 30)
- Other: action "remove_features" (no interaction features), "single_seed" (seed 42 only)

**Your task:** Suggest something DIFFERENT from the attempt log. Avoid repeating exact configs. In 1-2 paragraphs explain your rationale, then return JSON:
{{"action": "<action_name>", "params": {{...}}, "rationale": "<short reason>"}}
"""

    analysis = chat(prompt)
    suggestion = {"action": "baseline_only", "params": {}, "rationale": ""}

    code_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", analysis)
    if code_match:
        try:
            block = json.loads(code_match.group(1))
            suggestion = {
                "action": block.get("action", "baseline_only"),
                "params": block.get("params", {}),
                "rationale": block.get("rationale", ""),
            }
        except (json.JSONDecodeError, TypeError):
            pass

    if not suggestion.get("params"):
        suggestion["params"] = {}

    return analysis, suggestion


def submit_file(file_path: Path, message: str) -> bool:
    """Submit via Kaggle Python API (avoids CLI progress bar / stderr issues)."""
    from kaggle.api.kaggle_api_extended import KaggleApi
    from requests import RequestException

    api = KaggleApi()
    api.authenticate()
    try:
        result = api.competition_submit(
            str(file_path), message, COMPETITION, quiet=True
        )
        if result == "Could not submit to competition":
            print("Submit failed: upload did not complete")
            return False
        print(f"Successfully submitted to {COMPETITION}")
        return True
    except RequestException as e:
        msg = str(e)
        if hasattr(e, "response") and e.response is not None:
            body = getattr(e.response, "text", None) or ""
            if body:
                msg = f"{msg}\nResponse: {body[:500]}"
        print(f"Submit failed (API): {msg}")
        return _submit_via_cli_fallback(file_path, message)
    except Exception as e:
        err_msg = str(e)
        print(f"Submit failed: {err_msg}")
        # 400 Bad Request etc - try CLI fallback
        if "400" in err_msg or "bad request" in err_msg.lower():
            return _submit_via_cli_fallback(file_path, message)
        return False


def _submit_via_cli_fallback(file_path: Path, message: str) -> bool:
    """Fallback: submit via kaggle CLI when API fails."""
    for venv_root in (project_root, project_root.parent):
        kaggle = venv_root / ".venv" / "Scripts" / "kaggle"
        if kaggle.exists():
            break
        kaggle = venv_root / "venv" / "Scripts" / "kaggle"
        if kaggle.exists():
            break
    else:
        return False
    r = subprocess.run(
        [str(kaggle), "competitions", "submit", "-c", COMPETITION, "-f", str(file_path), "-m", message],
        capture_output=True, text=True, cwd=str(project_root), timeout=120,
    )
    # CLI often writes progress to stderr; treat as success if stdout contains "Successfully"
    out = (r.stdout or "") + (r.stderr or "")
    if "successfully submitted" in out.lower() or "successfully" in out.lower():
        print("CLI submit succeeded.")
        return True
    if r.returncode != 0:
        print(f"CLI submit failed: {r.stderr or r.stdout or 'unknown'}")
        return False
    return True


def wait_for_score(description: str, max_wait_sec: int = 300) -> float | None:
    for _ in range(max_wait_sec // 15):
        time.sleep(15)
        subs = get_submission_scores()
        for s in subs:
            if description in s.get("description", ""):
                return s["publicScore"]
    return None


def run_one_iteration(
    baseline: dict,
    iteration: int,
    use_llm: bool = True,
) -> tuple[dict, bool]:
    """Run one full cycle. Returns (updated_baseline, improved)."""
    best_score = baseline["best_public_score"]

    from src.submission_context import get_submission_context
    ctx = get_submission_context(page_size=20)

    if not use_llm:
        # Fallback: try baseline_only if we have no attempt log, else optuna_tune
        attempt_log = ctx.get("attempt_log", [])
        if not attempt_log:
            suggestion = {"action": "baseline_only", "params": {}, "rationale": "Initial run"}
        else:
            suggestion = {"action": "optuna_tune", "params": {"n_trials": 20}, "rationale": "Hyperparameter tuning"}
        print(f"\n[Iter {iteration}] --no-llm, using: {suggestion['action']}")
    else:
        print(f"\n[Iter {iteration}] Analyzing submission history ({len(ctx['submission_history'])} submissions, {len(ctx.get('attempt_log', []))} attempts)")
        try:
            analysis, suggestion = ask_nim_for_suggestion(best_score, ctx)
            print(f"  NIM suggestion: {suggestion['action']} params={suggestion.get('params', {})}")
        except Exception as e:
            print(f"  NIM error: {e}")
            suggestion = {"action": "baseline_only", "params": {}, "rationale": "Fallback after error"}

    config_hash = _suggestion_hash(suggestion)
    attempt_log = ctx.get("attempt_log", [])
    if any(e.get("config_hash") == config_hash for e in attempt_log):
        print(f"  Skipping - exact config already tried (hash={config_hash})")
        return baseline, False

    print(f"\n[Iter {iteration}] Training: {suggestion['action']}")
    from src.train_variants import train_from_suggestion
    cv_auc, _, sub_path, error = train_from_suggestion(suggestion)

    if cv_auc is None:
        entry = {
            "action": suggestion.get("action"),
            "params": suggestion.get("params", {}),
            "rationale": suggestion.get("rationale", ""),
            "config_hash": config_hash,
            "cv_auc": None,
            "public_score": None,
            "improvement": False,
            "error": error or "Execution failed",
        }
        append_attempt_log(entry)
        print(f"  Execution failed - logged. Continuing to next iteration.")
        return baseline, False

    msg = f"Auto iter {iteration} - {suggestion['action']} CV {cv_auc:.4f}"
    if not submit_file(sub_path, msg):
        entry = {
            "action": suggestion.get("action"),
            "params": suggestion.get("params", {}),
            "rationale": suggestion.get("rationale", ""),
            "config_hash": config_hash,
            "cv_auc": cv_auc,
            "public_score": None,
            "improvement": False,
            "error": "Submit failed",
        }
        append_attempt_log(entry)
        return baseline, False

    print(f"\n[Iter {iteration}] Waiting for score (poll every 15s)...")
    score = wait_for_score(msg)
    if score is None:
        print("  Timeout - no score yet. Check manually.")
        entry = {
            "action": suggestion.get("action"),
            "params": suggestion.get("params", {}),
            "rationale": suggestion.get("rationale", ""),
            "config_hash": config_hash,
            "cv_auc": cv_auc,
            "public_score": None,
            "improvement": False,
            "error": "Score timeout",
        }
        append_attempt_log(entry)
        return baseline, False

    print(f"  Public score: {score:.5f}")
    improvement = score > best_score

    entry = {
        "action": suggestion.get("action"),
        "params": suggestion.get("params", {}),
        "rationale": suggestion.get("rationale", ""),
        "config_hash": config_hash,
        "cv_auc": cv_auc,
        "public_score": score,
        "improvement": improvement,
        "error": None,
    }
    append_attempt_log(entry)

    if improvement:
        new_baseline = {
            "best_public_score": score,
            "best_submission": sub_path.name,
            "best_description": msg,
            "updated": time.strftime("%Y-%m-%d %H:%M"),
        }
        save_baseline(new_baseline)
        print(f"  *** New baseline! {score:.5f} ***")
        return new_baseline, True

    return baseline, False


def main():
    p = argparse.ArgumentParser(description="Automated improvement loop (open-ended)")
    p.add_argument("-n", "--max-iterations", type=int, default=5, help="Max iterations")
    p.add_argument("--no-llm", action="store_true", help="Skip NIM, use fallback suggestion")
    p.add_argument("--delay", type=int, default=60, help="Seconds between submissions")
    p.add_argument("--analyze-only", action="store_true", help="Fetch context, send to NIM, print suggestion (no train/submit)")
    args = p.parse_args()

    if args.analyze_only:
        from src.submission_context import get_submission_context
        ctx = get_submission_context(page_size=20)
        baseline = load_baseline()
        print("Submission history:")
        for h in ctx["submission_history"]:
            print(f"  {h.get('fileName', '?')}: {h['publicScore']:.5f} | local={h.get('has_local')} | {(h.get('description') or '')[:50]}")
        print(f"\nAttempt log ({len(ctx.get('attempt_log', []))} entries):")
        for e in ctx.get("attempt_log", [])[-10:]:
            print(f"  {e.get('action')} -> cv={e.get('cv_auc')} pub={e.get('public_score')} improvement={e.get('improvement')} error={e.get('error')}")
        print(f"\nAsking NIM for suggestion...")
        analysis, suggestion = ask_nim_for_suggestion(baseline["best_public_score"], ctx)
        print("\n--- NIM Analysis ---")
        print(analysis)
        print(f"\nSuggested: action={suggestion['action']} params={suggestion.get('params')}")
        sys.exit(0)

    baseline = load_baseline()
    print(f"Starting auto loop. Baseline: {baseline['best_public_score']:.5f}")
    print(f"Max iterations: {args.max_iterations}, delay: {args.delay}s")

    for i in range(1, args.max_iterations + 1):
        print(f"\n{'='*80}")
        print(f"ITERATION {i}/{args.max_iterations}")
        print("="*80)

        baseline, improved = run_one_iteration(baseline, i, use_llm=not args.no_llm)

        if i < args.max_iterations:
            print(f"\nWaiting {args.delay}s before next iteration...")
            time.sleep(args.delay)

    print(f"\nDone. Final baseline: {baseline['best_public_score']:.5f}")


if __name__ == "__main__":
    main()
