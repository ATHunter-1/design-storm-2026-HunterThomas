"""Score one feature set on each rolling-origin fold.

Reuses the ablation fitters (same seeds, grid, weights, thread counts) so a
per-year number here is directly comparable to the single-split number there.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_percentage_error, r2_score, root_mean_squared_error

from ablation.scoring import FITTERS, TargetSpec, excursion_recall_precision
from rolling.folds import Fold


@dataclass(frozen=True)
class FoldScores:
    test_year: int
    train_rows: int
    test_rows: int
    excursion_days: int
    r2: float
    rmse: float
    mape: float
    excursion_recall: float
    excursion_precision: float


def score_folds(folds: list[Fold], spec: TargetSpec, features: list[str], model: str) -> list[FoldScores]:
    return [score_fold(fold, spec, features, model) for fold in folds]


def score_fold(fold: Fold, spec: TargetSpec, features: list[str], model: str) -> FoldScores:
    X_train, y_train = fold.train[features], fold.train[spec.name]
    X_test, y_test = fold.test[features], fold.test[spec.name]
    preds, _ = FITTERS[model](X_train, y_train, X_test, spec)
    return _fold_scores(fold, y_test.to_numpy(), preds, spec)


def _fold_scores(fold: Fold, actual: np.ndarray, preds: np.ndarray, spec: TargetSpec) -> FoldScores:
    recall, precision = excursion_recall_precision(actual, preds, spec)
    return FoldScores(
        test_year=fold.test_year,
        train_rows=len(fold.train),
        test_rows=len(fold.test),
        excursion_days=int(spec.is_excursion(actual).sum()),
        r2=float(r2_score(actual, preds)),
        rmse=float(root_mean_squared_error(actual, preds)),
        mape=float(mean_absolute_percentage_error(actual, preds)),
        excursion_recall=recall,
        excursion_precision=precision,
    )
