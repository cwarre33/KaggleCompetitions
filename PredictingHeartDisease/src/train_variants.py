"""Train variants based on LLM-suggested actions."""
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score

from .config import SUBMISSIONS_DIR, TARGET_COL, N_FOLDS, RANDOM_STATE
from .data_loader import load_train, load_test
from .features import preprocess, add_features


def _train_core(
    X_processed: np.ndarray,
    X_test_processed: np.ndarray,
    y: pd.Series,
    test_ids: pd.Series,
    seeds: tuple[int, ...],
    model_type: str = "xgboost",
    model_params: dict | None = None,
    action_name: str = "baseline",
) -> tuple[float, np.ndarray, Path]:
    """Core training loop: fit model per seed, aggregate predictions."""
    model_params = model_params or {}
    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    all_test_preds = []
    all_scores = []

    for seed in seeds:
        test_preds = np.zeros((len(X_test_processed), N_FOLDS))
        for fold, (tr_idx, val_idx) in enumerate(skf.split(X_processed, y)):
            X_tr, X_val = X_processed[tr_idx], X_processed[val_idx]
            y_tr, y_val = y.iloc[tr_idx], y.iloc[val_idx]

            if model_type == "lightgbm":
                import lightgbm as lgb
                params = {"random_state": seed, "verbosity": -1, **model_params}
                model = lgb.LGBMClassifier(**params)
            else:
                import xgboost as xgb
                params = {"random_state": seed, **model_params}
                model = xgb.XGBClassifier(**params)

            model.fit(X_tr, y_tr)
            val_pred = model.predict_proba(X_val)[:, 1]
            auc = roc_auc_score(y_val, val_pred)
            all_scores.append(auc)
            test_preds[:, fold] = model.predict_proba(X_test_processed)[:, 1]

        all_test_preds.append(test_preds.mean(axis=1))

    test_final = np.mean(all_test_preds, axis=0)
    mean_auc = np.mean(all_scores)
    print(f"CV ROC AUC: {mean_auc:.4f} (+/- {np.std(all_scores):.4f})")

    SUBMISSIONS_DIR.mkdir(parents=True, exist_ok=True)
    fname = f"submission_{action_name}.csv"
    out_path = SUBMISSIONS_DIR / fname
    pd.DataFrame({"id": test_ids, TARGET_COL: test_final}).to_csv(out_path, index=False)
    print(f"Saved: {out_path}")
    return mean_auc, test_final, out_path


