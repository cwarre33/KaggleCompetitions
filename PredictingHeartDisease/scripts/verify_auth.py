"""Verify Kaggle API authentication using KAGGLE_API_TOKEN from .env"""
import sys
from pathlib import Path

# Load .env from project root
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / ".env")

def main():
    token = __import__("os").environ.get("KAGGLE_API_TOKEN")
    if not token:
        print("ERROR: KAGGLE_API_TOKEN not found in environment. Check .env")
        return False
    
    print(f"Token found: {token[:15]}...")
    
    try:
        import kagglehub
        path = kagglehub.competition_download("playground-series-s6e2")
        print(f"SUCCESS: Auth works. Data path: {path}")
        return True
    except Exception as e:
        print(f"kagglehub failed: {e}")
        print("Trying classic kaggle CLI...")
        try:
            import subprocess
            result = subprocess.run(
                ["kaggle", "competitions", "list", "--page", "1"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                print("SUCCESS: Classic kaggle CLI works")
                return True
            print(f"kaggle CLI failed: {result.stderr}")
        except Exception as e2:
            print(f"kaggle CLI error: {e2}")
        return False

if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
