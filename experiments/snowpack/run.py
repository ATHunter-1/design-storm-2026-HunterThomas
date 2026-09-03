"""Water-year snowpack table and wet/dry labels for data/MichiganCreek.csv.

Usage (from experiments/):
    .venv/bin/python -m snowpack.run

Prints the summary and writes snowpack/results/wateryear.csv. The reference
median is the in-kit fallback (median April 1 SWE of the years in the file);
the period-of-record median comes from the analog-years exploration.
"""

import sys
from pathlib import Path

import pandas as pd

from snowpack.wateryear import DRY_BELOW_FRACTION, summarise_by_water_year, wet_or_dry

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE.parent.parent / "data"
RESULTS_DIR = HERE / "results"
SNOTEL_FILE = "MichiganCreek.csv"
DATE_FORMAT = "%m/%d/%Y"


def main() -> int:
    swe = load_swe(DATA_DIR / SNOTEL_FILE)
    summary = summarise_by_water_year(swe)
    reference_median = summary["april1_swe"].median()
    table = with_labels(summary, reference_median)
    _write(table)
    _print(table, reference_median)
    return 0


def load_swe(path: Path) -> pd.Series:
    raw = pd.read_csv(path)
    dates = pd.DatetimeIndex(pd.to_datetime(raw["DATE"], format=DATE_FORMAT))
    return pd.Series(pd.to_numeric(raw["SWE"], errors="coerce").to_numpy(), index=dates, name="SWE")


def with_labels(summary: pd.DataFrame, reference_median: float) -> pd.DataFrame:
    table = summary.copy()
    table["fraction_of_median"] = table["april1_swe"] / reference_median
    table["label"] = wet_or_dry(summary, reference_median)
    return table


def _write(table: pd.DataFrame) -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    table.to_csv(RESULTS_DIR / "wateryear.csv", float_format="%.4f", date_format="%Y-%m-%d")


def _print(table: pd.DataFrame, reference_median: float) -> None:
    print(table.to_string())
    print(f"\nreference_median (in-kit fallback, median April 1 SWE): {reference_median:.2f} in")
    print(f"dry below {DRY_BELOW_FRACTION:.2f} x median = {DRY_BELOW_FRACTION * reference_median:.2f} in")


if __name__ == "__main__":
    sys.exit(main())
