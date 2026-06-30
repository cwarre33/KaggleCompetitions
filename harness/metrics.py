from __future__ import annotations

import numpy as np
from sklearn.metrics import roc_auc_score, mean_squared_error


def score_metric(*, metric: str, y_true, y_pred) -> float:
    metric = (metric or "").lower()
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    if metric in {"roc_auc", "auc"}:
        return float(roc_auc_score(y_true, y_pred))
    if metric in {"rmse"}:
        return float(np.sqrt(mean_squared_error(y_true, y_pred)))

    raise ValueError(f"Unsupported metric: {metric}")

