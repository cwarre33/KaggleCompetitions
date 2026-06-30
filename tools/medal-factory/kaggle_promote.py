#!/usr/bin/env python3
"""
Kaggle notebook promotion tool.
- List all your notebooks via Kaggle API
- Optionally make private notebooks public (pull → set is_private → push)
- Export a report and links for promotion

Requires: pip install kaggle
Auth: KAGGLE_USERNAME + KAGGLE_KEY, or ~/.kaggle/kaggle.json
"""

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path


try:
    from kaggle.api.kaggle_api_extended import KaggleApi
except ImportError:
    print("Install the Kaggle API: pip install kaggle", file=sys.stderr)
    sys.exit(1)

KERNEL_METADATA_FILE = "kernel-metadata.json"
BASE_URL = "https://www.kaggle.com/code"


def get_api():
    api = KaggleApi()
    api.authenticate()
    return api


def list_my_kernels(api, page_size=100, max_pages=10):
    """List all kernels for the authenticated user (paginated)."""
    all_kernels = []
    page = 1
    while page <= max_pages:
        kernels = api.kernels_list(mine=True, page=page, page_size=page_size)
        if not kernels:
            break
        for k in kernels:
            ref = getattr(k, "ref", None) or getattr(k, "slug", None)
            if not ref and hasattr(k, "owner_slug") and hasattr(k, "slug"):
                ref = f"{k.owner_slug}/{k.slug}"
            if ref:
                all_kernels.append(k)
        if len(kernels) < page_size:
            break
        page += 1
    return all_kernels


def kernel_ref(k):
    """Get ref string (username/slug) for a kernel object."""
    ref = getattr(k, "ref", None)
    if ref:
        return ref
    if hasattr(k, "owner_slug") and hasattr(k, "slug"):
        return f"{k.owner_slug}/{k.slug}"
    return None


def make_public(api, kernel_ref_str, dry_run=True, only_if_private=True):
    """
    Make a kernel public: pull (with metadata), set is_private=False, push.
    Returns (success: bool, message: str).
    If only_if_private and kernel is already public, returns (True, "Already public") without pushing.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            api.kernels_pull(kernel_ref_str, path=tmpdir, metadata=True, quiet=True)
        except Exception as e:
            return False, f"Pull failed: {e}"
        meta_path = os.path.join(tmpdir, KERNEL_METADATA_FILE)
        if not os.path.isfile(meta_path):
            return False, "No metadata file after pull"
        with open(meta_path) as f:
            meta = json.load(f)
        if meta.get("is_private", True) is False:
            return True, "Already public"
        if dry_run:
            return True, "[dry run] Would set public"
        meta["is_private"] = False
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)
        try:
            api.kernels_push(tmpdir)
            return True, "Set to public"
        except Exception as e:
            return False, f"Push failed: {e}"


def main():
    parser = argparse.ArgumentParser(
        description="List your Kaggle notebooks, make them public, and get links for promotion."
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all your notebooks (default if no other action).",
    )
    parser.add_argument(
        "--make-public",
        action="store_true",
        help="Make private notebooks public (pull, set is_private=false, push).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="With --make-public, only show what would be done; do not push.",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=100,
        help="Kernels per page when listing (default 100).",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=10,
        help="Max pages to fetch when listing (default 10).",
    )
    parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="Write report (markdown + links) to this file.",
    )
    args = parser.parse_args()

    if not args.list and not args.make_public:
        args.list = True

    try:
        api = get_api()
    except Exception as e:
        print("Kaggle authentication failed:", e, file=sys.stderr)
        print("Set KAGGLE_USERNAME and KAGGLE_KEY, or place kaggle.json in ~/.kaggle/", file=sys.stderr)
        sys.exit(1)

    # List
    kernels = list_my_kernels(api, page_size=args.page_size, max_pages=args.max_pages)
    if not kernels:
        print("No kernels found for your account.")
        return

    lines = []
    lines.append("# Your Kaggle notebooks\n")
    lines.append(f"Total: {len(kernels)} notebook(s)\n")
    lines.append("| Ref | Title | Link |")
    lines.append("|-----|-------|------|")

    for k in kernels:
        ref = kernel_ref(k)
        if not ref:
            continue
        title = getattr(k, "title", ref)
        link = f"{BASE_URL}/{ref}"
        lines.append(f"| {ref} | {title} | [Open]({link}) |")

    report = "\n".join(lines)
    # Avoid UnicodeEncodeError on Windows console (e.g. emoji in titles)
    try:
        print(report)
    except UnicodeEncodeError:
        enc = sys.stdout.encoding or "utf-8"
        print(report.encode(enc, errors="replace").decode(enc))

    # Make public
    if args.make_public:
        print("\n--- Make public ---")
        for k in kernels:
            ref = kernel_ref(k)
            if not ref:
                continue
            ok, msg = make_public(api, ref, dry_run=args.dry_run, only_if_private=True)
            status = "OK" if ok else "FAIL"
            print(f"  {ref}: [{status}] {msg}")

    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
        print(f"\nReport written to {args.out}")


if __name__ == "__main__":
    main()
