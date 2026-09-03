import numpy as np
import pandas as pd

from novelty.run import TargetResults, evaluate_target


def _frame():
    days = pd.DatetimeIndex(
        [d for y in (2022, 2023, 2024) for d in pd.date_range(f"{y}-04-01", f"{y}-04-30", freq="D")]
    )
    x = np.arange(len(days), dtype=float)
    return pd.DataFrame({"x": x, "TOC": 2.0 + 0.01 * x}, index=days)


def test_evaluate_target_yields_daily_binned_and_feature_tables_per_fold_and_model():
    results = evaluate_target(_frame(), "TOC", ["x"], ("linear",))
    assert isinstance(results, TargetResults)
    assert results.daily.groupby(["test_year", "model"]).size().to_dict() == {(2023, "linear"): 30, (2024, "linear"): 30}
    assert list(results.daily.columns[:3]) == ["date", "test_year", "model"]
    assert set(results.binned.columns) == {"test_year", "model", "n_outside_minmax", "days", "mae"}
    assert results.binned["days"].sum() == 60
    assert results.features.set_index(["test_year", "feature"])["days_outside"].to_dict() == {(2023, "x"): 30, (2024, "x"): 30}
    assert results.features["test_days"].tolist() == [30, 30]
