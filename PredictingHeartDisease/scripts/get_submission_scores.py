"""Fetch submission history and public scores from Kaggle API."""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

COMPETITION = "playground-series-s6e2"


def _get_attr(obj, *names, default=None):
    for n in names:
        v = getattr(obj, n, None)
        if v is not None:
            return v
    return default


def get_submissions(page_size: int = 20):
    """Fetch submission list with public/private scores."""
    from kaggle.api.kaggle_api_extended import KaggleApi
    api = KaggleApi()
    api.authenticate()
    subs = api.competition_submissions(COMPETITION, page_size=page_size)
    return subs


def get_submission_scores(page_size: int = 10) -> list[dict]:
    """Return list of {fileName, description, publicScore} for completed submissions."""
    subs = get_submissions(page_size)
    results = []
    for s in subs:
        pub = _get_attr(s, "publicScore", "public_score")
        desc = _get_attr(s, "description", "fileName", default="") or ""
        fname = _get_attr(s, "fileName", "file_name", default="") or ""
        status = _get_attr(s, "status", default="")
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


def main():
    subs = get_submissions()
    print(f"Competition: {COMPETITION}")
    print("-" * 60)
    for i, s in enumerate(subs):
        desc = _get_attr(s, "description", "fileName", default="") or ""
        pub = _get_attr(s, "publicScore", "public_score")
        priv = _get_attr(s, "privateScore", "private_score")
        status = _get_attr(s, "status", default="")
        date = _get_attr(s, "date", default="")
        print(f"{i+1}. {str(desc)[:50]} | public={pub} | private={priv} | status={status} | {date}")
    if not subs:
        print("No submissions found.")
    return subs


if __name__ == "__main__":
    main()
