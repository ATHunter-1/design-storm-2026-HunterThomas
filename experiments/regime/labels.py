"""Reference median and wet/dry labels for the in-kit water years. Pure.

The reference is the period-of-record median April 1 SWE at Michigan Creek
(exploration-notes section 9). When the long record is missing or too short,
the in-kit median stands in and the table says so on every row.
"""

from dataclasses import dataclass

import pandas as pd

from snowpack.wateryear import wet_or_dry

MIN_REFERENCE_YEARS = 20
APRIL_1_COLUMN = "april1_swe"


@dataclass(frozen=True)
class Reference:
    median: float
    years: int
    fallback_used: bool


def reference_from(
    full_summary: pd.DataFrame | None, kit_summary: pd.DataFrame, minimum_years: int = MIN_REFERENCE_YEARS
) -> Reference:
    if _april_1_years(full_summary) >= minimum_years:
        return _reference(full_summary, fallback_used=False)
    return _reference(kit_summary, fallback_used=True)


def _april_1_years(summary: pd.DataFrame | None) -> int:
    return 0 if summary is None else int(summary[APRIL_1_COLUMN].notna().sum())


def _reference(summary: pd.DataFrame, fallback_used: bool) -> Reference:
    values = summary[APRIL_1_COLUMN].dropna()
    return Reference(median=float(values.median()), years=len(values), fallback_used=fallback_used)


def labels_table(summary: pd.DataFrame, reference: Reference) -> pd.DataFrame:
    table = summary[[APRIL_1_COLUMN, "days_with_data"]].copy()
    table.insert(1, "fraction_of_reference", table[APRIL_1_COLUMN] / reference.median)
    table.insert(2, "label", wet_or_dry(summary, reference.median).reindex(summary.index))
    table["reference_median"] = reference.median
    table["reference_years"] = reference.years
    table["fallback_used"] = reference.fallback_used
    return table
