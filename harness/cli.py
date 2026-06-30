from __future__ import annotations

import argparse
import importlib
from pathlib import Path

from harness import __version__
from harness.hydra_utils import compose_config
from harness.trainer import HarnessTrainer
from harness.artifacts import init_run
from harness.research.extract import build_context_pack
from harness.research.nim_brief import generate_research_brief


def _import_symbol(spec: str):
    """
    Import `module:Symbol` and return `Symbol`.
    Example: `competitions.example_competition.task:ExampleTask`
    """
    if ":" not in spec:
        raise ValueError(f"Expected 'module:Symbol', got: {spec}")
    mod_name, sym_name = spec.split(":", 1)
    mod = importlib.import_module(mod_name)
    return getattr(mod, sym_name)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="kaggle-harness")
    p.add_argument("--version", action="store_true", help="Print version and exit")

    sub = p.add_subparsers(dest="cmd")

    research = sub.add_parser("research", help="Extract working solutions + generate NIM research brief")
    research.add_argument("--competition-dir", required=True, help="Path to competition folder (e.g. PredictingHeartDisease)")
    research.add_argument("--slug", required=True, help="Kaggle competition slug (for /kaggle/input/<slug>)")
    research.add_argument("--repo-root", default=".", help="Repo root (used for run artifacts + conf)")
    research.add_argument("--out", default="auto", help="Output root (auto -> /kaggle/working if present)")
    research.add_argument("--model", default="meta/llama-3.1-8b-instruct", help="NIM model name")
    research.add_argument("--max-files", type=int, default=50)
    research.add_argument("--max-notebook-cells", type=int, default=80)

    run = sub.add_parser("run", help="Run a competition entrypoint module")
    run.add_argument(
        "--competition",
        required=True,
        help="Competition run module, e.g. competitions.my_comp.run",
    )
    run.add_argument(
        "--action",
        required=True,
        choices=["train", "predict", "make-submission"],
        help="Action to execute",
    )
    run.add_argument("--repo-root", default=".", help="Repo root (used to find ./conf)")
    run.add_argument(
        "--override",
        action="append",
        default=[],
        help="Hydra override, repeatable. Example: --override trainer.max_epochs=3",
    )

    predict = sub.add_parser("predict", help="Alias for: run --action predict")
    predict.add_argument("--competition", required=True, help="Competition run module, e.g. competitions.my_comp.run")
    predict.add_argument("--repo-root", default=".", help="Repo root (used to find ./conf)")
    predict.add_argument(
        "--override",
        action="append",
        default=[],
        help="Hydra override, repeatable. Example: --override paths.out_dir=/kaggle/working",
    )

    ms = sub.add_parser("make-submission", help="Alias for: run --action make-submission")
    ms.add_argument("--competition", required=True, help="Competition run module, e.g. competitions.my_comp.run")
    ms.add_argument("--repo-root", default=".", help="Repo root (used to find ./conf)")
    ms.add_argument(
        "--override",
        action="append",
        default=[],
        help="Hydra override, repeatable. Example: --override competition.data_dir=/kaggle/input/...",
    )

    train = sub.add_parser("train", help="Train a task using the harness trainer")
    train.add_argument(
        "--task",
        required=True,
        help="Task class spec: module:Symbol (must inherit harness.base.BaseTask)",
    )
    train.add_argument(
        "--repo-root",
        default=".",
        help="Repo root (used to find ./conf). Default: current directory",
    )
    train.add_argument(
        "--config-name",
        default="global_defaults",
        help="Hydra config name (in conf/). Default: global_defaults",
    )
    train.add_argument(
        "--override",
        action="append",
        default=[],
        help="Hydra override, repeatable. Example: --override trainer.max_epochs=3",
    )

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(__version__)
        return 0

    if args.cmd == "research":
        repo_root = Path(args.repo_root).resolve()

        # Load .env for local runs (Kaggle Secrets usually provide env vars already).
        try:
            from dotenv import load_dotenv  # type: ignore

            load_dotenv(repo_root / ".env")
            load_dotenv(repo_root.parent / ".env")
        except Exception:
            pass

        run = init_run(
            competition=str(args.slug),
            repo_root=str(repo_root),
            out_dir=str(args.out),
            config_snapshot={"cmd": "research", "slug": args.slug},
        )

        context_pack = build_context_pack(
            competition_dir=repo_root / args.competition_dir,
            slug=str(args.slug),
            max_files=int(args.max_files),
            max_notebook_cells=int(args.max_notebook_cells),
        )
        (run.artifacts_dir / "context_pack.json").write_text(
            __import__("json").dumps(context_pack, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        try:
            brief = generate_research_brief(context_pack=context_pack, model=str(args.model))
        except Exception as e:
            brief = (
                "## Research brief (NIM call failed)\n\n"
                f"Error: `{e}`\n\n"
                "Set `NIM_API_KEY` in the environment and rerun.\n"
            )

        (run.artifacts_dir / "research_brief.md").write_text(brief, encoding="utf-8")

        # Print a suggested next-step command (user can tweak overrides)
        print("Wrote:", run.artifacts_dir / "context_pack.json")
        print("Wrote:", run.artifacts_dir / "research_brief.md")
        print("\nNext step (example):")
        print(
            "kaggle-harness run --competition competitions.playground_series_s6e2.run --action train "
            f"--override competition.slug={args.slug} --override competition.data_dir=/kaggle/input/{args.slug} "
            "--override model.algorithm=xgboost"
        )
        return 0

    if args.cmd == "run":
        mod = importlib.import_module(args.competition)
        if not hasattr(mod, "main"):
            raise AttributeError(f"{args.competition} must define a main(...) function")
        return int(
            mod.main(
                action=args.action,
                repo_root=str(Path(args.repo_root).resolve()),
                overrides=list(args.override or []),
            )
            or 0
        )

    if args.cmd == "train":
        repo_root = Path(args.repo_root).resolve()
        cfg = compose_config(
            config_dir=repo_root / "conf",
            config_name=args.config_name,
            overrides=list(args.override or []),
        )
        task_cls = _import_symbol(args.task)
        trainer = HarnessTrainer(cfg)
        trainer.setup_task(task_cls)
        trainer.train()
        return 0

    if args.cmd == "predict":
        mod = importlib.import_module(args.competition)
        return int(
            mod.main(
                action="predict",
                repo_root=str(Path(args.repo_root).resolve()),
                overrides=list(args.override or []),
            )
            or 0
        )

    if args.cmd == "make-submission":
        mod = importlib.import_module(args.competition)
        return int(
            mod.main(
                action="make-submission",
                repo_root=str(Path(args.repo_root).resolve()),
                overrides=list(args.override or []),
            )
            or 0
        )

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

