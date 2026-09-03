"""Driver attribution for TOC excursion episodes on the rolling-origin test years.

Usage (from experiments/):
    .venv/bin/python -m drivers.run                  # rf_grid and catboost
    .venv/bin/python -m drivers.run --models catboost

Episodes are found on the anchored index (the days the models were scored on),
driver labels are read from the full unanchored frame. Results in drivers/results/:
episodes.csv (one row per episode with driver, detection, and lead per model),
recall-by-driver.csv, coverage.csv (raw excursion days per year and how many
the anchored index misses), and episodes.meta.json.
"""

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import catboost
import numpy as np
import pandas as pd
import sklearn

from ablation.configs import JAKE_FEATURES
from ablation.frame import RECIPES, build_frame, load_sources
from ablation.scoring import FITTERS, TARGETS, TargetSpec, anchored_rows
from drivers.episodes import Episode, episode_detection, episodes, label_driver
from drivers.report import coverage_table, episode_table, recall_table
from rolling.folds import Fold, rolling_origin_folds

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE.parent.parent / "data"
RESULTS_DIR = HERE / "results"
META_FILE = "episodes.meta.json"
TARGET = "TOC"
DEFAULT_MODELS = ("rf_grid", "catboost")


def main(argv: list[str] | None = None) -> int:
    args = _parse(argv)
    spec = TARGETS[TARGET]
    full = build_frame(load_sources(DATA_DIR), RECIPES[TARGET])
    anchored = anchored_rows(full, TARGET, JAKE_FEATURES[TARGET], JAKE_FEATURES[TARGET])
    tables = _attribute(full, rolling_origin_folds(anchored), args.models, spec)
    tables["coverage"] = coverage_table(full[TARGET], anchored.index, spec.excursion_threshold, spec.excursion_is_above)
    _write(tables)
    return 0


def _parse(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", choices=list(DEFAULT_MODELS), default=list(DEFAULT_MODELS))
    return parser.parse_args(argv)


def _attribute(full: pd.DataFrame, folds: list[Fold], models: list[str], spec: TargetSpec) -> dict[str, pd.DataFrame]:
    actual = pd.concat([fold.test[TARGET] for fold in folds]).sort_index()
    found = episodes(actual, spec.excursion_threshold, spec.excursion_is_above)
    labels = [label_driver(episode, full) for episode in found]
    detections = {model: _detections(found, _test_predictions(folds, model, spec), spec) for model in models}
    return {
        "episodes": episode_table(found, labels, detections),
        "recall-by-driver": recall_table(found, labels, detections),
    }


def _test_predictions(folds: list[Fold], model: str, spec: TargetSpec) -> pd.Series:
    features = JAKE_FEATURES[TARGET]
    parts = []
    for fold in folds:
        print(f"{TARGET} {model} test year {fold.test_year}", file=sys.stderr)
        preds, _ = FITTERS[model](fold.train[features], fold.train[TARGET], fold.test[features], spec)
        parts.append(pd.Series(preds, index=fold.test.index))
    return pd.concat(parts).sort_index()


def _detections(found: list[Episode], preds: pd.Series, spec: TargetSpec):
    return [episode_detection(episode, preds, spec.excursion_threshold, spec.excursion_is_above) for episode in found]


def _write(tables: dict[str, pd.DataFrame]) -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    for name, table in tables.items():
        table.to_csv(RESULTS_DIR / f"{name}.csv", index=False, float_format="%.6f")
        print(table.to_string(index=False), file=sys.stderr)
    (RESULTS_DIR / META_FILE).write_text(json.dumps(_metadata(), indent=2))


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


if __name__ == "__main__":
    sys.exit(main())
