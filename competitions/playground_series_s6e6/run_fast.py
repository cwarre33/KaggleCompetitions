"""Fast LightGBM-only run with improved features + SDSS17 extra data."""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import balanced_accuracy_score
from sklearn.preprocessing import LabelEncoder

from competitions._template.data import load_tabular_csvs
from competitions.playground_series_s6e6.features import build_features
from harness.artifacts import RunArtifacts, init_run
from harness.hydra_utils import compose_config

LABELS = np.array(["GALAXY", "QSO", "STAR"])

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


def main(repo_root: str = ".") -> None:
    repo_root_p = Path(repo_root).resolve()
    cfg = compose_config(
        config_dir=repo_root_p / "conf",
        config_name="global_defaults",
        overrides=["competition=playground_series_s6e6"],
    )
    run: RunArtifacts = init_run(
        competition=cfg.competition.slug,
        repo_root=repo_root_p,
        out_dir=cfg.paths.out_dir,
        config_snapshot=cfg,
    )

    data_dir = repo_root_p / cfg.competition.data_dir
    data = load_tabular_csvs(data_dir)
    df_train, df_test = data.train, data.test

    # Extra data
    sdss_path = repo_root_p / "data" / "sdss17" / "star_classification.csv"
    df_extra = None
    if sdss_path.exists():
        df_extra = pd.read_csv(sdss_path)
        df_extra["spectral_type"] = "unknown"
        df_extra["galaxy_population"] = "unknown"
        df_extra = df_extra[["alpha","delta","u","g","r","i","z","redshift","spectral_type","galaxy_population","class"]]
        print(f"  [extra] SDSS17: {len(df_extra):,} rows")

    le = LabelEncoder()
    le.fit(LABELS)
    y = le.transform(df_train["class"])

    X_comp = build_features(df_train.drop(columns=["class", "id"]))
    X_test = build_features(df_test.drop(columns=["id"]))
    feat_cols = X_comp.columns.tolist()
    print(f"  Features: {len(feat_cols)}")

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
    oof = np.zeros((len(X_comp), 3))
    test_proba = np.zeros((len(X_test), 3))
    fold_scores = []

    for fold, (tr_idx, va_idx) in enumerate(skf.split(X_comp, y)):
        X_tr, X_va = X_comp.iloc[tr_idx], X_comp.iloc[va_idx]
        y_tr, y_va = y[tr_idx], y[va_idx]
        if X_extra is not None:
            X_tr = pd.concat([X_tr, X_extra], ignore_index=True)
            y_tr = np.concatenate([y_tr, y_extra])

        model = lgb.LGBMClassifier(**LGB_PARAMS)
        model.fit(X_tr, y_tr, eval_set=[(X_va, y_va)],
                  callbacks=[lgb.early_stopping(150, verbose=False), lgb.log_evaluation(500)])

        p = model.predict_proba(X_va)
        oof[va_idx] = p
        test_proba += model.predict_proba(X_test) / n_folds
        score = balanced_accuracy_score(le.inverse_transform(y_va), le.inverse_transform(p.argmax(1)))
        fold_scores.append(score)
        print(f"  Fold {fold+1}: bal_acc={score:.5f}")

    oof_score = balanced_accuracy_score(le.inverse_transform(y), le.inverse_transform(oof.argmax(1)))
    print(f"\nOOF balanced_accuracy: {oof_score:.5f}")
    print(f"Mean fold:             {np.mean(fold_scores):.5f} ± {np.std(fold_scores):.5f}")

    run.save_metrics({"oof_balanced_accuracy": oof_score, "fold_scores": [float(s) for s in fold_scores]})

    test_ids = df_test["id"].values
    # Save proba CSV for ridge-flip corpus
    proba_df = pd.DataFrame(test_proba, columns=le.classes_)
    proba_df.insert(0, "id", test_ids)
    proba_df.to_csv(run.artifacts_dir / "test_preds__lgb_v2.csv", index=False)

    test_labels = le.inverse_transform(test_proba.argmax(1))
    sub = pd.DataFrame({"id": test_ids, "class": test_labels})
    sub_path = run.write_submission(sub, filename="submission.csv")
    print(f"\nSubmission: {sub_path}")
    print(sub["class"].value_counts())
    return str(sub_path)


if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
