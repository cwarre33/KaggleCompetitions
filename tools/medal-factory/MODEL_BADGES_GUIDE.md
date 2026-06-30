# Model badges: Pipeline Creator, API Model Creator, Model Variation Creator

## 1. Model Pipeline Creator

**Badge:** Create a model from notebook output (train/save in a notebook, then create a model from that output on Kaggle).

**Steps:**
- Use the notebook in **model_pipeline_notebook/** (or copy its code into a new Kaggle notebook).
- Run the notebook **on Kaggle** so it writes files to `/kaggle/working/` (e.g. `model.pkl`).
- In the right-hand **Output** panel, use **“Create model from notebook output”** (or similar) to create a new model from those files.
- Badge is awarded when the model is created from the notebook output.

See **model_pipeline_notebook/README.md** for details.

---

## 2. API Model Creator

**Badge:** Create a model using the Kaggle API.

**Steps:**
- From the repo root run:  
  `python create_api_models.py`
- The script creates one model and one model instance via `kaggle models create` and `kaggle models instances create`.

**Note:** The Kaggle Models API may require early-access enablement on your account. If you get a permission or “not available” error, check [Kaggle Models](https://www.kaggle.com/models) and your account settings, or create a model and instance once via the Kaggle website.

---

## 3. Model Variation Creator

**Badge:** Create a model with multiple variations (e.g. different sizes, frameworks, or configs).

**Steps:**
- The same script **create_api_models.py** creates one model and **two** model instances (variations): `pyTorch-small` and `pyTorch-large`.
- After both instances are created, the **Model Variation Creator** badge is awarded.

So running `python create_api_models.py` once can earn both **API Model Creator** and **Model Variation Creator**.

---

## Summary

| Badge | What to do |
|-------|------------|
| **Model Pipeline Creator** | Run **model_pipeline_notebook** on Kaggle → create model from notebook output in the Output panel. |
| **API Model Creator** | Run `python create_api_models.py` (creates 1 model + 1 instance). |
| **Model Variation Creator** | Run `python create_api_models.py` (creates 1 model + 2 instances = 2 variations). |
