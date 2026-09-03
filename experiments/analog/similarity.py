"""Analog years: which past water years look like a given one. Pure functions.

Snowpack shape per water year comes from snowpack.wateryear; flow is grouped
by the same water year. Days are counted from October 1 of the water year's
preceding calendar year so peak timing can be compared across years.
"""

import numpy as np
import pandas as pd

from snowpack.wateryear import WATER_YEAR_START_MONTH, assign_water_year, summarise_by_water_year

SHAPE_COLUMNS = ("peak_swe", "peak_day_of_water_year", "days_peak_to_meltout")
SNOW_COLUMNS = ["peak_swe", "peak_day_of_water_year", "april1_swe", "days_peak_to_meltout", "days_with_data"]
FLOW_COLUMNS = ["flow_max", "flow_max_day_of_water_year", "flow_mean"]
DISTANCE = "distance"
FIRST_OF_MONTH = 1


def water_year_table(swe: pd.Series, flow: pd.Series) -> pd.DataFrame:
    snow = _snow_by_water_year(swe)
    river = _flow_by_water_year(flow)
    table = snow.join(river, how="outer").sort_index()
    table["days_with_data"] = table["days_with_data"].astype("Int64")
    table.index.name = "water_year"
    return table


def _snow_by_water_year(swe: pd.Series) -> pd.DataFrame:
    summary = summarise_by_water_year(swe)
    summary["peak_day_of_water_year"] = _day_of_water_year(summary["peak_date"], summary.index)
    return summary[SNOW_COLUMNS]


def _flow_by_water_year(flow: pd.Series) -> pd.DataFrame:
    ordered = flow.sort_index()
    groups = ordered.groupby(assign_water_year(ordered.index))
    peak_dates = groups.idxmax()
    table = pd.DataFrame({
        "flow_max": groups.max(),
        "flow_max_day_of_water_year": _day_of_water_year(peak_dates, peak_dates.index),
        "flow_mean": groups.mean(),
    })
    return table[FLOW_COLUMNS]


def _day_of_water_year(dates: pd.Series, water_years: pd.Index) -> pd.Series:
    starts = pd.Series(
        [_water_year_start(int(year)) for year in water_years], index=water_years, dtype="datetime64[ns]"
    )
    days = (pd.Series(dates.to_numpy(), index=water_years) - starts).dt.days
    return days.astype("Int64")


def _water_year_start(water_year: int) -> pd.Timestamp:
    return pd.Timestamp(year=water_year - 1, month=WATER_YEAR_START_MONTH, day=FIRST_OF_MONTH)


def analog_ranking(table: pd.DataFrame, reference_year: int, columns) -> pd.DataFrame:
    columns = list(columns)
    complete = table.dropna(subset=columns)
    scores = _z_scores(complete[columns].astype(float))
    distance = np.sqrt(((scores - scores.loc[reference_year]) ** 2).sum(axis=1))
    ranking = complete.drop(index=reference_year).copy()
    ranking.insert(0, DISTANCE, distance.drop(index=reference_year))
    return ranking.sort_values(DISTANCE, kind="stable")


def _z_scores(values: pd.DataFrame) -> pd.DataFrame:
    spread = values.std(ddof=0).replace(0.0, 1.0)
    return (values - values.mean()) / spread


def following_year(table: pd.DataFrame, years: list[int]) -> pd.DataFrame:
    next_years = [year + 1 for year in years]
    rows = table.reindex(next_years)
    rows.insert(0, "following_water_year", next_years)
    rows.index = pd.Index(years, name="analog_year")
    return rows


def mask_days(swe: pd.Series, dates) -> pd.Series:
    masked = swe.copy()
    masked[masked.index.isin(pd.to_datetime(list(dates)))] = np.nan
    return masked
