"""Rolling-origin evaluation: train through year N, test on year N+1, for every N.

Usage (from experiments/):
    .venv/bin/python -m rolling.run                         # both targets, jake_full vs contested drop
    .venv/bin/python -m rolling.run --target TOC --labels jake_full drop:swe_7day drop:precip_7day
    .venv/bin/python -m rolling.run --models catboost

Results: rolling/results/<target>-<models>.csv (one row per label, model, test year)
and <target>-<models>.summary.csv, plus a .meta.json with input md5s and versions.
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

from ablation.frame import RECIPES, build_frame, load_sources
from ablation.run import DATA_DIR, _metadata
from ablation.scoring import TARGETS, anchored_rows
from rolling.evaluate import score_folds
from rolling.folds import rolling_origin_folds
from rolling.report import comparison_sets, results_table, summarise

RESULTS_DIR = Path(__file__).resolve().parent / "results"
DEFAULT_MODELS = ("rf_grid", "catboost")


def main(argv: list[str] | None = None) -> int:
    args = _parse(argv)
    sources = load_sources(DATA_DIR)
    for target in ([args.target] if args.target else list(TARGETS)):
        table = _evaluate_target(sources, target, args.labels, args.models)
        _write(target, args.models, table)
    return 0


def _parse(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", choices=list(TARGETS), default=None)
    parser.add_argument("--labels", nargs="+", default=None)
    parser.add_argument("--models", nargs="+", choices=["rf_grid", "catboost"], default=list(DEFAULT_MODELS))
    return parser.parse_args(argv)


def _evaluate_target(sources, target: str, labels, models) -> pd.DataFrame:
    frame = build_frame(sources, RECIPES[target])
    sets = comparison_sets(target, labels)
    anchor = list(sets["jake_full"]) if "jake_full" in sets else _union(sets)
    scores_by_run = {}
    for label, features in sets.items():
        folds = rolling_origin_folds(anchored_rows(frame, target, list(features), anchor))
        for model in models:
            print(f"{target} {model} {label}: {[f.test_year for f in folds]}", file=sys.stderr)
            scores_by_run[(label, model)] = score_folds(folds, TARGETS[target], list(features), model)
    return results_table(scores_by_run)


def _union(sets: dict[str, tuple[str, ...]]) -> list[str]:
    return list(dict.fromkeys(f for features in sets.values() for f in features))


def _write(target: str, models: list[str], table: pd.DataFrame) -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    stem = f"{target}-{'+'.join(models)}"
    table.to_csv(RESULTS_DIR / f"{stem}.csv", index=False, float_format="%.6f")
    summary = summarise(table)
    summary.to_csv(RESULTS_DIR / f"{stem}.summary.csv", index=False, float_format="%.6f")
    (RESULTS_DIR / f"{stem}.meta.json").write_text(json.dumps(_metadata(), indent=2))
    print(table.to_string(index=False), file=sys.stderr)
    print(summary.to_string(index=False), file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
