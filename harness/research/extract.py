from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


KEYWORDS = [
    "StratifiedKFold",
    "KFold",
    "GroupKFold",
    "TimeSeriesSplit",
    "xgboost",
    "XGB",
    "lightgbm",
    "LGBM",
    "catboost",
    "CatBoost",
    "optuna",
    "torch",
    "transformers",
    "fit(",
    "train",
    "predict",
    "submission",
]


def _read_text(path: Path, max_chars: int) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:max_chars]
    except Exception:
        return ""


def _extract_headings_from_markdown(text: str, max_lines: int = 80) -> list[str]:
    out: list[str] = []
    for line in text.splitlines()[:max_lines]:
        if line.lstrip().startswith("#"):
            out.append(line.strip())
    return out


def _ipynb_summary(path: Path, *, max_cells: int, max_cell_chars: int) -> dict[str, Any]:
    try:
        nb = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return {"path": str(path), "error": "failed_to_parse"}

    cells = nb.get("cells", [])
    headings: list[str] = []
    key_cells: list[dict[str, Any]] = []

    for c in cells[:max_cells]:
        ctype = c.get("cell_type")
        source = "".join(c.get("source", []) if isinstance(c.get("source", []), list) else [str(c.get("source", ""))])
        if ctype == "markdown":
            for line in source.splitlines():
                if line.lstrip().startswith("#"):
                    headings.append(line.strip())
        elif ctype == "code":
            src = source[:max_cell_chars]
            if any(k.lower() in src.lower() for k in KEYWORDS):
                key_cells.append({"cell_type": "code", "source": src})

    return {
        "path": str(path),
        "headings": headings[:30],
        "key_cells": key_cells[:20],
        "n_cells": len(cells),
    }


def _detect_entrypoints(paths: list[Path]) -> list[str]:
    out: list[str] = []
    for p in paths:
        name = p.name.lower()
        if name in {"run_on_kaggle.py", "submit.py", "run_auto_loop.py", "improvement_loop.py"}:
            out.append(str(p))
    return sorted(out)


def _python_signals(text: str) -> dict[str, Any]:
    lc = text.lower()
    families = []
    for fam in ["xgboost", "lightgbm", "catboost", "torch", "transformers", "optuna"]:
        if fam in lc:
            families.append(fam)

    cv = []
    for cv_name in ["stratifiedkfold", "kfold", "groupkfold", "timeseriessplit"]:
        if cv_name in lc:
            cv.append(cv_name)

    # crude feature function hints
    feats = []
    for m in re.finditer(r"def\s+(add_features|preprocess|build_features)\s*\(", text):
        feats.append(m.group(1))

    return {"model_families": families, "cv": cv, "feature_fns": feats}


def build_context_pack(
    *,
    competition_dir: str | Path,
    slug: str,
    max_files: int = 50,
    max_file_chars: int = 20000,
    max_notebooks: int = 10,
    max_notebook_cells: int = 80,
    max_cell_chars: int = 4000,
) -> dict[str, Any]:
    competition_dir = Path(competition_dir).resolve()

    scripts = sorted((competition_dir / "scripts").glob("*.py"))
    src_train = sorted((competition_dir / "src").glob("train*.py"))
    readmes = []
    if (competition_dir / "README.md").exists():
        readmes.append(competition_dir / "README.md")
    research_md = sorted((competition_dir / "research").glob("*.md"))

    notebooks = sorted((competition_dir / "notebooks").glob("*.ipynb"))[:max_notebooks]
    submissions = sorted((competition_dir / "submissions").glob("*.csv"))

    baseline_json = competition_dir / "research" / "baseline.json"
    attempt_log = competition_dir / "research" / "attempt_log.jsonl"

    py_files = (scripts + src_train)[:max_files]
    py_summaries: list[dict[str, Any]] = []
    pipeline_signals = {"model_families": set(), "cv": set(), "feature_fns": set()}

    for p in py_files:
        txt = _read_text(p, max_file_chars)
        sig = _python_signals(txt)
        for k in pipeline_signals.keys():
            for v in sig.get(k, []):
                pipeline_signals[k].add(v)
        py_summaries.append(
            {
                "path": str(p),
                "size": p.stat().st_size if p.exists() else None,
                "signals": sig,
                "snippet": txt[:2000],
            }
        )

    md_summaries: list[dict[str, Any]] = []
    for p in (readmes + research_md)[:max_files]:
        txt = _read_text(p, max_file_chars)
        md_summaries.append(
            {
                "path": str(p),
                "headings": _extract_headings_from_markdown(txt),
                "snippet": txt[:4000],
            }
        )

    nb_summaries = [_ipynb_summary(p, max_cells=max_notebook_cells, max_cell_chars=max_cell_chars) for p in notebooks]

    history: dict[str, Any] = {}
    if baseline_json.exists():
        try:
            history["baseline_json"] = json.loads(baseline_json.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            history["baseline_json"] = {"error": "failed_to_parse"}
    if attempt_log.exists():
        lines = attempt_log.read_text(encoding="utf-8", errors="ignore").splitlines()
        history["attempt_log_tail"] = lines[-20:]

    context_pack: dict[str, Any] = {
        "competition_meta": {
            "slug": slug,
            "competition_dir": str(competition_dir),
        },
        "entrypoints": {
            "detected": _detect_entrypoints(scripts),
        },
        "pipelines": {
            "model_families": sorted(pipeline_signals["model_families"]),
            "cv": sorted(pipeline_signals["cv"]),
            "feature_fns": sorted(pipeline_signals["feature_fns"]),
        },
        "python_files": py_summaries,
        "markdown_files": md_summaries,
        "notebooks": nb_summaries,
        "artifacts_history": {
            "submissions": [p.name for p in submissions[-20:]],
            **history,
        },
    }

    return context_pack

