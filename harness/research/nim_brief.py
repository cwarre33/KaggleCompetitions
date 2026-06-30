from __future__ import annotations

import json
from typing import Any

from harness.llm.nim_client import chat


def _prompt(*, context_pack: dict[str, Any]) -> str:
    meta = context_pack.get("competition_meta", {})
    pipelines = context_pack.get("pipelines", {})
    entrypoints = context_pack.get("entrypoints", {})
    baseline = context_pack.get("artifacts_history", {}).get("baseline_json", {})

    return f"""You are a Kaggle competition expert.\n\nYou will be given a JSON context pack extracted from an existing codebase. Your job is to produce a concise, actionable research brief that sets up the next training run.\n\n## Competition\n- slug: {meta.get('slug')}\n- local_dir: {meta.get('competition_dir')}\n\n## Detected entrypoints\n{json.dumps(entrypoints, indent=2)[:2000]}\n\n## Detected pipeline signals\n{json.dumps(pipelines, indent=2)}\n\n## Baseline history (if present)\n{json.dumps(baseline, indent=2)[:2000]}\n\n## Full context pack (truncated)\n{json.dumps(context_pack, ensure_ascii=False)[:12000]}\n\n## Output format (STRICT)\nReturn markdown with these sections:\n\n1) **Fast baseline** (what to run first)\n2) **Likely strong approaches** (2-5 bullets)\n3) **First 3 experiments**: each must include: hypothesis, exact change, expected CV impact, risks\n4) **Next command**: a single shell command line beginning with `kaggle-harness` using Hydra `--override` flags.\n\nImportant constraints:\n- Assume this will run inside a Kaggle Notebook.\n- Prefer robust CV and simple feature engineering over exotic tricks.\n- If the competition might be closed/expired, still produce a runnable training command; don’t rely on submission APIs.\n"""


def generate_research_brief(
    *,
    context_pack: dict[str, Any],
    model: str = "meta/llama-3.1-8b-instruct",
    api_key: str | None = None,
) -> str:
    prompt = _prompt(context_pack=context_pack)
    return chat(prompt=prompt, model=model, api_key=api_key, max_tokens=2048)

