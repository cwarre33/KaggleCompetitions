"""Run improved model (ensemble + multi-seed)."""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.train_improved import train_improved

if __name__ == "__main__":
    auc, _ = train_improved(ensemble=True, multi_seed=True)
    print(f"\nSubmit: kaggle competitions submit -c playground-series-s6e2 -f submissions/submission_improved.csv -m 'Improved ensemble'")
