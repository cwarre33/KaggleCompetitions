# Get model usability to 10 (still at 9.33)

These updates were applied via the API:

- **Base model:** `pytorch-small` is set to **BaseModel**.
- **Variant link:** `pytorch-large` is set to **KaggleVariant** with base = `pytorch-small`.
- **Training data:** Both variations have a short `trainingData` entry.

**Provenance** could not be set via the CLI (client bug with field names). You need to finish the last bits on the **Kaggle website**.

## Do this on the model page

1. Open: **https://www.kaggle.com/models/cameronwarrennn/api-model-creator-badge**
2. Click **Edit** (or the ⋮ menu → Edit).
3. Fill in anything the page still asks for for usability. Often:
   - **Provenance / source** — e.g. “Created via Kaggle API for badge documentation.”
   - **Tags / task** — e.g. add a task tag if there’s a tag selector.
   - **Subtitle** — already set via API; confirm it’s there.
   - **Description (model card)** — already set; confirm it’s there.
4. For **each variation** (pytorch-small, pytorch-large), open its **Edit** and ensure:
   - **Overview** and **Usage** (with example code) are filled.
   - **License** is set.
5. **Publish a notebook** that uses this model and link it from the model page (or save a version with the model attached). Docs say this can help.
6. Save and refresh; check the **usability** score again.

## If the page shows a usability checklist

Use the checklist on the model (or variation) edit page. It will list exactly what’s missing (e.g. “Base model”, “Provenance”, “Tags”, “Notebook”). Fill every item it shows until the score reaches 10.

## If it’s a different model at 9.33

If the model at 9.33 is **not** `api-model-creator-badge` (e.g. another model you created from a notebook), then:

1. Open **that** model’s page.
2. Click **Edit** and look for the usability section or checklist.
3. For **Base model**: pick one variation, edit it, and set **Model instance type** (or equivalent) to **Base model**.
4. Fill any other missing fields the checklist or form shows (provenance, tags, usage, notebook, etc.).

The exact fields depend on what Kaggle shows on the edit screen; the checklist is the source of truth for what’s missing.
