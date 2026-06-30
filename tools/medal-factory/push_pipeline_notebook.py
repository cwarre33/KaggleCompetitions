#!/usr/bin/env python3
"""
Push the pipeline_notebook to Kaggle so you can run it there and then
create a dataset from its output (earns "Dataset Pipeline Creator" badge).

Run from repo root:
  python push_pipeline_notebook.py
Then on Kaggle: open the notebook → Run All → right panel → Create dataset from notebook output.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
PIPELINE_DIR = REPO_ROOT / "pipeline_notebook"
KERNEL_METADATA = PIPELINE_DIR / "kernel-metadata.json"
PLACEHOLDER = "YOUR_KAGGLE_USERNAME"


def get_kaggle_username():
    username = os.environ.get("KAGGLE_USERNAME")
    if username:
        return username
    home = Path.home()
    kaggle_json = home / ".kaggle" / "kaggle.json"
    if kaggle_json.is_file():
        try:
            data = json.loads(kaggle_json.read_text(encoding="utf-8"))
            return data.get("username")
        except (json.JSONDecodeError, KeyError):
            pass
    return None


def main():
    if not PIPELINE_DIR.is_dir() or not KERNEL_METADATA.is_file():
        print("Error: pipeline_notebook/ and kernel-metadata.json must exist.", file=sys.stderr)
        sys.exit(1)

    username = get_kaggle_username()
    if not username:
        print("Kaggle username not found. Place kaggle.json in %USERPROFILE%\\.kaggle\\ or set KAGGLE_USERNAME.", file=sys.stderr)
        sys.exit(1)

    meta = json.loads(KERNEL_METADATA.read_text(encoding="utf-8"))
    if PLACEHOLDER in meta.get("id", ""):
        meta["id"] = meta["id"].replace(PLACEHOLDER, username)
        KERNEL_METADATA.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        print(f"Using Kaggle username: {username}")

    print("Pushing pipeline notebook to Kaggle...")
    result = subprocess.run(
        ["kaggle", "kernels", "push", "-p", str(PIPELINE_DIR)],
        cwd=REPO_ROOT,
        shell=(os.name == "nt"),
    )
    if result.returncode != 0:
        sys.exit(result.returncode)
    print("Done. Open the notebook on Kaggle → Run All → then use 'Create dataset from notebook output' in the right panel to earn the badge.")


if __name__ == "__main__":
    main()
