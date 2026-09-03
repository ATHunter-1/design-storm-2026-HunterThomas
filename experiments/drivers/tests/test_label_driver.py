import numpy as np
import pandas as pd

from drivers.episodes import (
    FLOW_COLUMN,
    PRECIP_COLUMN,
    RAIN,
    SNOWMELT,
    SWE_COLUMN,
    UNCLEAR,
    Episode,
    label_driver,
)

QUIET_DAYS = 100
FLOW_HIGH = 1000.0
PRECIP_SPIKE = 5.0
SWE_STEADY = 5.0


def _full_frame(start="2024-01-01"):
    """Flow ramps 100 to 200 and precip 0 to 1, so the median and the 90th
    percentile are real cut points and early-February days sit below both."""
    dates = pd.date_range(start, periods=QUIET_DAYS, freq="D")
    return pd.DataFrame(
        {
            SWE_COLUMN: SWE_STEADY,
            FLOW_COLUMN: np.linspace(100.0, 200.0, QUIET_DAYS),
            PRECIP_COLUMN: np.linspace(0.0, 1.0, QUIET_DAYS),
        },
        index=dates,
    )


def _episode(start, end, peak_date=None):
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    return Episode(start=start, end=end, days=(end - start).days + 1, peak_value=4.0, peak_date=peak_date or end)


def test_falling_swe_with_high_flow_is_snowmelt():
    full = _full_frame()
    window = slice("2024-02-03", "2024-02-12")
    full.loc[window, SWE_COLUMN] = np.linspace(10.0, 2.0, 10)
    full.loc["2024-02-12", FLOW_COLUMN] = FLOW_HIGH
    assert label_driver(_episode("2024-02-10", "2024-02-12"), full) == SNOWMELT


def test_rain_spike_with_low_flow_is_rain():
    full = _full_frame()
    full.loc["2024-02-08", PRECIP_COLUMN] = PRECIP_SPIKE
    assert label_driver(_episode("2024-02-10", "2024-02-12"), full) == RAIN


def test_nan_swe_day_in_window_still_labels_from_the_other_days():
    full = _full_frame()
    window = slice("2024-02-03", "2024-02-12")
    full.loc[window, SWE_COLUMN] = np.linspace(10.0, 2.0, 10)
    full.loc["2024-02-12", SWE_COLUMN] = np.nan
    full.loc["2024-02-12", FLOW_COLUMN] = FLOW_HIGH
    assert label_driver(_episode("2024-02-10", "2024-02-12"), full) == SNOWMELT


def test_steady_swe_and_no_rain_is_unclear():
    assert label_driver(_episode("2024-02-10", "2024-02-12"), _full_frame()) == UNCLEAR


def test_missing_calendar_days_in_the_window_are_skipped():
    full = _full_frame().drop(pd.date_range("2024-02-04", "2024-02-06"))
    window = slice("2024-02-03", "2024-02-12")
    full.loc[window, SWE_COLUMN] = np.linspace(10.0, 2.0, 7)
    full.loc["2024-02-12", FLOW_COLUMN] = FLOW_HIGH
    assert label_driver(_episode("2024-02-10", "2024-02-12"), full) == SNOWMELT
