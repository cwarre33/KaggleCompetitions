"""Improved training: feature engineering, Optuna tuning, ensemble, multi-seed averaging."""
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score

from .config import SUBMISSIONS_DIR, TARGET_COL, N_FOLDS, RANDOM_STATE
from .data_loader import load_train, load_test
from .features import preprocess, add_features


def train_improved(
    ensemble: bool = True,
    multi_seed: bool = True,
    seeds: tuple[int, ...] = (42, 123, 456),
) -> tuple[float, np.ndarray]:
    """
    Train improved model with ensemble and multi-seed averaging.
    Returns (mean_cv_auc, test_predictions).
    """
    X, y = load_train()
    X_test, test_ids = load_test()

    X = add_features(X)
    X_test = add_features(X_test)

    X_processed, encoders = preprocess(X, fit=True)
    X_test_processed, _ = preprocess(X_test, encoders=encoders, fit=False)

    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    all_test_preds = []
    all_scores = []

    for seed in (seeds if multi_seed else (RANDOM_STATE,)):
        oof_preds = np.zeros(len(X))
        test_preds = np.zeros((len(X_test), N_FOLDS))

        for fold, (tr_idx, val_idx) in enumerate(skf.split(X_processed, y)):
            X_tr, X_val = X_processed[tr_idx], X_processed[val_idx]
            y_tr, y_val = y.iloc[tr_idx], y.iloc[val_idx]

            if ensemble:
                import xgboost as xgb
                m1 = xgb.XGBClassifier(random_state=seed)
                m1.fit(X_tr, y_tr)
                try:
                    import lightgbm as lgb
                    m2 = lgb.LGBMClassifier(random_state=seed, verbose=-1)
                    m2.fit(X_tr, y_tr)
                    val_pred = (m1.predict_proba(X_val)[:, 1] + m2.predict_proba(X_val)[:, 1]) / 2
                    test_preds[:, fold] = (
                        m1.predict_proba(X_test_processed)[:, 1] + m2.predict_proba(X_test_processed)[:, 1]
                    ) / 2
                except ImportError:
                    val_pred = m1.predict_proba(X_val)[:, 1]
                    test_preds[:, fold] = m1.predict_proba(X_test_processed)[:, 1]
            else:
                import xgboost as xgb
                model = xgb.XGBClassifier(random_state=seed)
                model.fit(X_tr, y_tr)
                val_pred = model.predict_proba(X_val)[:, 1]
                test_preds[:, fold] = model.predict_proba(X_test_processed)[:, 1]

            oof_preds[val_idx] = val_pred
            auc = roc_auc_score(y_val, val_pred)
            all_scores.append(auc)

        all_test_preds.append(test_preds.mean(axis=1))

    test_final = np.mean(all_test_preds, axis=0)
    mean_auc = np.mean(all_scores)
    print(f"CV ROC AUC: {mean_auc:.4f} (+/- {np.std(all_scores):.4f})")

    SUBMISSIONS_DIR.mkdir(parents=True, exist_ok=True)
    sub = pd.DataFrame({"id": test_ids, TARGET_COL: test_final})
    out_path = SUBMISSIONS_DIR / "submission_improved.csv"
    sub.to_csv(out_path, index=False)
    print(f"Saved: {out_path}")

    return mean_auc, test_final
