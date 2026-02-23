"""Load and validate competition data."""
import pandas as pd
from pathlib import Path

from .config import DATA_RAW, TARGET_COL


def load_train() -> tuple[pd.DataFrame, pd.Series]:
    """Load training data. Returns (X, y) with y as 0/1."""
    df = pd.read_csv(DATA_RAW / "train.csv")
    y = df[TARGET_COL].map({"Absence": 0, "Presence": 1})
    X = df.drop(columns=[TARGET_COL, "id"], errors="ignore")
    return X, y


def load_test() -> pd.DataFrame:
    """Load test data."""
    df = pd.read_csv(DATA_RAW / "test.csv")
    ids = df["id"].copy()
    X = df.drop(columns=["id"], errors="ignore")
    return X, ids


def load_sample_submission() -> pd.DataFrame:
    """Load sample submission format."""
    return pd.read_csv(DATA_RAW / "sample_submission.csv")
