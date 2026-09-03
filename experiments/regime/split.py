"""Regime folds: train on the wet water years and test on the dry ones, and the
reverse. Pure. Labels come from snowpack.wateryear.wet_or_dry; this module never
decides what wet or dry means, it only splits rows by an existing label.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_percentage_error, r2_score, root_mean_squared_error

from ablation.scoring import FITTERS, TargetSpec, excursion_recall_precision
from snowpack.wateryear import assign_water_year

WET = "wet"
DRY = "dry"
DIRECTIONS = ((WET, DRY), (DRY, WET))


@dataclass(frozen=True)
class RegimeFold:
    train_regime: str
    test_regime: str
    train_years: tuple[int, ...]
    test_years: tuple[int, ...]
    excluded_rows: int
    train: pd.DataFrame
    test: pd.DataFrame


@dataclass(frozen=True)
class RegimeScores:
    train_regime: str
    test_regime: str
    train_years: tuple[int, ...]
    test_years: tuple[int, ...]
    excluded_rows: int
    train_rows: int
    test_rows: int
    excursion_days: int
    r2: float
    rmse: float
    mape: float
    excursion_recall: float
    excursion_precision: float


def regime_folds(frame: pd.DataFrame, labels: pd.Series) -> list[RegimeFold]:
    row_labels = assign_water_year(frame.index).map(labels)
    excluded = int(row_labels.isna().sum())
    return [_fold(frame, row_labels, train, test, excluded) for train, test in DIRECTIONS]


def _fold(frame: pd.DataFrame, row_labels: pd.Series, train: str, test: str, excluded: int) -> RegimeFold:
    train_rows = frame[(row_labels == train).to_numpy()]
    test_rows = frame[(row_labels == test).to_numpy()]
    return RegimeFold(
        train_regime=train,
        test_regime=test,
        train_years=_years(train_rows),
        test_years=_years(test_rows),
        excluded_rows=excluded,
        train=train_rows,
        test=test_rows,
    )


def _years(rows: pd.DataFrame) -> tuple[int, ...]:
    return tuple(int(y) for y in sorted(assign_water_year(rows.index).unique()))


def score_regime_fold(fold: RegimeFold, spec: TargetSpec, features: list[str], model: str) -> RegimeScores:
    X_train, y_train = fold.train[features], fold.train[spec.name]
    X_test, y_test = fold.test[features], fold.test[spec.name]
    preds, _ = FITTERS[model](X_train, y_train, X_test, spec)
    return _scores(fold, y_test.to_numpy(), preds, spec)


def _scores(fold: RegimeFold, actual: np.ndarray, preds: np.ndarray, spec: TargetSpec) -> RegimeScores:
    recall, precision = excursion_recall_precision(actual, preds, spec)
    return RegimeScores(
        train_regime=fold.train_regime,
        test_regime=fold.test_regime,
        train_years=fold.train_years,
        test_years=fold.test_years,
        excluded_rows=fold.excluded_rows,
        train_rows=len(fold.train),
        test_rows=len(fold.test),
        excursion_days=int(spec.is_excursion(actual).sum()),
        r2=float(r2_score(actual, preds)),
        rmse=float(root_mean_squared_error(actual, preds)),
        mape=float(mean_absolute_percentage_error(actual, preds)),
        excursion_recall=recall,
        excursion_precision=precision,
    )
