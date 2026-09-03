import numpy as np
import pandas as pd

from drivers.episodes import RAIN, SNOWMELT, UNCLEAR, Detection, Episode, recall_by_driver


def _episode(day: int) -> Episode:
    date = pd.Timestamp("2024-05-01") + pd.Timedelta(days=day)
    return Episode(start=date, end=date, days=1, peak_value=4.0, peak_date=date)


def test_one_of_two_detected_gives_recall_half():
    detections = [
        (_episode(0), SNOWMELT, Detection(detected=True, lead=-2)),
        (_episode(5), SNOWMELT, Detection(detected=False, lead=None)),
    ]
    table = recall_by_driver(detections).set_index("driver")
    assert table.loc[SNOWMELT, "episodes"] == 2
    assert table.loc[SNOWMELT, "detected"] == 1
    assert np.isclose(table.loc[SNOWMELT, "recall"], 0.5)


def test_mean_lead_is_over_detected_episodes_only():
    detections = [
        (_episode(0), RAIN, Detection(detected=True, lead=-3)),
        (_episode(5), RAIN, Detection(detected=True, lead=1)),
        (_episode(9), RAIN, Detection(detected=False, lead=None)),
    ]
    table = recall_by_driver(detections).set_index("driver")
    assert np.isclose(table.loc[RAIN, "mean_lead"], -1.0)


def test_one_row_per_driver_in_fixed_order():
    detections = [
        (_episode(0), UNCLEAR, Detection(detected=False, lead=None)),
        (_episode(3), RAIN, Detection(detected=True, lead=0)),
        (_episode(6), SNOWMELT, Detection(detected=True, lead=-1)),
    ]
    table = recall_by_driver(detections)
    assert list(table["driver"]) == [SNOWMELT, RAIN, UNCLEAR]
    assert list(table.columns) == ["driver", "episodes", "detected", "recall", "mean_lead"]


def test_no_detections_gives_an_empty_table_with_columns():
    table = recall_by_driver([])
    assert table.empty
    assert list(table.columns) == ["driver", "episodes", "detected", "recall", "mean_lead"]
