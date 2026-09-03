"""Fit one model on one feature set and score it the way Jake's notebooks do.

Splits are chronological (shuffle=False), seeds are fixed, and thread counts
are pinned so two runs on the same machine produce the same numbers.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_percentage_error, r2_score, root_mean_squared_error
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit, train_test_split

SEED = 42
THREADS = 4
GRID = {
    "n_estimators": [100, 200],
    "max_depth": [3, 5, 7],
    "min_samples_leaf": [5, 10, 20],
    "max_features": [1.0, "sqrt"],
}
CV_SPLITS = 5
CATBOOST_ITERATIONS = 1000
CATBOOST_LEARNING_RATE = 0.03
CATBOOST_DEPTH = 6
EMPHASIS_WEIGHT = 1.5


@dataclass(frozen=True)
class TargetSpec:
    name: str
    test_size: float
    rf_emphasis: float
    catboost_emphasis: float
    excursion_threshold: float
    excursion_is_above: bool

    def is_excursion(self, values: np.ndarray) -> np.ndarray:
        if self.excursion_is_above:
            return values > self.excursion_threshold
        return values < self.excursion_threshold


TARGETS = {
    "TOC": TargetSpec("TOC", test_size=0.5, rf_emphasis=3.0, catboost_emphasis=4.0,
                      excursion_threshold=3.0, excursion_is_above=True),
    "Alk": TargetSpec("Alk", test_size=0.45, rf_emphasis=60.0, catboost_emphasis=60.0,
                      excursion_threshold=60.0, excursion_is_above=False),
}


@dataclass(frozen=True)
class Scores:
    rows: int
    r2: float
    rmse: float
    mape: float
    excursion_recall: float
    excursion_precision: float
    cv_mean_r2: float | None = None
    cv_std_r2: float | None = None


def score_feature_set(
    frame: pd.DataFrame, spec: TargetSpec, features: list[str], model: str, anchor: list[str] | None = None
) -> Scores:
    df = anchored_rows(frame, spec.name, features, anchor)
    X, y = df[features], df[spec.name]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=spec.test_size, shuffle=False)
    fit = FITTERS[model]
    preds, cv = fit(X_train, y_train, X_test, spec)
    return _scores(y_test.to_numpy(), preds, spec, len(df), cv)


def anchored_rows(frame: pd.DataFrame, target: str, features: list[str], anchor: list[str] | None) -> pd.DataFrame:
    """Keep only days where every anchor feature is present, so each feature set
    trains and tests on the identical days and the split boundary never moves."""
    required = list(dict.fromkeys(features + (anchor or []) + [target]))
    return frame[required].dropna()


def _emphasis_weights(y: pd.Series, spec: TargetSpec, threshold: float) -> np.ndarray:
    beyond = y > threshold if spec.excursion_is_above else y < threshold
    return np.where(beyond, EMPHASIS_WEIGHT, 1.0)


def _fit_linear(X_train, y_train, X_test, spec):
    model = LinearRegression().fit(X_train, y_train)
    return model.predict(X_test), None


def _fit_rf_grid(X_train, y_train, X_test, spec):
    weights = _emphasis_weights(y_train, spec, spec.rf_emphasis)
    search = GridSearchCV(
        estimator=RandomForestRegressor(random_state=SEED),
        param_grid=GRID,
        cv=TimeSeriesSplit(n_splits=CV_SPLITS),
        n_jobs=THREADS,
        verbose=0,
    )
    search.fit(X_train, y_train, sample_weight=weights)
    best = search.best_index_
    cv = (search.cv_results_["mean_test_score"][best], search.cv_results_["std_test_score"][best])
    return search.best_estimator_.predict(X_test), cv


def _fit_catboost(X_train, y_train, X_test, spec):
    weights = _emphasis_weights(y_train, spec, spec.catboost_emphasis)
    model = CatBoostRegressor(
        iterations=CATBOOST_ITERATIONS,
        learning_rate=CATBOOST_LEARNING_RATE,
        depth=CATBOOST_DEPTH,
        loss_function="RMSE",
        random_state=SEED,
        thread_count=THREADS,
        verbose=0,
        allow_writing_files=False,
    )
    model.fit(X_train, y_train, sample_weight=weights)
    return model.predict(X_test), None


FITTERS = {"linear": _fit_linear, "rf_grid": _fit_rf_grid, "catboost": _fit_catboost}


def _scores(actual: np.ndarray, preds: np.ndarray, spec: TargetSpec, rows: int, cv) -> Scores:
    recall, precision = excursion_recall_precision(actual, preds, spec)
    return Scores(
        rows=rows,
        r2=float(r2_score(actual, preds)),
        rmse=float(root_mean_squared_error(actual, preds)),
        mape=float(mean_absolute_percentage_error(actual, preds)),
        excursion_recall=recall,
        excursion_precision=precision,
        cv_mean_r2=None if cv is None else float(cv[0]),
        cv_std_r2=None if cv is None else float(cv[1]),
    )


def excursion_recall_precision(actual: np.ndarray, preds: np.ndarray, spec: TargetSpec) -> tuple[float, float]:
    actual_beyond = spec.is_excursion(np.asarray(actual))
    pred_beyond = spec.is_excursion(np.asarray(preds))
    caught = np.sum(actual_beyond & pred_beyond)
    recall = float(caught / actual_beyond.sum()) if actual_beyond.sum() else float("nan")
    precision = float(caught / pred_beyond.sum()) if pred_beyond.sum() else float("nan")
    return recall, precision
