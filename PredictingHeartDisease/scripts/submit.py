"""Create submission CSV from trained model predictions."""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "baseline"
    if mode == "improved":
        from src.train_improved import train_improved
        auc, _ = train_improved(ensemble=True, multi_seed=True)
        print(f"\nSubmit: kaggle competitions submit -c playground-series-s6e2 -f submissions/submission_improved.csv -m 'Improved'")
    else:
        from src.train import train_baseline
        model = mode if mode in ("xgboost", "lightgbm") else "xgboost"
        auc, _ = train_baseline(model_type=model, save_predictions=True)
        print(f"\nSubmit: kaggle competitions submit -c playground-series-s6e2 -f submissions/submission_baseline_{model}.csv -m 'Baseline {model}'")
