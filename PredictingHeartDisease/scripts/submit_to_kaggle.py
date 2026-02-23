"""Submit a file to Kaggle competition using the venv's Kaggle API."""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Load .env for KAGGLE_API_TOKEN
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

def main():
    file_path = sys.argv[1] if len(sys.argv) > 1 else str(project_root / "submissions" / "submission_baseline_xgboost.csv")
    message = sys.argv[2] if len(sys.argv) > 2 else "Baseline"
    competition = "playground-series-s6e2"

    path = Path(file_path)
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(1)

    from kaggle.api.kaggle_api_extended import KaggleApi
    api = KaggleApi()
    api.authenticate()
    result = api.competition_submit(str(path), message, competition)
    print(result)

if __name__ == "__main__":
    main()
