#!/usr/bin/env python3
"""Push model_pipeline_notebook to Kaggle. Run it there, then create model from output for the badge."""
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
NOTEBOOK_DIR = REPO_ROOT / "model_pipeline_notebook"
META = NOTEBOOK_DIR / "kernel-metadata.json"
PLACEHOLDER = "YOUR_KAGGLE_USERNAME"

def get_username():
    u = os.environ.get("KAGGLE_USERNAME")
    if u: return u
    kj = Path.home() / ".kaggle" / "kaggle.json"
    if kj.is_file():
        try: return json.loads(kj.read_text()).get("username")
        except Exception: pass
    return None

def main():
    username = get_username()
    if not username:
        print("Kaggle username not found. Set KAGGLE_USERNAME or add kaggle.json to ~/.kaggle/", file=sys.stderr)
        sys.exit(1)
    if META.is_file():
        data = json.loads(META.read_text())
        if PLACEHOLDER in data.get("id", ""):
            data["id"] = data["id"].replace(PLACEHOLDER, username)
            META.write_text(json.dumps(data, indent=2))
    r = subprocess.run(["kaggle", "kernels", "push", "-p", str(NOTEBOOK_DIR)], cwd=REPO_ROOT, shell=(os.name == "nt"))
    sys.exit(r.returncode)

if __name__ == "__main__":
    main()
