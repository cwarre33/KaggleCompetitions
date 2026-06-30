#!/usr/bin/env python3
"""
Create a dataset on Kaggle using the Kaggle API.
This earns you the "API Dataset Creator" badge.

Prerequisites: pip install kaggle, and kaggle.json in %USERPROFILE%\\.kaggle\\ (or KAGGLE_USERNAME/KAGGLE_KEY).

Run from repo root:
  python create_api_dataset.py
"""

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
API_DATASET_DIR = REPO_ROOT / "api_dataset"
METADATA_FILE = API_DATASET_DIR / "dataset-metadata.json"
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
    if not API_DATASET_DIR.is_dir() or not METADATA_FILE.is_file():
        print("Error: api_dataset/ and dataset-metadata.json must exist.", file=sys.stderr)
        sys.exit(1)

    username = get_kaggle_username()
    if not username:
        print(
            "Kaggle username not found. Place kaggle.json in %USERPROFILE%\\.kaggle\\ or set KAGGLE_USERNAME.",
            file=sys.stderr,
        )
        sys.exit(1)

    meta = json.loads(METADATA_FILE.read_text(encoding="utf-8"))
    current_id = meta.get("id", "")
    if PLACEHOLDER in current_id:
        meta["id"] = current_id.replace(PLACEHOLDER, username)
        METADATA_FILE.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        print(f"Using Kaggle username: {username}")

    print("Creating dataset on Kaggle (kaggle datasets create)...")
    result = subprocess.run(
        ["kaggle", "datasets", "create", "-p", str(API_DATASET_DIR)],
        cwd=REPO_ROOT,
        shell=(os.name == "nt"),
    )
    if result.returncode != 0:
        sys.exit(result.returncode)
    print("Done. Check your Kaggle profile for the 'API Dataset Creator' badge.")


if __name__ == "__main__":
    main()
