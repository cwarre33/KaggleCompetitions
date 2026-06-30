#!/usr/bin/env python3
"""
Push the api_notebook folder to Kaggle using the Kaggle API.
This earns you the "API Notebook Creator" badge.

Prerequisites:
  1. pip install kaggle
  2. Kaggle API credentials:
     - Download kaggle.json from https://www.kaggle.com/settings (Create Legacy API Key)
     - Place at %USERPROFILE%\\.kaggle\\kaggle.json (Windows) or ~/.kaggle/kaggle.json (Mac/Linux)

Run from repo root:
  python push_api_notebook.py
"""

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
API_NOTEBOOK_DIR = REPO_ROOT / "api_notebook"
KERNEL_METADATA = API_NOTEBOOK_DIR / "kernel-metadata.json"
PLACEHOLDER = "YOUR_KAGGLE_USERNAME"


def get_kaggle_username():
    """Get username from kaggle.json or KAGGLE_USERNAME env."""
    username = os.environ.get("KAGGLE_USERNAME")
    if username:
        return username
    # Windows: %USERPROFILE%\.kaggle\kaggle.json
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
    if not API_NOTEBOOK_DIR.is_dir() or not KERNEL_METADATA.is_file():
        print("Error: api_notebook/ and kernel-metadata.json must exist.", file=sys.stderr)
        sys.exit(1)

    username = get_kaggle_username()
    if not username:
        print(
            "Kaggle username not found. Either:\n"
            "  1) Place kaggle.json in %USERPROFILE%\\.kaggle\\ (with a 'username' key), or\n"
            "  2) Set KAGGLE_USERNAME in the environment, or\n"
            "  3) Edit api_notebook/kernel-metadata.json and replace YOUR_KAGGLE_USERNAME with your Kaggle username.",
            file=sys.stderr,
        )
        sys.exit(1)

    meta = json.loads(KERNEL_METADATA.read_text(encoding="utf-8"))
    current_id = meta.get("id", "")
    if PLACEHOLDER in current_id:
        meta["id"] = current_id.replace(PLACEHOLDER, username)
        KERNEL_METADATA.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        print(f"Using Kaggle username: {username}")

    print("Pushing notebook to Kaggle (kaggle kernels push)...")
    # Use the kaggle CLI (pip installs a "kaggle" console script)
    result = subprocess.run(
        ["kaggle", "kernels", "push", "-p", str(API_NOTEBOOK_DIR)],
        cwd=REPO_ROOT,
        shell=(os.name == "nt"),  # on Windows, shell=True so "kaggle" is found in PATH
    )
    if result.returncode != 0:
        sys.exit(result.returncode)
    print("Done. Check your Kaggle profile for the 'API Notebook Creator' badge.")


if __name__ == "__main__":
    main()
