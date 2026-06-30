from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import lightgbm as lgb
import xgboost as xgb
from catboost import CatBoostClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import balanced_accuracy_score
from sklearn.preprocessing import LabelEncoder

from competitions._template.data import load_tabular_csvs
from competitions.playground_series_s6e6.features import build_features
from harness.artifacts import RunArtifacts, init_run
from harness.hydra_utils import compose_config

LABELS = np.array(["GALAXY", "QSO", "STAR"])  # alphabetical = LabelEncoder order

LGB_PARAMS = dict(
    objective="multiclass",
    num_class=3,
    metric="multi_logloss",
    num_leaves=511,
    n_estimators=3000,
    learning_rate=0.03,
    subsample=0.8,
    subsample_freq=1,
    colsample_bytree=0.8,
    reg_lambda=1.0,
    min_child_samples=20,
    random_state=42,
    n_jobs=-1,
    verbose=-1,
    class_weight="balanced",
)

XGB_PARAMS = dict(
    objective="multi:softprob",
    num_class=3,
    eval_metric="mlogloss",
    max_depth=7,
    n_estimators=2000,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_lambda=1.0,
    min_child_weight=5,
    random_state=42,
    n_jobs=-1,
    tree_method="hist",
    verbosity=0,
    early_stopping_rounds=100,
)

CAT_PARAMS = dict(
    iterations=3000,
    learning_rate=0.05,
    depth=8,
    loss_function="MultiClass",
    eval_metric="Accuracy",
    random_seed=42,
    verbose=500,
    auto_class_weights="Balanced",
    task_type="CPU",
    early_stopping_rounds=100,
)


def _load_sdss_extra(repo_root_p: Path) -> pd.DataFrame | None:
    sdss_path = repo_root_p / "data" / "sdss17" / "star_classification.csv"
    if not sdss_path.exists():
        print("  [extra] SDSS17 not found, skipping")
        return None
    df = pd.read_csv(sdss_path)
    df["spectral_type"] = "unknown"
    df["galaxy_population"] = "unknown"
    print(f"  [extra] SDSS17: {len(df):,} rows | {df['class'].value_counts().to_dict()}")
    return df[["alpha", "delta", "u", "g", "r", "i", "z", "redshift", "spectral_type", "galaxy_population", "class"]]


def main(*, action: str, repo_root: str, overrides: list[str] | None = None) -> int:
    repo_root_p = Path(repo_root).resolve()
    overrides = list(overrides or [])
    if not any(o.startswith("competition=") or o.startswith("+competition=") for o in overrides):
        overrides = ["competition=playground_series_s6e6", *overrides]
    cfg = compose_config(config_dir=repo_root_p / "conf", config_name="global_defaults", overrides=overrides)
    if action == "train":
        _train(cfg, repo_root_p)
        return 0
    raise ValueError(f"Unknown action: {action}")


