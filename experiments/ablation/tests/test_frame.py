import numpy as np
import pandas as pd

from ablation.frame import RECIPES, Sources, build_frame

DAYS = pd.date_range("2023-04-01", periods=20, freq="D")


def _sources() -> Sources:
    n = len(DAYS)
    foothills = pd.DataFrame({"DATE": DAYS.strftime("%-m/%-d/%Y"), "TOC_mg_L": np.arange(n) * 0.1 + 2, "Alk_mg_L": 50 + np.arange(n)})
    usgs = pd.DataFrame({
        "Date": DAYS.strftime("%Y-%m-%d"), "site_no": 6707525,
        "Specific_Cond_Mean": 300 + np.arange(n), "Turbidity_Median": np.arange(n) * 1.0,
        "Turbidity_Max": np.arange(n) * 2.0, "pH_Median": 8.0, "Dissolved_Oxygen_Mean": 9.0,
    })
    dwr = pd.DataFrame({"Date": DAYS.strftime("%Y-%m-%d"), "Flow_CFS": 100 + np.arange(n) * 10.0,
                        "GageHeight_ft": 4.0, "Precip": np.cumsum(np.ones(n))})
    precip = pd.DataFrame({"STATION": "X", "DATE": DAYS.strftime("%Y-%m-%d"), "PRCP": 1.0, "SNOW": 0.0,
                           "TMAX": 70.0, "TMIN": 40.0})
    sntl = pd.DataFrame({"DATE": DAYS.strftime("%-m/%-d/%Y"), "SWE": np.arange(n) * 1.0})
    return Sources(foothills, usgs, dwr, precip, sntl)


def test_toc_recipe_lags_usgs_by_two_days():
    frame = build_frame(_sources(), RECIPES["TOC"])
    assert frame.loc["2023-04-05", "Specific_Cond_Mean"] == 300 + 2


def test_alk_recipe_lags_usgs_by_four_days_and_has_no_swe():
    frame = build_frame(_sources(), RECIPES["Alk"])
    assert frame.loc["2023-04-05", "Specific_Cond_Mean"] == 300 + 0
    assert "SWE" not in frame.columns


def test_dwr_and_precip_lags():
    frame = build_frame(_sources(), RECIPES["TOC"])
    assert frame.loc["2023-04-10", "Flow_CFS"] == 100 + 7 * 10
    assert np.isnan(frame.loc["2023-04-03", "PRCP"])
    assert frame.loc["2023-04-05", "PRCP"] == 1.0


def test_month_encoding_puts_january_at_zero_radians():
    frame = build_frame(_sources(), RECIPES["Alk"])
    assert np.allclose(frame["month_sin"].iloc[0], np.sin(2 * np.pi * 3 / 12))
    assert np.allclose(frame["month_cos"].iloc[0], np.cos(2 * np.pi * 3 / 12))


def test_turb_flow_is_three_day_turbidity_times_seven_day_flow():
    frame = build_frame(_sources(), RECIPES["Alk"])
    row = frame.loc["2023-04-15"]
    assert np.isclose(row["turb_flow"], row["turb_3day"] * row["flow_7day_avg"])


def test_toc_only_features_exist_only_for_toc():
    toc = build_frame(_sources(), RECIPES["TOC"])
    alk = build_frame(_sources(), RECIPES["Alk"])
    for col in ["swe_7day", "turb/cond", "cond_7day", "gage_ht_3day"]:
        assert col in toc.columns
        assert col not in alk.columns


def test_toc_recipe_lags_swe_by_two_days():
    frame = build_frame(_sources(), RECIPES["TOC"])
    assert frame.loc["2023-04-05", "SWE"] == 2.0


def test_alk_recipe_keeps_four_day_dwr_and_six_day_precip_lags():
    frame = build_frame(_sources(), RECIPES["Alk"])
    assert frame.loc["2023-04-10", "Flow_CFS"] == 100 + 5 * 10
    assert np.isnan(frame.loc["2023-04-05", "PRCP"])
    assert frame.loc["2023-04-07", "PRCP"] == 1.0
