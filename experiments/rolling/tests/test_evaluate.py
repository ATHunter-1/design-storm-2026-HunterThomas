import numpy as np
import pandas as pd

from ablation.scoring import TARGETS
from rolling.evaluate import FoldScores, score_fold, score_folds
from rolling.folds import rolling_origin_folds


def _linear_frame():
    days = pd.DatetimeIndex(
        [d for y in (2022, 2023, 2024) for d in pd.date_range(f"{y}-04-01", f"{y}-06-30", freq="D")]
    )
    x = np.arange(len(days), dtype=float)
    return pd.DataFrame({"x": x, "TOC": 2.0 + 0.01 * x}, index=days)


def test_linear_fit_on_a_line_is_exact():
    fold = rolling_origin_folds(_linear_frame())[0]
    scores = score_fold(fold, TARGETS["TOC"], ["x"], "linear")
    assert isinstance(scores, FoldScores)
    assert scores.test_year == 2023
    assert scores.train_rows == 91
    assert scores.test_rows == 91
    assert np.isclose(scores.r2, 1.0)
    assert np.isclose(scores.rmse, 0.0, atol=1e-9)


def test_excursion_metrics_use_the_target_threshold():
    fold = rolling_origin_folds(_linear_frame())[1]
    scores = score_fold(fold, TARGETS["TOC"], ["x"], "linear")
    assert scores.excursion_days == int((fold.test["TOC"] > 3.0).sum())
    assert np.isclose(scores.excursion_recall, 1.0)


def test_score_folds_returns_one_result_per_fold_in_year_order():
    folds = rolling_origin_folds(_linear_frame())
    results = score_folds(folds, TARGETS["TOC"], ["x"], "linear")
    assert [r.test_year for r in results] == [2023, 2024]
