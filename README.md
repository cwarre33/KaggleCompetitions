# Kaggle Competitions

A repository for all Kaggle competition code, experiments, and submissions. Each competition lives in its own subdirectory with data, notebooks, models, and submission pipelines.

## Structure

```
KaggleCompetition/
├── .venv/                    # Shared Python environment
├── PredictingHeartDisease/   # Playground S6E2 - Heart Disease
├── <CompetitionName>/        # Future competitions
└── README.md
```

## Competitions

| Competition | Directory | Status |
|-------------|-----------|--------|
| [Predicting Heart Disease](https://www.kaggle.com/competitions/playground-series-s6e2) (S6E2) | `PredictingHeartDisease/` | Active |

## Setup

1. Create and activate the shared venv:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   pip install -r requirements.txt
   ```

2. Add `kaggle.json` to `~/.kaggle/` for submissions.

3. Add `.env` with `KAGGLE_API_TOKEN` and `NIM_API_KEY` (for improvement loops).

See each competition's `README.md` for details.