def _train(cfg, repo_root_p: Path) -> None:
    run: RunArtifacts = init_run(
        competition=cfg.competition.slug,
        repo_root=repo_root_p,
        out_dir=cfg.paths.out_dir,
        config_snapshot=cfg,
    )

    data_dir = Path(cfg.competition.data_dir)
    if not data_dir.is_absolute():
        data_dir = repo_root_p / data_dir

    data = load_tabular_csvs(data_dir)
    df_train = data.train
    df_test = data.test

    df_extra = _load_sdss_extra(repo_root_p)

    le = LabelEncoder()
    le.fit(LABELS)
    y = le.transform(df_train[cfg.competition.target_col])

    X_comp = build_features(df_train.drop(columns=[cfg.competition.target_col, cfg.competition.id_col]))
    X_test = build_features(df_test.drop(columns=[cfg.competition.id_col]))
    feat_cols = X_comp.columns.tolist()

    # Align extra data columns
    X_extra, y_extra = None, None
    if df_extra is not None:
        X_extra = build_features(df_extra.drop(columns=["class"]))
        for col in feat_cols:
            if col not in X_extra.columns:
                X_extra[col] = 0
        X_extra = X_extra[feat_cols]
        y_extra = le.transform(df_extra["class"])

    n_folds = 5
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=42)

    # Storage: OOF + test probabilities per model
    results = {
        "lgb": {"oof": np.zeros((len(X_comp), 3)), "test": np.zeros((len(X_test), 3)), "folds": []},
        "xgb": {"oof": np.zeros((len(X_comp), 3)), "test": np.zeros((len(X_test), 3)), "folds": []},
        "cat": {"oof": np.zeros((len(X_comp), 3)), "test": np.zeros((len(X_test), 3)), "folds": []},
    }

    for fold, (tr_idx, va_idx) in enumerate(skf.split(X_comp, y)):
        X_tr, X_va = X_comp.iloc[tr_idx], X_comp.iloc[va_idx]
        y_tr, y_va = y[tr_idx], y[va_idx]

        if X_extra is not None:
            X_tr_aug = pd.concat([X_tr, X_extra], ignore_index=True)
            y_tr_aug = np.concatenate([y_tr, y_extra])
        else:
            X_tr_aug, y_tr_aug = X_tr, y_tr

        # --- LightGBM ---
        lgb_m = lgb.LGBMClassifier(**LGB_PARAMS)
        lgb_m.fit(X_tr_aug, y_tr_aug, eval_set=[(X_va, y_va)],
                  callbacks=[lgb.early_stopping(150, verbose=False), lgb.log_evaluation(1000)])
        p = lgb_m.predict_proba(X_va)
        results["lgb"]["oof"][va_idx] = p
        results["lgb"]["test"] += lgb_m.predict_proba(X_test) / n_folds
        results["lgb"]["folds"].append(balanced_accuracy_score(le.inverse_transform(y_va), le.inverse_transform(p.argmax(1))))

        # --- XGBoost ---
        xgb_m = xgb.XGBClassifier(**XGB_PARAMS)
        xgb_m.fit(X_tr_aug, y_tr_aug, eval_set=[(X_va, y_va)], verbose=False)
        p = xgb_m.predict_proba(X_va)
        results["xgb"]["oof"][va_idx] = p
        results["xgb"]["test"] += xgb_m.predict_proba(X_test) / n_folds
        results["xgb"]["folds"].append(balanced_accuracy_score(le.inverse_transform(y_va), le.inverse_transform(p.argmax(1))))

        # --- CatBoost ---
        cat_m = CatBoostClassifier(**CAT_PARAMS)
        cat_m.fit(X_tr_aug, y_tr_aug, eval_set=(X_va, y_va), use_best_model=True)
        p = cat_m.predict_proba(X_va)
        results["cat"]["oof"][va_idx] = p
        results["cat"]["test"] += cat_m.predict_proba(X_test) / n_folds
        results["cat"]["folds"].append(balanced_accuracy_score(le.inverse_transform(y_va), le.inverse_transform(p.argmax(1))))

        print(f"  Fold {fold+1}: LGB={results['lgb']['folds'][-1]:.5f}  XGB={results['xgb']['folds'][-1]:.5f}  CAT={results['cat']['folds'][-1]:.5f}")

    # OOF scores
    oof_true = le.inverse_transform(y)
    scores = {}
    for name, r in results.items():
        scores[name] = balanced_accuracy_score(oof_true, le.inverse_transform(r["oof"].argmax(1)))

    # Ensemble
    oof_ens = sum(r["oof"] for r in results.values()) / len(results)
    test_ens = sum(r["test"] for r in results.values()) / len(results)
    scores["ensemble"] = balanced_accuracy_score(oof_true, le.inverse_transform(oof_ens.argmax(1)))
    print(f"\nOOF: LGB={scores['lgb']:.5f}  XGB={scores['xgb']:.5f}  CAT={scores['cat']:.5f}  Ensemble={scores['ensemble']:.5f}")

    run.save_metrics({"oof_scores": {k: float(v) for k, v in scores.items()}})

    # Save per-model OOF + test probas (for stacker / ridge-flip corpus)
    test_ids = df_test[cfg.competition.id_col].values
    for name, r in results.items():
        _save_proba_csv(run.artifacts_dir / f"test_preds__{name}.csv", test_ids, r["test"], le)
        _save_proba_csv(run.artifacts_dir / f"oof_preds__{name}.csv", df_train[cfg.competition.id_col].values, r["oof"], le)

    # Ensemble submission
    test_labels = le.inverse_transform(test_ens.argmax(1))
    sub = pd.DataFrame({cfg.competition.id_col: test_ids, cfg.competition.target_col: test_labels})
    sub_path = run.write_submission(sub, filename="submission.csv")
    print(f"\nSubmission: {sub_path}")
    print(sub[cfg.competition.target_col].value_counts())

    # Also save ensemble probas for ridge-flip
    _save_proba_csv(run.artifacts_dir / "test_preds__ensemble.csv", test_ids, test_ens, le)


def _save_proba_csv(path: Path, ids, proba: np.ndarray, le: LabelEncoder) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(proba, columns=le.classes_)
    df.insert(0, "id", ids)
    df.to_csv(path, index=False)
