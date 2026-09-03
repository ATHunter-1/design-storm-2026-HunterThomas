import numpy as np
import pandas as pd

from novelty.score import feature_ranges, novelty_per_day


def _train():
    days = pd.date_range("2022-04-01", periods=11, freq="D")
    return pd.DataFrame({"a": np.arange(11, dtype=float), "b": np.full(11, 3.0)}, index=days)


def _test(a_values):
    days = pd.date_range("2023-04-01", periods=len(a_values), freq="D")
    return pd.DataFrame({"a": a_values, "b": np.full(len(a_values), 3.0)}, index=days)


def test_feature_ranges_has_min_max_and_quantiles_per_feature():
    ranges = feature_ranges(_train(), ["a", "b"])
    assert list(ranges.index) == ["a", "b"]
    assert list(ranges.columns) == ["min", "max", "q_low", "q_high"]
    assert ranges.loc["a", "min"] == 0.0
    assert ranges.loc["a", "max"] == 10.0
    assert np.isclose(ranges.loc["a", "q_low"], 0.5)
    assert np.isclose(ranges.loc["a", "q_high"], 9.5)


def test_day_beyond_training_max_counts_as_outside():
    novelty = novelty_per_day(_test([12.0, 5.0]), feature_ranges(_train(), ["a", "b"]), ["a", "b"])
    assert list(novelty.index) == list(_test([12.0, 5.0]).index)
    assert novelty["n_outside_minmax"].tolist() == [1, 0]
    assert novelty["a_outside"].tolist() == [True, False]
    assert novelty["b_outside"].tolist() == [False, False]


def test_quantile_count_flags_days_inside_minmax_but_beyond_the_tails():
    novelty = novelty_per_day(_test([9.8, 5.0]), feature_ranges(_train(), ["a", "b"]), ["a", "b"])
    assert novelty["n_outside_minmax"].tolist() == [0, 0]
    assert novelty["n_outside_quantiles"].tolist() == [1, 0]


def test_nan_feature_value_is_not_counted_as_outside():
    novelty = novelty_per_day(_test([np.nan]), feature_ranges(_train(), ["a", "b"]), ["a", "b"])
    assert novelty["n_outside_minmax"].tolist() == [0]
    assert novelty["n_outside_quantiles"].tolist() == [0]
    assert novelty["a_outside"].tolist() == [False]
