# Kaggle Playground S6E2 - Heart Disease Prediction

Competition: [Predicting Heart Disease](https://www.kaggle.com/competitions/playground-series-s6e2)  
Metric: ROC AUC Score

## Setup

1. **Environment** (use parent `.venv` if KaggleCompetition has one, or create here)
   ```bash
   # From KaggleCompetition root:
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   pip install -r requirements.txt

   # Run from PredictingHeartDisease:
   cd PredictingHeartDisease
   ..\.venv\Scripts\python scripts/run_auto_loop.py -n 5
   ```

2. **Kaggle API**  
   Set `KAGGLE_API_TOKEN` in `.env` (from Kaggle Settings → Create New Token).

3. **Download data**
   ```bash
   python scripts/download_data.py
   ```
   Accept competition rules at [Kaggle](https://www.kaggle.com/competitions/playground-series-s6e2/rules) if you get 403.

## Usage

- **Baseline**: `python scripts/submit.py` or `python scripts/submit.py xgboost`
- **Improved** (ensemble + multi-seed): `python scripts/run_improved.py`
- **Optuna tuning**: `python scripts/tune_optuna.py`

## Submit to Kaggle

**Important:** Use the venv's `kaggle` executable. Running plain `kaggle` can hit the system Python's broken kagglesdk.

```bash
.venv\Scripts\kaggle competitions submit -c playground-series-s6e2 -f submissions/submission_baseline_xgboost.csv -m "Baseline"
```

**Auth:** The submit command needs `kaggle.json` at `C:\Users\cameronwarren\.kaggle\kaggle.json`:
1. Kaggle → Settings → API → Create New Token (downloads `kaggle.json`)
2. Place it in `C:\Users\cameronwarren\.kaggle\`

`KAGGLE_API_TOKEN` in `.env` is for kagglehub (downloads only); submissions use `kaggle.json`.

## Improvement loop (NIM LLM)

Uses NVIDIA NIM API to analyze why submissions underperform and suggest changes.

**Automated loop** (recommended):
```bash
python scripts/run_auto_loop.py -n 5
```
Runs up to 5 iterations: analyze → train → submit → wait for score → update baseline → repeat. Use `--delay 120` between submissions to respect Kaggle rate limits.

**Manual:**
1. Fetch scores: `python scripts/get_submission_scores.py`
2. Run analysis: `python scripts/improvement_loop.py`
3. Train + submit: `python scripts/improvement_loop.py --submit`

Add `NIM_API_KEY` to `.env` (from [build.nvidia.com](https://build.nvidia.com/) → Get API Key).

## Project structure

- `data/raw/` - Competition CSVs
- `src/` - Config, data loader, features, train pipelines, NIM client
- `notebooks/01_eda.ipynb` - EDA and baseline
- `submissions/` - Submission files
- `research/` - PLAN.md, baseline.json (best score tracking)
