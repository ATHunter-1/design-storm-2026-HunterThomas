"""Analog years for water year 2026 from the period-of-record SWE and flow files.

Usage (from experiments/):
    .venv/bin/python -m analog.run --fetch   # network: refresh analog/data/*.csv and its README
    .venv/bin/python -m analog.run           # offline: analog/results/*.csv from the committed CSVs

Results: water-years.csv (every water year), analogs-2026.csv (top 5 by snowpack
shape), following-years.csv (the water year after each analog), the same two
with the four suspect May 2026 SWE readings masked (see data/README.md), and
.meta.json with input md5s, library versions, and the git commit.
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

from analog.fetch import FLOW_FILE, SWE_FILE, fetch_all
from analog.similarity import SHAPE_COLUMNS, analog_ranking, following_year, mask_days, water_year_table

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"
RESULTS_DIR = HERE / "results"
REFERENCE_YEAR = 2026
TOP_N = 5
SUSPECT_SWE_DATES = ["2026-05-12", "2026-05-13", "2026-05-14", "2026-05-15"]
WATER_YEARS_FILE = "water-years.csv"
ANALOGS_FILE = "analogs-2026.csv"
FOLLOWING_FILE = "following-years.csv"
ANALOGS_MASKED_FILE = "analogs-2026-masked.csv"
FOLLOWING_MASKED_FILE = "following-years-masked.csv"
META_FILE = ".meta.json"
FLOAT_FORMAT = "%.4f"


def main(argv: list[str] | None = None) -> int:
    args = _parse(argv)
    if args.fetch:
        fetch_all(DATA_DIR)
        return 0
    written = build_results(DATA_DIR, RESULTS_DIR)
    _print(written)
    return 0


def _parse(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--fetch", action="store_true")
    return parser.parse_args(argv)


def build_results(data_dir: Path, results_dir: Path) -> dict[str, pd.DataFrame]:
    swe = load_swe(data_dir / SWE_FILE)
    flow = load_flow(data_dir / FLOW_FILE)
    as_fetched = _rank(water_year_table(swe, flow))
    masked = _rank(water_year_table(mask_days(swe, SUSPECT_SWE_DATES), flow))
    written = {
        WATER_YEARS_FILE: as_fetched["table"],
        ANALOGS_FILE: as_fetched["analogs"],
        FOLLOWING_FILE: as_fetched["following"],
        ANALOGS_MASKED_FILE: masked["analogs"],
        FOLLOWING_MASKED_FILE: masked["following"],
    }
    _write(results_dir, written, data_dir)
    return written


def _rank(table: pd.DataFrame) -> dict[str, pd.DataFrame]:
    analogs = analog_ranking(table, REFERENCE_YEAR, SHAPE_COLUMNS).head(TOP_N)
    return {"table": table, "analogs": analogs, "following": following_year(table, list(analogs.index))}


def load_swe(path: Path) -> pd.Series:
    raw = pd.read_csv(path)
    index = pd.DatetimeIndex(pd.to_datetime(raw["DATE"]))
    return pd.Series(pd.to_numeric(raw["SWE"], errors="coerce").to_numpy(), index=index, name="SWE")


def load_flow(path: Path) -> pd.Series:
    raw = pd.read_csv(path)
    index = pd.DatetimeIndex(pd.to_datetime(raw["measDate"]))
    return pd.Series(pd.to_numeric(raw["Flow_CFS"], errors="coerce").to_numpy(), index=index, name="Flow_CFS")


def _write(results_dir: Path, written: dict[str, pd.DataFrame], data_dir: Path) -> None:
    results_dir.mkdir(exist_ok=True)
    for name, frame in written.items():
        frame.to_csv(results_dir / name, float_format=FLOAT_FORMAT)
    (results_dir / META_FILE).write_text(json.dumps(_metadata(data_dir), indent=2))


def _metadata(data_dir: Path) -> dict:
    return {
        "inputs_md5": {p.name: hashlib.md5(p.read_bytes()).hexdigest() for p in sorted(data_dir.glob("*.csv"))},
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


def _print(written: dict[str, pd.DataFrame]) -> None:
    for name in (ANALOGS_FILE, FOLLOWING_FILE, ANALOGS_MASKED_FILE, FOLLOWING_MASKED_FILE):
        print(f"\n{name}")
        print(written[name].to_string())


if __name__ == "__main__":
    sys.exit(main())