def train_from_suggestion(
    suggestion: dict,
) -> tuple[float | None, np.ndarray | None, Path | None, str | None]:
    """
    Execute model suggestion. Returns (cv_auc, preds, path, error).
    On success: error is None. On failure: cv_auc/preds/path are None, error is str.
    suggestion: {action: str, params: dict, rationale?: str}
    """
    action = (suggestion.get("action") or "baseline_only").strip().lower()
    params = dict(suggestion.get("params") or {})

    # Feature flags from params
    use_features = params.pop("use_features", None)
    seeds_param = params.pop("seeds", None)

    if use_features is False or action in ("remove_features", "baseline_only"):
        use_features = False
    elif use_features is True or action not in ("remove_features", "baseline_only"):
        use_features = True

    if seeds_param == "single" or action == "single_seed":
        seeds = (RANDOM_STATE,)
    elif isinstance(seeds_param, list) and len(seeds_param) > 0:
        seeds = tuple(int(s) for s in seeds_param[:5])
    else:
        seeds = (42, 123, 456)

    X, y = load_train()
    X_test, test_ids = load_test()

    if use_features:
        X = add_features(X)
        X_test = add_features(X_test)

    X_processed, encoders = preprocess(X, fit=True)
    X_test_processed, _ = preprocess(X_test, encoders=encoders, fit=False)

    # XGBoost params (filter to valid keys)
    xgb_keys = {"learning_rate", "n_estimators", "max_depth", "min_child_weight", "subsample", "colsample_bytree", "reg_alpha", "reg_lambda", "gamma"}
    model_params = {k: v for k, v in params.items() if k in xgb_keys}

    try:
        if action in ("baseline_only", "remove_features", "single_seed"):
            cv, preds, path = _train_core(
                X_processed, X_test_processed, y, test_ids,
                seeds=seeds, model_type="xgboost", model_params=model_params,
                action_name=action,
            )
            return cv, preds, path, None
        elif action == "lightgbm":
            lgb_keys = {"learning_rate", "n_estimators", "max_depth", "num_leaves", "min_child_samples", "subsample", "colsample_bytree", "reg_alpha", "reg_lambda"}
            lgb_params = {k: v for k, v in params.items() if k in lgb_keys}
            cv, preds, path = _train_core(
                X_processed, X_test_processed, y, test_ids,
                seeds=seeds, model_type="lightgbm", model_params=lgb_params,
                action_name="lightgbm",
            )
            return cv, preds, path, None
        elif action == "optuna_tune":
            n_trials = int(params.get("n_trials", 30))
            cv, preds, path = _train_optuna(
                X_processed, X_test_processed, y, test_ids,
                seeds=seeds, n_trials=n_trials, use_features=use_features,
            )
            return cv, preds, path, None
        elif action == "xgboost_tuned":
            cv, preds, path = _train_core(
                X_processed, X_test_processed, y, test_ids,
                seeds=seeds, model_type="xgboost", model_params=model_params,
                action_name="xgboost_tuned",
            )
            return cv, preds, path, None
        else:
            # Try as xgboost with params (e.g. model suggests custom action name + params)
            cv, preds, path = _train_core(
                X_processed, X_test_processed, y, test_ids,
                seeds=seeds, model_type="xgboost", model_params=model_params,
                action_name=action.replace(" ", "_")[:30],
            )
            return cv, preds, path, None
    except Exception as e:
        print(f"train_from_suggestion failed: {e}")
        return None, None, None, str(e)


def _train_optuna(
    X_processed: np.ndarray,
    X_test_processed: np.ndarray,
    y: pd.Series,
    test_ids: pd.Series,
    seeds: tuple[int, ...],
    n_trials: int = 30,
    use_features: bool = True,
) -> tuple[float, np.ndarray, Path]:
    """Optuna hyperparameter tuning for XGBoost."""
    import optuna
    from sklearn.model_selection import cross_val_score
    import xgboost as xgb

    def objective(trial):
        p = {
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3),
            "n_estimators": trial.suggest_int("n_estimators", 100, 500),
            "max_depth": trial.suggest_int("max_depth", 3, 10),
            "min_child_weight": trial.suggest_int("min_child_weight", 1, 7),
            "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
            "random_state": RANDOM_STATE,
        }
        model = xgb.XGBClassifier(**p)
        skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=RANDOM_STATE)
        scores = cross_val_score(model, X_processed, y, cv=skf, scoring="roc_auc")
        return scores.mean()

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
    best_params = {k: v for k, v in study.best_params.items() if k != "random_state"}
    best_params["random_state"] = RANDOM_STATE

    return _train_core(
        X_processed, X_test_processed, y, test_ids,
        seeds=seeds, model_type="xgboost", model_params=best_params,
        action_name="optuna_tune",
    )


def train_variant(
    action: str = "baseline_only",
    params: dict | None = None,
) -> tuple[float, np.ndarray, Path]:
    """
    Train based on action from improvement loop (backward compatible).
    action: baseline_only | remove_features | optuna_tune | single_seed
    Returns (cv_auc, test_preds, submission_path).
    """
    cv_auc, preds, path, error = train_from_suggestion({"action": action, "params": params or {}})
    if cv_auc is None:
        raise RuntimeError(f"train_variant failed for action={action}")
    return cv_auc, preds, path
