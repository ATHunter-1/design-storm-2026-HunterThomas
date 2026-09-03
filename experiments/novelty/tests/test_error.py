import numpy as np
import pandas as pd

from novelty.score import binned_error, error_vs_novelty, feature_ranges, novelty_per_day, outside_days_per_feature


def _novelty():
    train = pd.DataFrame({"a": np.arange(11, dtype=float)}, index=pd.date_range("2022-04-01", periods=11, freq="D"))
    test = pd.DataFrame({"a": [12.0, 5.0, -1.0, 6.0]}, index=pd.date_range("2023-04-01", periods=4, freq="D"))
    return novelty_per_day(test, feature_ranges(train, ["a"]), ["a"])


def test_error_vs_novelty_has_one_row_per_test_day_with_actual_pred_abs_error():
    novelty = _novelty()
    actual = pd.Series([2.0, 3.0, 4.0, 5.0], index=novelty.index)
    daily = error_vs_novelty(novelty, actual, np.array([2.5, 3.0, 3.0, 5.5]))
    assert len(daily) == 4
    assert list(daily.index) == list(novelty.index)
    assert daily["n_outside_minmax"].tolist() == [1, 0, 1, 0]
    assert daily["actual"].tolist() == [2.0, 3.0, 4.0, 5.0]
    assert daily["pred"].tolist() == [2.5, 3.0, 3.0, 5.5]
    assert np.allclose(daily["abs_error"], [0.5, 0.0, 1.0, 0.5])


def test_binned_error_has_one_row_per_distinct_count_and_days_sum_to_test_days():
    novelty = _novelty()
    actual = pd.Series([2.0, 3.0, 4.0, 5.0], index=novelty.index)
    binned = binned_error(error_vs_novelty(novelty, actual, np.array([2.5, 3.0, 3.0, 5.5])))
    assert binned["n_outside_minmax"].tolist() == [0, 1]
    assert binned["days"].tolist() == [2, 2]
    assert binned["days"].sum() == len(novelty)
    assert np.allclose(binned["mae"], [0.25, 0.75])


def test_outside_days_per_feature_counts_test_days_beyond_training_range():
    counts = outside_days_per_feature(_novelty(), ["a"])
    assert counts.tolist() == [2]
    assert list(counts.index) == ["a"]
