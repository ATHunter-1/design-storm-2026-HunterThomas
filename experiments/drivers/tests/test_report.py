import pandas as pd

from drivers.episodes import RAIN, SNOWMELT, Detection, Episode
from drivers.report import coverage_table, episode_table, recall_table

MODELS = ("rf_grid", "catboost")


def _episode(day: int, days: int = 1) -> Episode:
    start = pd.Timestamp("2024-05-01") + pd.Timedelta(days=day)
    end = start + pd.Timedelta(days=days - 1)
    return Episode(start=start, end=end, days=days, peak_value=4.0, peak_date=end)


def _detections():
    return {
        "rf_grid": [Detection(True, -2), Detection(False, None)],
        "catboost": [Detection(True, 0), Detection(True, -1)],
    }


def test_episode_table_has_one_row_per_episode_with_driver_and_per_model_columns():
    found = [_episode(0, days=3), _episode(10)]
    table = episode_table(found, [SNOWMELT, RAIN], _detections())
    assert list(table.columns) == [
        "start", "end", "days", "peak_value", "peak_date", "driver",
        "rf_grid_detected", "rf_grid_lead", "catboost_detected", "catboost_lead",
    ]
    assert list(table["driver"]) == [SNOWMELT, RAIN]
    assert list(table["rf_grid_detected"]) == [True, False]
    assert table["rf_grid_lead"].tolist()[0] == -2
    assert pd.isna(table["rf_grid_lead"].tolist()[1])


def test_recall_table_stacks_one_block_per_model():
    found = [_episode(0), _episode(10)]
    table = recall_table(found, [SNOWMELT, SNOWMELT], _detections())
    assert list(table.columns) == ["model", "driver", "episodes", "detected", "recall", "mean_lead"]
    by_model = table.set_index("model")
    assert by_model.loc["rf_grid", "recall"] == 0.5
    assert by_model.loc["catboost", "recall"] == 1.0


def test_coverage_counts_raw_excursion_days_outside_the_anchored_index():
    raw = pd.Series(
        [4.0, 4.0, 2.0, 4.0, 4.0],
        index=pd.to_datetime(["2023-05-01", "2023-05-02", "2023-05-03", "2024-06-01", "2024-06-02"]),
    )
    anchored = pd.DatetimeIndex(["2023-05-01", "2024-06-01", "2024-06-02"])
    table = coverage_table(raw, anchored, 3.0, above=True).set_index("year")
    assert table.loc[2023].tolist() == [2, 1, 1]
    assert table.loc[2024].tolist() == [2, 2, 0]
    assert list(table.columns) == ["raw_excursion_days", "on_anchored_index", "not_covered"]
