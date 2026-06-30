# Dataset Documenter badge — usability 10

Earn the **Dataset Documenter** badge by creating a dataset with a **perfect usability rating of 10**.

## What counts toward usability

Kaggle’s usability score is based on **completeness**, **credibility**, and **compatibility**:

| Area | What to provide |
|------|------------------|
| **Completeness** | Subtitle, tags/keywords, description, **cover image** |
| **Credibility** | **Source/provenance**, **public notebook** (optional), **update frequency** |
| **Compatibility** | **License**, **file format** (e.g. CSV), **file description**, **column descriptions** (for tabular data) |

## Option 1: Create the pre-filled dataset via API

From the repo root:

```bash
python create_documenter_dataset.py
```

This uploads **documenter_dataset/** with:

- **Title** and **subtitle** (20–80 chars)
- **Description** (overview, contents, usage, provenance)
- **Keywords** (e.g. tabular, tutorial, beginner)
- **License** (CC0-1.0)
- **File description** for `sample_data.csv`
- **Column descriptions** for `id`, `value`, `label` (via `schema.fields`)

Then on Kaggle:

1. Open your new dataset (link printed by the script).
2. **Edit dataset** and add anything still missing for a 10:
   - **Cover image** — required for full completeness (upload an image).
   - **Source / provenance** — e.g. “Synthetic data for badge documentation.”
   - **Update frequency** — e.g. “As needed” or “Never.”
3. Save. When the usability score reaches 10, the badge is awarded.

## Option 2: Bring an existing dataset to 10

If you already have a dataset, edit it on Kaggle and ensure:

- **Subtitle** (short line under the title, 20–80 chars).
- **Description** — clear overview, what’s in the data, how to use it.
- **Tags** — several relevant tags (e.g. tabular, tutorial).
- **License** — one license selected.
- **Cover image** — any clear image that represents the dataset.
- **Source** — where the data comes from (or “Synthetic” / “Generated for X”).
- **Update frequency** — how often it’s updated (e.g. “Never”, “As needed”).
- For each **file**: short description; for **tabular files**, **column descriptions** for every column.

## Checklist (quick reference)

- [ ] Title (6–50 chars)
- [ ] Subtitle (20–80 chars)
- [ ] Description (several sentences)
- [ ] Tags / keywords (multiple)
- [ ] License
- [ ] Cover image
- [ ] Source / provenance
- [ ] Update frequency
- [ ] File description(s)
- [ ] Column descriptions for all tabular columns

After your dataset shows **usability 10**, the **Dataset Documenter** badge will appear on your [accomplishments](https://www.kaggle.com/accomplishments) page.
