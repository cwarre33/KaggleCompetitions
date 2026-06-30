# API Notebook Creator badge

This folder is used to **push a notebook to Kaggle via the Kaggle API** so you can earn the [API Notebook Creator](https://www.kaggle.com/progression/badges) badge.

## One-time setup

1. **Install the Kaggle API**
   ```bash
   pip install kaggle
   ```

2. **Get your API credentials**
   - Go to [Kaggle → Account → API](https://www.kaggle.com/settings)
   - Click **Create Legacy API Key** (downloads `kaggle.json`)

3. **Place `kaggle.json`**
   - **Windows:** `C:\Users\<You>\.kaggle\kaggle.json`
   - **Mac/Linux:** `~/.kaggle/kaggle.json`

## Push the notebook (earn the badge)

From the **repo root** (KaggleMedalFactory), run:

```bash
python push_api_notebook.py
```

Or with the CLI directly (replace `YOUR_USERNAME` in `kernel-metadata.json` first):

```bash
kaggle kernels push -p api_notebook
```

After a successful push, the badge should appear on your [Kaggle accomplishments](https://www.kaggle.com/accomplishments) page.
