"""Project configuration - paths, constants, competition settings."""
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Data paths
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
SUBMISSIONS_DIR = PROJECT_ROOT / "submissions"
RESEARCH_DIR = PROJECT_ROOT / "research"
ATTEMPT_LOG = RESEARCH_DIR / "attempt_log.jsonl"

# Competition
COMPETITION_NAME = "playground-series-s6e2"
TARGET_COL = "Heart Disease"  # Actual column name in S6E2 data
METRIC = "roc_auc"

# Model defaults
RANDOM_STATE = 42
N_FOLDS = 5
