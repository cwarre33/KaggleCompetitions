from __future__ import annotations

from pathlib import Path

import hydra
from omegaconf import DictConfig


def compose_config(
    *,
    config_dir: str | Path,
    config_name: str,
    overrides: list[str] | None = None,
) -> DictConfig:
    """
    Compose a Hydra config from an explicit config directory.

    This works well in Kaggle notebooks where the working directory can vary;
    callers should pass a resolved `config_dir` (typically `<repo_root>/conf`).
    """
    config_dir = Path(config_dir).resolve()
    overrides = overrides or []
    with hydra.initialize_config_dir(version_base=None, config_dir=str(config_dir)):
        return hydra.compose(config_name=config_name, overrides=overrides)

