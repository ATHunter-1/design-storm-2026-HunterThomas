"""Run the ablation study and write one results table per run.

Usage (from experiments/):
    .venv/bin/python -m ablation.run                 # both targets, rf_grid + catboost
    .venv/bin/python -m ablation.run --target Alk    # one target
    .venv/bin/python -m ablation.run --models catboost
    .venv/bin/python -m ablation.run --check         # determinism: run jake_full twice, diff

Results: ablation/results/<target>-<models>.csv plus a .meta.json recording
input md5s, library versions, and the git commit.
"""

import argparse
import hashlib
import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

import catboost
import numpy as np
import pandas as pd
import sklearn

from ablation.configs import Config, JAKE_FEATURES, ablation_configs
from ablation.frame import RECIPES, build_frame, load_sources
from ablation.scoring import TARGETS, score_feature_set

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE.parent.parent / "data"
RESULTS_DIR = HERE / "results"
DEFAULT_MODELS = ("rf_grid", "catboost")


def main(argv: list[str] | None = None) -> int:
    args = _parse(argv)
    sources = load_sources(DATA_DIR)
    if args.check:
        return _determinism_check(sources, args.target or "Alk")
    for target in _targets(args.target):
        frame = build_frame(sources, RECIPES[target])
        rows = _score_all(frame, ablation_configs(target, tuple(args.models)))
        _write(target, args.models, rows)
    return 0


def _parse(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", choices=list(TARGETS), default=None)
    parser.add_argument("--models", nargs="+", choices=["rf_grid", "catboost"], default=list(DEFAULT_MODELS))
    parser.add_argument("--check", action="store_true")
    return parser.parse_args(argv)


def _targets(chosen: str | None) -> list[str]:
    return [chosen] if chosen else list(TARGETS)


def _score_all(frame: pd.DataFrame, configs: list[Config]) -> list[dict]:
    rows = []
    for i, config in enumerate(configs, 1):
        print(f"[{i}/{len(configs)}] {config.target} {config.model} {config.label}", file=sys.stderr)
        scores = score_feature_set(
            frame, TARGETS[config.target], list(config.features), config.model,
            anchor=JAKE_FEATURES[config.target],
        )
        rows.append({**_config_row(config), **asdict(scores)})
    return rows


def _config_row(config: Config) -> dict:
    return {
        "target": config.target,
        "model": config.model,
        "label": config.label,
        "n_features": len(config.features),
        "features": " ".join(config.features),
    }


def _write(target: str, models: list[str], rows: list[dict]) -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    stem = f"{target}-{'+'.join(models)}"
    table = pd.DataFrame(rows)
    table.to_csv(RESULTS_DIR / f"{stem}.csv", index=False, float_format="%.6f")
    (RESULTS_DIR / f"{stem}.meta.json").write_text(json.dumps(_metadata(), indent=2))
    print(_summary(table), file=sys.stderr)


def _metadata() -> dict:
    return {
        "inputs_md5": {p.name: hashlib.md5(p.read_bytes()).hexdigest() for p in sorted(DATA_DIR.glob("*.csv"))},
        "versions": {
            "python": sys.version.split()[0],
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit-learn": sklearn.__version__,
            "catboost": catboost.__version__,
        },
        "git_commit": _git_commit(),
    }


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=HERE, text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def _summary(table: pd.DataFrame) -> str:
    cols = ["model", "label", "n_features", "r2", "rmse", "excursion_recall", "excursion_precision"]
    return table[cols].sort_values(["model", "r2"], ascending=[True, False]).to_string(index=False)


def _determinism_check(sources, target: str) -> int:
    frame = build_frame(sources, RECIPES[target])
    config = Config(target, "jake_full", tuple(JAKE_FEATURES[target]), "rf_grid")
    first = _score_all(frame, [config, Config(target, "jake_full", config.features, "catboost")])
    second = _score_all(frame, [config, Config(target, "jake_full", config.features, "catboost")])
    identical = first == second
    print("determinism check:", "identical" if identical else "DIFFERS", file=sys.stderr)
    if not identical:
        print(json.dumps({"first": first, "second": second}, indent=2), file=sys.stderr)
    return 0 if identical else 1


if __name__ == "__main__":
    sys.exit(main())
