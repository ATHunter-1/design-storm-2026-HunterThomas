import numpy as np
import pandas as pd

from snowpack.wateryear import DRY_BELOW_FRACTION, assign_water_year, summarise_by_water_year, wet_or_dry


def test_october_to_december_belong_to_the_next_water_year():
    index = pd.DatetimeIndex(["2023-12-15", "2024-03-15"])
    assert assign_water_year(index).tolist() == [2024, 2024]


def _winter(start_year: int, peak_month_day: str, meltout_month_day: str) -> pd.Series:
    """Snow from November 1, linear rise to the peak, linear fall to zero, zero to September 30."""
    first_snow = pd.Timestamp(f"{start_year}-11-01")
    peak = pd.Timestamp(f"{start_year + 1}-{peak_month_day}")
    meltout = pd.Timestamp(f"{start_year + 1}-{meltout_month_day}")
    last = pd.Timestamp(f"{start_year + 1}-09-30")
    rise = pd.Series(np.linspace(0.5, 10.0, (peak - first_snow).days + 1), index=pd.date_range(first_snow, peak))
    fall = pd.Series(np.linspace(10.0, 0.0, (meltout - peak).days + 1), index=pd.date_range(peak, meltout))[1:]
    tail = pd.Series(0.0, index=pd.date_range(meltout, last))[1:]
    return pd.concat([rise, fall, tail])


def _two_winters() -> pd.Series:
    return pd.concat([_winter(2022, "04-10", "06-05"), _winter(2023, "04-20", "06-15")])


def test_one_row_per_water_year_with_peak_and_meltout_in_the_accumulation_year():
    summary = summarise_by_water_year(_two_winters())
    assert summary.index.tolist() == [2023, 2024]
    assert summary.loc[2023, "peak_date"] == pd.Timestamp("2023-04-10")
    assert summary.loc[2023, "meltout_date"] == pd.Timestamp("2023-06-05")
    assert summary.loc[2024, "peak_date"] == pd.Timestamp("2024-04-20")
    assert summary.loc[2024, "meltout_date"] == pd.Timestamp("2024-06-15")
    assert summary.loc[2023, "peak_swe"] == 10.0
    assert summary.loc[2023, "days_peak_to_meltout"] == 56
    assert summary.loc[2023, "days_with_data"] == len(_winter(2022, "04-10", "06-05"))


def test_descending_date_order_gives_an_identical_summary():
    ascending = _two_winters()
    descending = ascending.iloc[::-1]
    pd.testing.assert_frame_equal(summarise_by_water_year(descending), summarise_by_water_year(ascending))


def test_snow_present_on_december_31_is_never_a_meltout():
    series = _winter(2022, "04-10", "06-05")
    assert series[pd.Timestamp("2022-12-31")] > 0
    summary = summarise_by_water_year(series)
    assert summary["meltout_date"].tolist() == [pd.Timestamp("2023-06-05")]


def test_april1_swe_is_the_april_1_reading_when_present():
    series = _winter(2022, "04-10", "06-05")
    summary = summarise_by_water_year(series)
    assert summary.loc[2023, "april1_swe"] == series[pd.Timestamp("2023-04-01")]


def test_april1_swe_is_nan_when_there_is_no_april_1_reading():
    series = _winter(2022, "04-10", "06-05").drop(pd.Timestamp("2023-04-01"))
    summary = summarise_by_water_year(series)
    assert pd.isna(summary.loc[2023, "april1_swe"])


def test_meltout_is_nan_when_swe_never_reaches_zero_after_the_peak():
    series = _winter(2022, "04-10", "06-05")
    never_zero = series[series > 0]
    summary = summarise_by_water_year(never_zero)
    assert pd.isna(summary.loc[2023, "meltout_date"])
    assert pd.isna(summary.loc[2023, "days_peak_to_meltout"])
    assert summary.loc[2023, "peak_date"] == pd.Timestamp("2023-04-10")


def test_zero_readings_before_the_first_snow_are_not_a_meltout():
    october_bare = pd.Series(0.0, index=pd.date_range("2022-10-01", "2022-10-31"))
    series = pd.concat([october_bare, _winter(2022, "04-10", "06-05")])
    summary = summarise_by_water_year(series)
    assert summary.loc[2023, "meltout_date"] == pd.Timestamp("2023-06-05")


def _summary_with_april1(values: dict) -> pd.DataFrame:
    return pd.DataFrame({"april1_swe": pd.Series(values, dtype=float)})


def test_wet_or_dry_default_fraction_splits_at_75_percent_of_the_reference_median():
    summary = _summary_with_april1({2023: 7.4, 2024: 7.5, 2025: np.nan})
    labels = wet_or_dry(summary, reference_median=10)
    assert labels.to_dict() == {2023: "dry", 2024: "wet"}
    assert DRY_BELOW_FRACTION == 0.75


def test_wet_or_dry_honours_a_custom_fraction():
    summary = _summary_with_april1({2023: 8.9})
    labels = wet_or_dry(summary, reference_median=10, dry_below=0.9)
    assert labels.to_dict() == {2023: "dry"}


def test_a_water_year_with_no_numeric_readings_still_gets_a_row():
    winter = _winter(2022, "04-10", "06-05")
    blank_next_year = pd.Series(np.nan, index=pd.date_range("2023-10-01", "2023-10-31"))
    summary = summarise_by_water_year(pd.concat([winter, blank_next_year]))
    assert summary.index.tolist() == [2023, 2024]
    assert summary.loc[2024, "days_with_data"] == 0
    assert pd.isna(summary.loc[2024, "peak_swe"])
    assert pd.isna(summary.loc[2024, "peak_date"])
    assert pd.isna(summary.loc[2024, "meltout_date"])
