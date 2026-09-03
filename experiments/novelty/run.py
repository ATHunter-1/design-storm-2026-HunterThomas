"""Novelty score: how far outside the training range each test day sits, and
whether prediction error rises with it.

Usage (from experiments/):
    .venv/bin/python -m novelty.run                     # both targets, jake_full, rf_grid + catboost
    .venv/bin/python -m novelty.run --target TOC
    .venv/bin/python -m novelty.run --models catboost
    .venv/bin/python -m novelty.run --replot             # redraw figures from the saved daily CSVs

Results per target in novelty/results/: <target>-daily.csv (one row per test
day per fold per model), <target>-binned.csv, <target>-features.csv (per fold,
per feature, the number of test days outside the training range), and a
.meta.json with input md5s, library versions, and the git commit. One figure
per target in novelty/figures/.
"""

import argparse
import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import catboost
import matplotlib
import numpy as np
import pandas as pd
import sklearn

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from ablation.configs import JAKE_FEATURES
from ablation.frame import RECIPES, build_frame, load_sources
from ablation.run import DATA_DIR
from ablation.scoring import FITTERS, TARGETS, anchored_rows
from novelty.score import (
    MINMAX_COUNT,
    QUANTILE_COUNT,
    binned_error,
    error_vs_novelty,
    feature_ranges,
    novelty_per_day,
    outside_days_per_feature,
)
from rolling.folds import Fold, rolling_origin_folds

HERE = Path(__file__).resolve().parent
RESULTS_DIR = HERE / "results"
FIGURES_DIR = HERE / "figures"
DEFAULT_MODELS = ("rf_grid", "catboost")
MODEL_MARKERS = {"rf_grid": "o", "catboost": "x", "linear": "^"}
PANEL_WIDTH_IN = 4.0
PANEL_HEIGHT_IN = 3.6
POINT_ALPHA = 0.6
JITTER_WIDTH = 0.15
FIGURE_DPI = 120
COUNT_COLUMNS = {
    MINMAX_COUNT: "features outside training min/max",
    QUANTILE_COUNT: "features beyond training 5th/95th percentile",
}


@dataclass(frozen=True)
class TargetResults:
    daily: pd.DataFrame
    binned: pd.DataFrame
    features: pd.DataFrame


def main(argv: list[str] | None = None) -> int:
    args = _parse(argv)
    sources = load_sources(DATA_DIR)
    for target in ([args.target] if args.target else list(TARGETS)):
        if args.replot:
            _replot(target)
            continue
        features = JAKE_FEATURES[target]
        rows = anchored_rows(build_frame(sources, RECIPES[target]), target, features, features)
        results = evaluate_target(rows, target, features, tuple(args.models))
        _write(target, results)
    return 0


def _parse(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", choices=list(TARGETS), default=None)
    parser.add_argument("--models", nargs="+", choices=list(FITTERS), default=list(DEFAULT_MODELS))
    parser.add_argument("--replot", action="store_true", help="redraw figures from results/*-daily.csv without refitting")
    return parser.parse_args(argv)


def evaluate_target(rows: pd.DataFrame, target: str, features: list[str], models: tuple[str, ...]) -> TargetResults:
    folds = rolling_origin_folds(rows)
    daily_tables, feature_tables = [], []
    for fold in folds:
        novelty = novelty_per_day(fold.test, feature_ranges(fold.train, features), features)
        feature_tables.append(_feature_table(fold, novelty, features))
        for model in models:
            print(f"{target} {model} test year {fold.test_year}", file=sys.stderr)
            daily_tables.append(_daily_table(fold, novelty, target, features, model))
    daily = pd.concat(daily_tables, ignore_index=True)
    return TargetResults(daily=daily, binned=_binned_table(daily), features=pd.concat(feature_tables, ignore_index=True))


def _daily_table(fold: Fold, novelty: pd.DataFrame, target: str, features: list[str], model: str) -> pd.DataFrame:
    preds, _ = FITTERS[model](fold.train[features], fold.train[target], fold.test[features], TARGETS[target])
    daily = error_vs_novelty(novelty, fold.test[target], preds)
    daily.insert(0, "model", model)
    daily.insert(0, "test_year", fold.test_year)
    return daily.rename_axis("date").reset_index()


def _binned_table(daily: pd.DataFrame) -> pd.DataFrame:
    binned = daily.groupby(["test_year", "model"], sort=True).apply(binned_error, include_groups=False)
    return binned.reset_index(level=[0, 1]).reset_index(drop=True)


def _feature_table(fold: Fold, novelty: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    counts = outside_days_per_feature(novelty, features).rename_axis("feature").reset_index()
    counts.insert(0, "test_year", fold.test_year)
    counts["test_days"] = len(fold.test)
    return counts


def _write(target: str, results: TargetResults) -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    FIGURES_DIR.mkdir(exist_ok=True)
    results.daily.to_csv(RESULTS_DIR / f"{target}-daily.csv", index=False, float_format="%.6f")
    results.binned.to_csv(RESULTS_DIR / f"{target}-binned.csv", index=False, float_format="%.6f")
    results.features.to_csv(RESULTS_DIR / f"{target}-features.csv", index=False)
    (RESULTS_DIR / f"{target}.meta.json").write_text(json.dumps(_metadata(), indent=2))
    _figure(results.daily, target).savefig(FIGURES_DIR / f"{target}-error-vs-novelty.png", dpi=FIGURE_DPI)
    print(results.binned.to_string(index=False), file=sys.stderr)


def _figure(daily: pd.DataFrame, target: str) -> plt.Figure:
    years = sorted(daily["test_year"].unique())
    fig, axes = plt.subplots(
        len(COUNT_COLUMNS), len(years), figsize=(PANEL_WIDTH_IN * len(years), PANEL_HEIGHT_IN * len(COUNT_COLUMNS)),
        sharey=True, squeeze=False,
    )
    for row, (column, label) in enumerate(COUNT_COLUMNS.items()):
        for ax, year in zip(axes[row], years):
            _panel(ax, daily[daily["test_year"] == year], year, column, label)
        axes[row][0].set_ylabel(f"absolute error ({target} mg/L)")
    fig.suptitle(f"{target}: prediction error against novelty of the day's inputs")
    fig.tight_layout()
    return fig


def _panel(ax, year_rows: pd.DataFrame, year: int, column: str, label: str) -> None:
    rng = np.random.default_rng(0)
    for model, rows in year_rows.groupby("model"):
        jitter = rng.uniform(-JITTER_WIDTH, JITTER_WIDTH, len(rows))
        ax.scatter(rows[column] + jitter, rows["abs_error"], marker=MODEL_MARKERS.get(model, "o"),
                   alpha=POINT_ALPHA, label=model)
    ax.set_xticks(range(int(year_rows[column].max()) + 1))
    ax.set_title(f"test year {year} ({len(year_rows) // year_rows['model'].nunique()} days)")
    ax.set_xlabel(label)
    ax.legend()


def _replot(target: str) -> None:
    daily = pd.read_csv(RESULTS_DIR / f"{target}-daily.csv")
    _figure(daily, target).savefig(FIGURES_DIR / f"{target}-error-vs-novelty.png", dpi=FIGURE_DPI)


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
