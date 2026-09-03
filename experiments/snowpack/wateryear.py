"""Snowpack by water year (October 1 to September 30). Pure functions.

A calendar year splits one winter's snow in half: November snow melts the
following May. Grouping by water year keeps each winter with its own melt.
"""

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

WATER_YEAR_START_MONTH = 10
APRIL_FIRST = (4, 1)
DRY_BELOW_FRACTION = 0.75
NO_DATE = pd.NaT


@dataclass(frozen=True)
class WaterYearSummary:
    water_year: int
    peak_swe: float
    peak_date: pd.Timestamp
    april1_swe: float
    meltout_date: pd.Timestamp
    days_peak_to_meltout: float
    days_with_data: int


def assign_water_year(index: pd.DatetimeIndex) -> pd.Series:
    year = pd.Series(index.year, index=index)
    return year.where(index.month < WATER_YEAR_START_MONTH, year + 1)


def summarise_by_water_year(swe: pd.Series) -> pd.DataFrame:
    ordered = swe.sort_index()
    groups = ordered.groupby(assign_water_year(ordered.index))
    rows = [asdict(_summarise_one(water_year, readings)) for water_year, readings in groups]
    table = pd.DataFrame(rows).set_index("water_year")
    table["days_peak_to_meltout"] = table["days_peak_to_meltout"].astype("Int64")
    return table


def _summarise_one(water_year: int, readings: pd.Series) -> WaterYearSummary:
    if readings.notna().sum() == 0:
        return _empty_summary(water_year)
    peak_date = readings.idxmax()
    meltout_date = _first_zero_after(readings, peak_date)
    return WaterYearSummary(
        water_year=int(water_year),
        peak_swe=readings.max(),
        peak_date=peak_date,
        april1_swe=_april_first_reading(readings, water_year),
        meltout_date=meltout_date,
        days_peak_to_meltout=(meltout_date - peak_date).days if not pd.isna(meltout_date) else np.nan,
        days_with_data=int(readings.notna().sum()),
    )


def _april_first_reading(readings: pd.Series, water_year: int) -> float:
    month, day = APRIL_FIRST
    return readings.get(pd.Timestamp(year=water_year, month=month, day=day), np.nan)


def _empty_summary(water_year: int) -> WaterYearSummary:
    return WaterYearSummary(
        water_year=int(water_year),
        peak_swe=np.nan,
        peak_date=NO_DATE,
        april1_swe=np.nan,
        meltout_date=NO_DATE,
        days_peak_to_meltout=np.nan,
        days_with_data=0,
    )


def _first_zero_after(readings: pd.Series, peak_date: pd.Timestamp) -> pd.Timestamp:
    zeros = readings[(readings.index > peak_date) & (readings == 0)]
    return zeros.index[0] if len(zeros) else NO_DATE


def wet_or_dry(
    summary: pd.DataFrame,
    reference_median: float,
    dry_below: float = DRY_BELOW_FRACTION,
    column: str = "april1_swe",
) -> pd.Series:
    values = summary[column].dropna()
    is_dry = values < dry_below * reference_median
    return pd.Series(np.where(is_dry, "dry", "wet"), index=values.index, name="label")
