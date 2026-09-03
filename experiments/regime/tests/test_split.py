import numpy as np
import pandas as pd

from snowpack.wateryear import assign_water_year
from regime.split import RegimeFold, regime_folds


def _frame(start: str, end: str) -> pd.DataFrame:
    days = pd.date_range(start, end, freq="D")
    return pd.DataFrame({"x": np.arange(len(days), dtype=float), "TOC": 1.0}, index=days)


def _labels(mapping: dict[int, str]) -> pd.Series:
    return pd.Series(mapping, name="label")


TWO_WET_TWO_DRY = {2023: "wet", 2024: "wet", 2025: "dry", 2026: "dry"}


def test_returns_exactly_two_folds_wet_to_dry_then_dry_to_wet():
    folds = regime_folds(_frame("2022-10-01", "2026-08-31"), _labels(TWO_WET_TWO_DRY))
    assert len(folds) == 2
    assert [(f.train_regime, f.test_regime) for f in folds] == [("wet", "dry"), ("dry", "wet")]
    assert all(isinstance(f, RegimeFold) for f in folds)


def test_wet_trained_fold_tests_only_on_dry_water_years_including_october_to_december():
    frame = _frame("2022-10-01", "2026-08-31")
    wet_to_dry = regime_folds(frame, _labels(TWO_WET_TWO_DRY))[0]
    test_water_years = assign_water_year(wet_to_dry.test.index)
    assert set(test_water_years) == {2025, 2026}
    assert pd.Timestamp("2024-11-15") in wet_to_dry.test.index
    assert pd.Timestamp("2024-11-15") not in wet_to_dry.train.index
    assert set(assign_water_year(wet_to_dry.train.index)) == {2023, 2024}
    assert wet_to_dry.train_years == (2023, 2024)
    assert wet_to_dry.test_years == (2025, 2026)


def test_dry_trained_fold_tests_only_on_wet_water_years():
    frame = _frame("2022-10-01", "2026-08-31")
    dry_to_wet = regime_folds(frame, _labels(TWO_WET_TWO_DRY))[1]
    assert set(assign_water_year(dry_to_wet.test.index)) == {2023, 2024}
    assert set(assign_water_year(dry_to_wet.train.index)) == {2025, 2026}
    assert dry_to_wet.train_years == (2025, 2026)
    assert dry_to_wet.test_years == (2023, 2024)


def test_unlabelled_water_year_rows_are_in_neither_train_nor_test_and_are_counted():
    frame = _frame("2022-04-01", "2026-08-31")
    unlabelled = frame[assign_water_year(frame.index) == 2022]
    assert len(unlabelled) > 0
    for fold in regime_folds(frame, _labels(TWO_WET_TWO_DRY)):
        assert fold.excluded_rows == len(unlabelled)
        assert not fold.train.index.intersection(unlabelled.index).size
        assert not fold.test.index.intersection(unlabelled.index).size
        assert len(fold.train) + len(fold.test) + fold.excluded_rows == len(frame)


def test_years_with_a_label_but_no_rows_are_not_reported():
    frame = _frame("2022-10-01", "2024-09-30")
    fold = regime_folds(frame, _labels(TWO_WET_TWO_DRY))[0]
    assert fold.train_years == (2023, 2024)
    assert fold.test_years == ()
    assert len(fold.test) == 0
