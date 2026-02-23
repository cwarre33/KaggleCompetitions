"""Training pipeline with stratified K-Fold CV and ROC AUC."""
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score

from .config import DATA_RAW, SUBMISSIONS_DIR, TARGET_COL, N_FOLDS, RANDOM_STATE
from .data_loader import load_train, load_test
from .features import preprocess


def train_baseline(
    model_type: str = "xgboost",
    n_folds: int = N_FOLDS,
    save_predictions: bool = True,
) -> tuple[float, np.ndarray]:
    """
    Train baseline model with stratified K-Fold CV.
    Returns (mean_cv_auc, oof_predictions).
    """
    X, y = load_train()
    X_test, test_ids = load_test()

    X_processed, encoders = preprocess(X, fit=True)
    X_test_processed, _ = preprocess(X_test, encoders=encoders, fit=False)

    if model_type == "xgboost":
        import xgboost as xgb
        model_cls = xgb.XGBClassifier
        params = {"random_state": RANDOM_STATE}
    else:
        import lightgbm as lgb
        model_cls = lgb.LGBMClassifier
        params = {"random_state": RANDOM_STATE, "verbose": -1}

    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=RANDOM_STATE)
    oof_preds = np.zeros(len(X))
    test_preds = np.zeros((len(X_test), n_folds))
    scores = []

    for fold, (tr_idx, val_idx) in enumerate(skf.split(X_processed, y)):
        X_tr, X_val = X_processed[tr_idx], X_processed[val_idx]
        y_tr, y_val = y.iloc[tr_idx], y.iloc[val_idx]

        model = model_cls(**params)
        model.fit(X_tr, y_tr)
        val_pred = model.predict_proba(X_val)[:, 1]
        oof_preds[val_idx] = val_pred
        auc = roc_auc_score(y_val, val_pred)
        scores.append(auc)
        test_preds[:, fold] = model.predict_proba(X_test_processed)[:, 1]

    mean_auc = np.mean(scores)
    print(f"CV ROC AUC: {mean_auc:.4f} (+/- {np.std(scores):.4f})")
    test_pred_final = test_preds.mean(axis=1)

    if save_predictions:
        SUBMISSIONS_DIR.mkdir(parents=True, exist_ok=True)
        sub = pd.DataFrame({"id": test_ids, TARGET_COL: test_pred_final})
        out_path = SUBMISSIONS_DIR / f"submission_baseline_{model_type}.csv"
        sub.to_csv(out_path, index=False)
        print(f"Saved: {out_path}")

    return mean_auc, test_pred_final
