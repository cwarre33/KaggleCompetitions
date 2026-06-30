#!/usr/bin/env python3
"""
Create a fully documented dataset on Kaggle (subtitle, description, keywords,
file + column descriptions) to aim for usability 10 and the "Dataset Documenter" badge.

Prerequisites: pip install kaggle, kaggle.json in %USERPROFILE%\\.kaggle\\

Run from repo root:
  python create_documenter_dataset.py
Then on Kaggle: open the dataset → add Cover Image, Source, Update frequency (if needed) to reach 10.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
DOCUMENTER_DIR = REPO_ROOT / "documenter_dataset"
METADATA_FILE = DOCUMENTER_DIR / "dataset-metadata.json"
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
    if not DOCUMENTER_DIR.is_dir() or not METADATA_FILE.is_file():
        print("Error: documenter_dataset/ and dataset-metadata.json must exist.", file=sys.stderr)
        sys.exit(1)

    username = get_kaggle_username()
    if not username:
        print("Kaggle username not found. Place kaggle.json in %USERPROFILE%\\.kaggle\\ or set KAGGLE_USERNAME.", file=sys.stderr)
        sys.exit(1)

    meta = json.loads(METADATA_FILE.read_text(encoding="utf-8"))
    if PLACEHOLDER in meta.get("id", ""):
        meta["id"] = meta["id"].replace(PLACEHOLDER, username)
        METADATA_FILE.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        print(f"Using Kaggle username: {username}")

    print("Creating documented dataset (kaggle datasets create)...")
    result = subprocess.run(
        ["kaggle", "datasets", "create", "-p", str(DOCUMENTER_DIR)],
        cwd=REPO_ROOT,
        shell=(os.name == "nt"),
    )
    if result.returncode != 0:
        sys.exit(result.returncode)
    print("Done. Open the dataset on Kaggle and add Cover Image + Source + Update frequency if needed for usability 10. See DATASET_DOCUMENTER_GUIDE.md.")


if __name__ == "__main__":
    main()
