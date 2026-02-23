"""Download Playground S6E2 competition data using KAGGLE_API_TOKEN from .env."""
import os
import shutil
import zipfile
from pathlib import Path

# Load .env before any kaggle imports
project_root = Path(__file__).resolve().parent.parent
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

# Use project-local cache so sandbox/restricted envs can write
os.environ.setdefault("KAGGLEHUB_CACHE", str(project_root / ".cache" / "kagglehub"))

DATA_RAW = project_root / "data" / "raw"
COMPETITION = "playground-series-s6e2"

RULES_URL = "https://www.kaggle.com/competitions/playground-series-s6e2/rules"


def _copy_from_kagglehub_path(path: Path) -> None:
    """Copy files from kagglehub cache to data/raw."""
    for f in path.rglob("*"):
        if f.is_file():
            rel = f.relative_to(path)
            dest = DATA_RAW / rel.name if rel.name == rel or len(rel.parts) == 1 else DATA_RAW / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dest)


def _fetch_fallback_data() -> None:
    """Fetch UCI heart disease data as fallback when Kaggle download fails (e.g. rules not accepted)."""
    import urllib.request
    import pandas as pd

    # UCI heart disease CSV - public URL
    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/heart-disease/processed.cleveland.data"
    cols = ["Age", "Sex", "ChestPainType", "RestingBP", "Cholesterol", "FastingBS",
            "RestingECG", "MaxHR", "ExerciseAngina", "Oldpeak", "ST_Slope", "NumVessels", "Thal", "HeartDisease"]
    df = pd.read_csv(url, header=None, names=cols)
    df["HeartDisease"] = (df["HeartDisease"] > 0).astype(int)
    df = df.drop(columns=["NumVessels", "Thal"], errors="ignore")

    # Align with Playground schema (may have slight column differences)
    train = df.sample(frac=0.8, random_state=42)
    test = df.drop(train.index).drop(columns=["HeartDisease"], errors="ignore")
    if "HeartDisease" in test.columns:
        test = test.drop(columns=["HeartDisease"])

    train.to_csv(DATA_RAW / "train.csv", index=False)
    sub = pd.DataFrame({"id": range(len(test)), "HeartDisease": 0})
    test.insert(0, "id", range(len(test)))
    test.to_csv(DATA_RAW / "test.csv", index=False)
    sub.to_csv(DATA_RAW / "sample_submission.csv", index=False)
    print("FALLBACK: Used UCI heart disease data. Accept competition rules and re-run for real data.")


def main():
    DATA_RAW.mkdir(parents=True, exist_ok=True)

    try:
        import kagglehub
        # Download to cache first (output_dir can fail if dir not empty)
        path = kagglehub.competition_download(COMPETITION)
        print(f"Downloaded to: {path}")

        src = Path(path)
        for f in src.rglob("*"):
            if f.is_file():
                shutil.copy2(f, DATA_RAW / f.name)
        # Ensure files in data/raw
        for name in ("train.csv", "test.csv", "sample_submission.csv"):
            if not (DATA_RAW / name).exists() and (src / name).exists():
                shutil.copy2(src / name, DATA_RAW / name)
        print(f"Data in: {DATA_RAW}")
    except Exception as e:
        err_msg = str(e).lower()
        if "403" in err_msg or "forbidden" in err_msg or "permission" in err_msg:
            print(f"Kaggle API error: {e}")
            print(f"\nPlease accept the competition rules at: {RULES_URL}")
            print("Then re-run this script. Using fallback UCI data for now.\n")
            _fetch_fallback_data()
            return
        raise

    # Validate
    required = ["train.csv", "test.csv", "sample_submission.csv"]
    for name in required:
        if not (DATA_RAW / name).exists():
            raise FileNotFoundError(f"Missing {name} in {DATA_RAW}")
    print("Validation OK: train.csv, test.csv, sample_submission.csv present")
