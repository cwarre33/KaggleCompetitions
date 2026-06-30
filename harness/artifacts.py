from __future__ import annotations

import json
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from omegaconf import OmegaConf


def _default_out_dir(repo_root: Path) -> Path:
    if Path("/kaggle/working").exists():
        return Path("/kaggle/working")
    # Allow override for local / other notebook runtimes
    env = os.environ.get("KAGGLE_WORKING_DIR")
    if env:
        return Path(env)
    return repo_root


def make_run_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    rand = secrets.token_hex(3)
    return f"{ts}_{rand}"


@dataclass(frozen=True)
class RunArtifacts:
    competition: str
    run_id: str
    run_dir: Path
    artifacts_dir: Path
    model_dir: Path
    oof_dir: Path
    submissions_dir: Path

    def save_metrics(self, metrics: dict[str, Any], filename: str = "metrics.json") -> Path:
        path = self.artifacts_dir / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(metrics, indent=2, sort_keys=True), encoding="utf-8")
        return path

    def save_array(self, name: str, arr: np.ndarray) -> Path:
        path = self.oof_dir / f"{name}.npy"
        path.parent.mkdir(parents=True, exist_ok=True)
        np.save(path, arr)
        return path

    def write_submission(self, df: pd.DataFrame, filename: str = "submission.csv") -> Path:
        path = self.submissions_dir / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=False)
        return path


def init_run(
    *,
    competition: str,
    repo_root: str | Path,
    out_dir: str | Path,
    config_snapshot,
    run_id: str | None = None,
) -> RunArtifacts:
    repo_root = Path(repo_root).resolve()
    run_id = run_id or make_run_id()

    out_dir_p = Path(out_dir)
    if str(out_dir_p).lower() == "auto":
        out_dir_p = _default_out_dir(repo_root)

    run_dir = out_dir_p / "runs" / competition / run_id
    artifacts_dir = run_dir / "artifacts"
    model_dir = artifacts_dir / "models"
    oof_dir = artifacts_dir / "oof"
    submissions_dir = run_dir / "submissions"

    for d in (model_dir, oof_dir, submissions_dir):
        d.mkdir(parents=True, exist_ok=True)

    # Snapshot config for reproducibility
    cfg_path = artifacts_dir / "config.yaml"
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text(OmegaConf.to_yaml(config_snapshot), encoding="utf-8")

    return RunArtifacts(
        competition=competition,
        run_id=run_id,
        run_dir=run_dir,
        artifacts_dir=artifacts_dir,
        model_dir=model_dir,
        oof_dir=oof_dir,
        submissions_dir=submissions_dir,
    )

