#!/usr/bin/env python3
"""
Create a Kaggle model and two model instances (variations) via the API.
Earns: API Model Creator, Model Variation Creator.

Order: 1) Create model, 2) Create instance 1, 3) Create instance 2.

Prerequisites: pip install kaggle, kaggle.json in %USERPROFILE%\\.kaggle\\

Run from repo root:
  python create_api_models.py
"""

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
API_MODEL_DIR = REPO_ROOT / "api_model"
INSTANCE_V1 = REPO_ROOT / "api_model_instance_v1"
INSTANCE_V2 = REPO_ROOT / "api_model_instance_v2"
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


def replace_owner_in_metadata(path, username):
    p = Path(path)
    if not p.is_file():
        return
    data = json.loads(p.read_text(encoding="utf-8"))
    if "ownerSlug" in data and PLACEHOLDER in str(data["ownerSlug"]):
        data["ownerSlug"] = username
        p.write_text(json.dumps(data, indent=2), encoding="utf-8")


def main():
    username = get_kaggle_username()
    if not username:
        print("Kaggle username not found. Place kaggle.json in %USERPROFILE%\\.kaggle\\ or set KAGGLE_USERNAME.", file=sys.stderr)
        sys.exit(1)

    for path in [API_MODEL_DIR / "model-metadata.json", INSTANCE_V1 / "model-instance-metadata.json", INSTANCE_V2 / "model-instance-metadata.json"]:
        replace_owner_in_metadata(path, username)
    print(f"Using Kaggle username: {username}")

    # 1) Create model (no files, just metadata)
    print("Step 1: Creating model (kaggle models create)...")
    r1 = subprocess.run(
        ["kaggle", "models", "create", "-p", str(API_MODEL_DIR)],
        cwd=REPO_ROOT,
        shell=(os.name == "nt"),
    )
    if r1.returncode != 0:
        print("Model create failed. You may need early-access to Kaggle Models API.", file=sys.stderr)
        sys.exit(r1.returncode)

    # 2) Create first instance (variation)
    print("Step 2: Creating first model instance / variation (kaggle models instances create)...")
    r2 = subprocess.run(
        ["kaggle", "models", "instances", "create", "-p", str(INSTANCE_V1)],
        cwd=REPO_ROOT,
        shell=(os.name == "nt"),
    )
    if r2.returncode != 0:
        print("First instance create failed.", file=sys.stderr)
        sys.exit(r2.returncode)

    # 3) Create second instance (second variation -> Model Variation Creator)
    print("Step 3: Creating second model instance / variation...")
    r3 = subprocess.run(
        ["kaggle", "models", "instances", "create", "-p", str(INSTANCE_V2)],
        cwd=REPO_ROOT,
        shell=(os.name == "nt"),
    )
    if r3.returncode != 0:
        print("Second instance create failed.", file=sys.stderr)
        sys.exit(r3.returncode)

    print("Done. Check accomplishments for: API Model Creator, Model Variation Creator.")


if __name__ == "__main__":
    main()
