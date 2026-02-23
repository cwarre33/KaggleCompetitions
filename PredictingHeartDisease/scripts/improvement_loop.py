"""
Improvement loop: use NIM LLM to analyze results, suggest changes, train, submit, check score.
If new score > baseline, update baseline.
"""
import json
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
SUBMISSIONS_DIR = project_root / "submissions"

_last_action = "baseline_only"  # Set by LLM analysis for next --submit run


def load_baseline() -> dict:
    if BASELINE_FILE.exists():
        return json.loads(BASELINE_FILE.read_text())
    return {"best_public_score": 0.0, "best_submission": "", "best_description": ""}


def save_baseline(data: dict):
    BASELINE_FILE.parent.mkdir(parents=True, exist_ok=True)
    BASELINE_FILE.write_text(json.dumps(data, indent=2))


def get_submission_scores():
    """Fetch latest submissions and their public scores."""
    from kaggle.api.kaggle_api_extended import KaggleApi
    api = KaggleApi()
    api.authenticate()
    subs = api.competition_submissions(COMPETITION, page_size=10)
    results = []
    for s in subs:
        pub = getattr(s, "publicScore", None) or getattr(s, "public_score", None)
        desc = getattr(s, "description", None) or ""
        status = getattr(s, "status", "")
        if pub is not None and "complete" in str(status).lower():
            try:
                results.append({"description": str(desc), "publicScore": float(pub)})
            except (TypeError, ValueError):
                pass
    return results


def ask_nim_for_analysis(baseline_score: float, improved_score: float, context: str) -> str:
    """Use NIM LLM to analyze why improved scored worse and suggest changes."""
    from src.nim_client import chat

    prompt = f"""You are a Kaggle competition expert. Analyze this situation:

**Competition:** Playground S6E2 - Predicting Heart Disease (binary classification, ROC AUC metric)

**Results:**
- Baseline (simple XGBoost, no extra features): public score {baseline_score:.5f}
- Improved (added interaction features MaxHR_per_Age, Chol_BP; multi-seed XGBoost): public score {improved_score:.5f}

The "improved" model scored LOWER than the baseline. This suggests:
1. The added features may cause overfitting to the training/CV fold
2. The interaction terms may not generalize to the test set
3. Multi-seed averaging without LightGBM (LightGBM not installed) might dilute signal

**Current code approach:**
- Baseline: XGBoost default params, 5-fold stratified CV, no feature engineering
- Improved: Same + add_features (MaxHR_per_Age = Max HR / (Age+1), Chol_BP = Cholesterol * BP), 3 seeds

**Your task:** In 2-4 short paragraphs:
1. Why did the improved model likely score worse?
2. What should we try next? Be specific: e.g. "remove the interaction features", "try Optuna tuning on baseline", "add target encoding with CV", "try different seeds", etc.
3. Output a JSON block at the end with exactly: {{"action": "one of: baseline_only | remove_features | optuna_tune | add_target_encoding | try_lightgbm | other", "params": {{}}}}
"""
    return chat(prompt)


def submit_file(file_path: Path, message: str) -> bool:
    """Submit via kaggle CLI. Returns True on success."""
    kaggle = project_root / ".venv" / "Scripts" / "kaggle"
    if not kaggle.exists():
        kaggle = Path(".venv/Scripts/kaggle")
    cmd = [
        str(kaggle),
        "competitions", "submit",
        "-c", COMPETITION,
        "-f", str(file_path),
        "-m", message,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(project_root))
    if r.returncode != 0:
        print(f"Submit failed: {r.stderr}")
        return False
    print(r.stdout)
    return True


def wait_for_score(description: str, max_wait_sec: int = 300) -> float | None:
    """Poll for new submission score. Returns publicScore when complete."""
    for _ in range(max_wait_sec // 15):
        time.sleep(15)
        subs = get_submission_scores()
        for s in subs:
            if description in s.get("description", ""):
                return s["publicScore"]
    return None


def run_improvement_loop(
    use_llm: bool = True,
    auto_submit: bool = False,
    max_iterations: int = 1,
):
    """Run one iteration of the improvement loop."""
    global _last_action
    baseline = load_baseline()
    best_score = baseline["best_public_score"]
    print(f"Current baseline: {best_score:.5f} ({baseline.get('best_description', '')})")

    # Fetch latest scores
    subs = get_submission_scores()
    print("\nRecent submissions:")
    for s in subs[:5]:
        print(f"  {s['description'][:40]}: {s['publicScore']}")

    if use_llm and subs:
        # Find a submission that scored worse than baseline (e.g. "Improved ensemble")
        worse_sub = next((s for s in subs if s["publicScore"] < best_score), None)
        if worse_sub:
            improved_score = worse_sub["publicScore"]
            worse_desc = worse_sub["description"]
            print(f"\n{worse_desc} ({improved_score:.5f}) < Baseline ({best_score:.5f}). Asking NIM for analysis...")
            try:
                analysis = ask_nim_for_analysis(best_score, improved_score, "")
                print("\n--- NIM Analysis ---")
                print(analysis)
                # Try to parse JSON action for next iteration
                if "{" in analysis and "}" in analysis:
                    start = analysis.rfind("{")
                    end = analysis.rfind("}") + 1
                    try:
                        action_block = json.loads(analysis[start:end])
                        _last_action = action_block.get("action", "baseline_only")
                        print(f"\nParsed action for next run: {_last_action}")
                    except (json.JSONDecodeError, TypeError):
                        _last_action = "baseline_only"
            except Exception as e:
                print(f"NIM API error: {e}. Set NIM_API_KEY in .env")

    if auto_submit:
        # Train based on last parsed action, or baseline
        action = _last_action
        print(f"\nTraining variant: {action}...")
        from src.train_variants import train_variant
        cv_auc, _, sub_path = train_variant(action=action)
        msg = f"Improvement loop - {action} CV {cv_auc:.4f}"
        if submit_file(sub_path, msg):
            print("Submitted. Wait ~1-2 min then run: python scripts/improvement_loop.py --scores-only")
            score = wait_for_score(msg)
            if score is not None and score > best_score:
                save_baseline({
                    "best_public_score": score,
                    "best_submission": sub_path.name,
                    "best_description": msg,
                    "updated": time.strftime("%Y-%m-%d"),
                })
                print(f"New baseline! {score:.5f}")

    return baseline


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--no-llm", action="store_true", help="Skip NIM analysis")
    p.add_argument("--submit", action="store_true", help="Train and submit after analysis")
    p.add_argument("--scores-only", action="store_true", help="Just fetch and print scores")
    args = p.parse_args()

    if args.scores_only:
        subs = get_submission_scores()
        for s in subs:
            print(f"{s['description'][:50]}: {s['publicScore']}")
        sys.exit(0)

    run_improvement_loop(use_llm=not args.no_llm, auto_submit=args.submit)
