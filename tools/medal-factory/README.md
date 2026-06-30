# Kaggle Notebook Promotion Tool

List your Kaggle notebooks via the Kaggle API, make private ones public, and export a report with links so you can promote them and increase visibility.

## Setup

1. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

   If the CLI fails with `ImportError: cannot import name 'KaggleClient'`, also install:

   ```bash
   pip install kagglesdk
   ```

2. **Authenticate with Kaggle**

   - Go to [Kaggle Account → API](https://www.kaggle.com/settings/account) and create an API token (downloads `kaggle.json`).
   - Either:
     - Place `kaggle.json` in `~/.kaggle/` (or `%USERPROFILE%\.kaggle\` on Windows), or
     - Set env vars: `KAGGLE_USERNAME` and `KAGGLE_KEY`.

## Usage

**List all your notebooks** (default):

```bash
python kaggle_promote.py
# or
python kaggle_promote.py --list
```

**List and save a markdown report with links:**

```bash
python kaggle_promote.py --list --out my_notebooks.md
```

**Make private notebooks public:**

```bash
# See what would be changed (no push)
python kaggle_promote.py --make-public --dry-run

# Actually make private kernels public
python kaggle_promote.py --make-public
```

**List + make public + save report:**

```bash
python kaggle_promote.py --list --make-public --out report.md
```

## Options

| Option           | Description |
|------------------|-------------|
| `--list`         | List your notebooks (default if no other action). |
| `--make-public`  | Pull each kernel, set `is_private` to false, and push (only private ones are updated). |
| `--dry-run`      | With `--make-public`, only show what would be done; do not push. |
| `--out FILE`     | Write the notebook table (markdown) to FILE. |
| `--page-size N`  | Kernels per page (default 100). |
| `--max-pages N`  | Max pages to fetch (default 10). |

## Increasing visibility

See **[PROMOTION_GUIDE.md](PROMOTION_GUIDE.md)** for concrete ways to get more views, upvotes, and interaction:

- Optimizing title, description, and tags
- Sharing on Twitter, LinkedIn, Reddit, and Kaggle Discussions
- Engaging with others’ notebooks and discussions
- Timing and discoverability
- Using the generated report for portfolio and social posts

## CLI alternative

You can also use the Kaggle CLI directly:

```bash
# List your kernels (include private with -m for “mine”)
kaggle kernels list -m

# Pull a kernel (with metadata) to a folder, then edit kernel-metadata.json (is_private: false) and push
kaggle kernels pull <username>/<kernel-slug> -p ./my_kernel -m
# edit kernel-metadata.json
kaggle kernels push -p ./my_kernel
```

This script automates listing, optional make-public, and report generation in one place.
