from dataclasses import fields

import numpy as np
import pandas as pd

from ablation.scoring import TARGETS
from regime.split import RegimeScores, regime_folds, score_regime_fold
from rolling.evaluate import FoldScores


def _linear_frame() -> pd.DataFrame:
    days = pd.date_range("2022-10-01", "2026-08-31", freq="D")
    x = np.arange(len(days), dtype=float)
    return pd.DataFrame({"x": x, "TOC": 2.0 + 0.001 * x}, index=days)


def _labels() -> pd.Series:
    return pd.Series({2023: "wet", 2024: "wet", 2025: "dry", 2026: "dry"})


def test_regime_scores_has_fold_scores_fields_except_test_year_plus_regime_fields():
    fold_score_fields = {f.name for f in fields(FoldScores)} - {"test_year"}
    regime_fields = {"train_regime", "test_regime", "train_years", "test_years", "excluded_rows"}
    assert {f.name for f in fields(RegimeScores)} == fold_score_fields | regime_fields


def test_linear_fit_on_a_line_is_exact_and_carries_the_fold_description():
    fold = regime_folds(_linear_frame(), _labels())[0]
    scores = score_regime_fold(fold, TARGETS["TOC"], ["x"], "linear")
    assert isinstance(scores, RegimeScores)
    assert (scores.train_regime, scores.test_regime) == ("wet", "dry")
    assert scores.train_years == (2023, 2024)
    assert scores.test_years == (2025, 2026)
    assert scores.excluded_rows == 0
    assert scores.train_rows == len(fold.train)
    assert scores.test_rows == len(fold.test)
    assert np.isclose(scores.r2, 1.0)
    assert np.isclose(scores.rmse, 0.0, atol=1e-9)


def test_excursion_metrics_use_the_target_threshold():
    fold = regime_folds(_linear_frame(), _labels())[0]
    scores = score_regime_fold(fold, TARGETS["TOC"], ["x"], "linear")
    assert scores.excursion_days == int((fold.test["TOC"] > 3.0).sum())
    assert scores.excursion_days > 0
    assert np.isclose(scores.excursion_recall, 1.0)
    assert np.isclose(scores.excursion_precision, 1.0)
