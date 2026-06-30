from __future__ import annotations

from pathlib import Path

import joblib


def save_model_joblib(model, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
    return path


def load_model_joblib(path: str | Path):
    return joblib.load(Path(path))

