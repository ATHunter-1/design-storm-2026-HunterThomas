"""Regime split: train on wet water years and test on dry, and the reverse.

Usage (from experiments/):
    .venv/bin/python -m regime.run                       # both targets, rf_grid + catboost
    .venv/bin/python -m regime.run --target TOC --models catboost

Results: regime/results/labels.csv (every in-kit water year with its April 1 SWE,
fraction of the reference median, label, and the reference itself), one
<target>-<models>.csv per run with a row per model and direction, and a
.meta.json with input md5s, library versions, and the git commit.
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

from ablation.configs import JAKE_FEATURES
from ablation.frame import RECIPES, build_frame, load_sources
from ablation.run import DATA_DIR
from ablation.scoring import TARGETS, anchored_rows
from analog.run import load_swe as load_full_swe
from regime.labels import labels_table, reference_from
from regime.split import RegimeFold, RegimeScores, regime_folds, score_regime_fold
from snowpack.run import SNOTEL_FILE, load_swe as load_kit_swe
from snowpack.wateryear import summarise_by_water_year

HERE = Path(__file__).resolve().parent
RESULTS_DIR = HERE / "results"
KIT_SWE_PATH = DATA_DIR / SNOTEL_FILE
FULL_SWE_PATH = HERE.parent / "analog" / "data" / "MichiganCreek_full.csv"
LABELS_FILE = "labels.csv"
DEFAULT_MODELS = ("rf_grid", "catboost")
FLOAT_FORMAT = "%.6f"


def main(argv: list[str] | None = None) -> int:
    args = _parse(argv)
    labels = write_labels(KIT_SWE_PATH, FULL_SWE_PATH, RESULTS_DIR)["label"].dropna()
    sources = load_sources(DATA_DIR)
    for target in ([args.target] if args.target else list(TARGETS)):
        table = _evaluate_target(sources, target, labels, args.models)
        _write(target, args.models, table)
    return 0


def _parse(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", choices=list(TARGETS), default=None)
    parser.add_argument("--models", nargs="+", choices=["rf_grid", "catboost"], default=list(DEFAULT_MODELS))
    return parser.parse_args(argv)


def write_labels(kit_path: Path, full_path: Path, results_dir: Path) -> pd.DataFrame:
    kit_summary = summarise_by_water_year(load_kit_swe(kit_path))
    full_summary = summarise_by_water_year(load_full_swe(full_path)) if full_path.exists() else None
    table = labels_table(kit_summary, reference_from(full_summary, kit_summary))
    results_dir.mkdir(exist_ok=True)
    table.to_csv(results_dir / LABELS_FILE, float_format="%.4f")
    print(table.to_string(), file=sys.stderr)
    return table


def _evaluate_target(sources, target: str, labels: pd.Series, models: list[str]) -> pd.DataFrame:
    features = list(JAKE_FEATURES[target])
    frame = anchored_rows(build_frame(sources, RECIPES[target]), target, features, features)
    folds = [fold for fold in regime_folds(frame, labels) if _scorable(fold, target)]
    rows = [_row(model, score_regime_fold(fold, TARGETS[target], features, model)) for model in models for fold in folds]
    return pd.DataFrame(rows)


def _scorable(fold: RegimeFold, target: str) -> bool:
    description = f"{target} train {fold.train_regime} {fold.train_years} test {fold.test_regime} {fold.test_years}"
    if fold.train.empty or fold.test.empty:
        print(f"skip {description}: one side has no rows", file=sys.stderr)
        return False
    print(f"{description}, excluded {fold.excluded_rows}", file=sys.stderr)
    return True


def _row(model: str, scores: RegimeScores) -> dict:
    row = {"model": model, **asdict(scores)}
    row["train_years"] = " ".join(str(y) for y in scores.train_years)
    row["test_years"] = " ".join(str(y) for y in scores.test_years)
    return row


def _write(target: str, models: list[str], table: pd.DataFrame) -> None:
    stem = f"{target}-{'+'.join(models)}"
    table.to_csv(RESULTS_DIR / f"{stem}.csv", index=False, float_format=FLOAT_FORMAT)
    (RESULTS_DIR / f"{stem}.meta.json").write_text(json.dumps(_metadata(), indent=2))
    print(table.to_string(index=False), file=sys.stderr)


def _metadata() -> dict:
    inputs = sorted(DATA_DIR.glob("*.csv")) + [FULL_SWE_PATH]
    return {
        "inputs_md5": {p.name: hashlib.md5(p.read_bytes()).hexdigest() for p in inputs},
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
