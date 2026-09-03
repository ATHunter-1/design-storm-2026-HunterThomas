import numpy as np
import pandas as pd

from rolling.folds import Fold, rolling_origin_folds


def _frame(years):
    days = pd.DatetimeIndex([d for y in years for d in pd.date_range(f"{y}-04-01", f"{y}-09-30", freq="D")])
    return pd.DataFrame({"x": np.arange(len(days), dtype=float), "y": 1.0}, index=days)


def test_one_fold_per_year_after_the_first():
    folds = rolling_origin_folds(_frame([2022, 2023, 2024, 2025]))
    assert [f.test_year for f in folds] == [2023, 2024, 2025]


def test_train_is_strictly_before_test_year():
    folds = rolling_origin_folds(_frame([2022, 2023, 2024]))
    fold_2024 = folds[-1]
    assert fold_2024.train.index.max() < pd.Timestamp("2024-01-01")
    assert fold_2024.test.index.min() >= pd.Timestamp("2024-01-01")
    assert fold_2024.test.index.max() < pd.Timestamp("2025-01-01")


def test_train_grows_with_each_fold():
    folds = rolling_origin_folds(_frame([2022, 2023, 2024, 2025]))
    sizes = [len(f.train) for f in folds]
    assert sizes == sorted(sizes)
    assert sizes[0] < sizes[-1]


def test_folds_cover_every_row_exactly_once_as_test_after_first_year():
    frame = _frame([2022, 2023, 2024])
    folds = rolling_origin_folds(frame)
    tested = pd.concat([f.test for f in folds])
    assert len(tested) == len(frame[frame.index.year > 2022])


def test_fold_is_a_value_object():
    frame = _frame([2022, 2023])
    fold = rolling_origin_folds(frame)[0]
    assert isinstance(fold, Fold)
    assert fold.train_years == (2022,)
