import numpy as np
import pandas as pd

from analog.similarity import water_year_table


def _daily(start: str, values: list[float]) -> pd.Series:
    index = pd.date_range(start, periods=len(values), freq="D")
    return pd.Series(values, index=index, dtype=float)


def _synthetic_swe(water_year: int, peak_day_offset: int, peak: float, meltout_offset: int) -> pd.Series:
    start = pd.Timestamp(year=water_year - 1, month=10, day=1)
    days = 365
    values = np.zeros(days)
    values[peak_day_offset:meltout_offset] = peak
    return pd.Series(values, index=pd.date_range(start, periods=days, freq="D"))


def test_peak_on_november_first_is_day_31_of_the_water_year():
    swe = _synthetic_swe(2001, peak_day_offset=31, peak=5.0, meltout_offset=40)
    flow = _daily("2000-10-01", [1.0] * 365)
    table = water_year_table(swe, flow)
    assert table.loc[2001, "peak_day_of_water_year"] == 31
    assert table.loc[2001, "peak_swe"] == 5.0
    assert table.loc[2001, "days_peak_to_meltout"] == 9


def test_flow_columns_come_from_the_same_water_year():
    swe = _synthetic_swe(2001, peak_day_offset=31, peak=5.0, meltout_offset=40)
    flow_values = [10.0] * 365
    flow_values[100] = 200.0
    flow = _daily("2000-10-01", flow_values)
    table = water_year_table(swe, flow)
    assert table.loc[2001, "flow_max"] == 200.0
    assert table.loc[2001, "flow_max_day_of_water_year"] == 100
    assert abs(table.loc[2001, "flow_mean"] - (10.0 * 364 + 200.0) / 365) < 1e-9


from analog.similarity import DISTANCE, analog_ranking, following_year, mask_days


def _shape_table() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "peak_swe": [12.0, 9.0, 4.9, 4.9, 15.0],
            "peak_day_of_water_year": [200, 190, 167, 167, 210],
            "days_peak_to_meltout": [40, 30, 27, 27, 50],
            "flow_max": [1000.0, 800.0, 400.0, 420.0, 1300.0],
        },
        index=pd.Index([2001, 2002, 2003, 2026, 2027], name="water_year"),
    )


def test_exact_copy_of_reference_ranks_first_with_distance_zero():
    ranking = analog_ranking(_shape_table(), 2026, list(SHAPE))
    assert ranking.index[0] == 2003
    assert ranking.iloc[0][DISTANCE] == 0.0
    assert ranking.loc[2003, "peak_swe"] == 4.9
    assert ranking[DISTANCE].is_monotonic_increasing


def test_reference_year_is_never_listed():
    ranking = analog_ranking(_shape_table(), 2026, list(SHAPE))
    assert 2026 not in ranking.index
    assert set(ranking.index) == {2001, 2002, 2003, 2027}


def test_years_missing_a_ranking_column_are_left_out():
    table = _shape_table()
    table.loc[2002, "days_peak_to_meltout"] = np.nan
    ranking = analog_ranking(table, 2026, list(SHAPE))
    assert 2002 not in ranking.index


def test_following_year_is_nan_after_the_last_year():
    table = _shape_table()
    result = following_year(table, [2001, 2027])
    assert result.loc[2001, "following_water_year"] == 2002
    assert result.loc[2001, "peak_swe"] == 9.0
    assert result.loc[2027, "following_water_year"] == 2028
    assert np.isnan(result.loc[2027, "peak_swe"])
    assert np.isnan(result.loc[2027, "flow_max"])


def test_mask_days_blanks_only_the_named_dates():
    swe = _daily("2026-05-10", [0.0, 0.0, 9.0, 9.0, 9.0, 9.0, 0.0])
    masked = mask_days(swe, ["2026-05-12", "2026-05-13", "2026-05-14", "2026-05-15"])
    assert masked.isna().sum() == 4
    assert masked["2026-05-11"] == 0.0
    assert swe["2026-05-12"] == 9.0


SHAPE = ("peak_swe", "peak_day_of_water_year", "days_peak_to_meltout")
