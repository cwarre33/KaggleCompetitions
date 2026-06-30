# Model usability 10 — add Base Model

If your Kaggle model has a usability score below 10 and the checklist says **Base Model** is missing, you need to mark **one of your model variations** as the **Base Model**.

## Option 1: Via Kaggle API (recommended)

1. **Pull the instance metadata** for the variation you want to make the base (e.g. the main or “small” one):

   ```bash
   kaggle models instances get <owner>/<model-slug>/<framework>/<instance-slug> -p <folder>
   ```

   Example for our badge model:

   ```bash
   kaggle models instances get cameronwarrennn/api-model-creator-badge/PyTorch/pytorch-small -p api_model_instance_v1
   ```

2. **Edit** the folder’s `model-instance-metadata.json` and set:

   ```json
   "modelInstanceType": "BaseModel"
   ```

   Allowed values: `"Unspecified"`, `"BaseModel"`, `"KaggleVariant"`, `"ExternalVariant"`.

3. **Push the update**:

   ```bash
   kaggle models instances update -p <folder>
   ```

   Example:

   ```bash
   kaggle models instances update -p api_model_instance_v1
   ```

4. Refresh your model page; usability should update (often to 10 if that was the only missing piece).

## Option 2: Via Kaggle website

On the model’s page, open **Edit** (or the edit flow for a variation). If there is a **Base model** or **Model instance type** (or similar) field, set it to **Base model** for one variation and save.

## Already done for `api-model-creator-badge` (via API)

- **pytorch-small**: `modelInstanceType` = **BaseModel**, `trainingData` set.
- **pytorch-large**: `modelInstanceType` = **KaggleVariant**, `baseModelInstance` = pytorch-small, `trainingData` set.

Provenance cannot be set via the current CLI (client bug). To aim for usability 10, complete any remaining items on the **model Edit page** on Kaggle (provenance, tags, linked notebook). See **MODEL_USABILITY_FULL_10.md** for the full checklist.
