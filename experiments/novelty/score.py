"""Novelty of a test day: how many of its inputs sit outside the training range.

Tree models cannot extrapolate. A day whose inputs fall outside anything seen
in training is routed to the nearest leaf and answered with full confidence,
so counting out-of-range inputs per day is a cheap flag for "the model is
guessing here". Pure: no I/O, no model fitting.
"""

import numpy as np
import pandas as pd

DEFAULT_LOWER_QUANTILE = 0.05
DEFAULT_UPPER_QUANTILE = 0.95
OUTSIDE_SUFFIX = "_outside"
MINMAX_COUNT = "n_outside_minmax"
QUANTILE_COUNT = "n_outside_quantiles"


def feature_ranges(
    train: pd.DataFrame,
    features: list[str],
    lower_q: float = DEFAULT_LOWER_QUANTILE,
    upper_q: float = DEFAULT_UPPER_QUANTILE,
) -> pd.DataFrame:
    values = train[list(features)]
    return pd.DataFrame(
        {
            "min": values.min(),
            "max": values.max(),
            "q_low": values.quantile(lower_q),
            "q_high": values.quantile(upper_q),
        }
    )


def novelty_per_day(test: pd.DataFrame, ranges: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    beyond_minmax = _beyond(test, ranges, features, "min", "max")
    beyond_quantiles = _beyond(test, ranges, features, "q_low", "q_high")
    novelty = pd.DataFrame(index=test.index)
    novelty[MINMAX_COUNT] = beyond_minmax.sum(axis=1).astype(int)
    novelty[QUANTILE_COUNT] = beyond_quantiles.sum(axis=1).astype(int)
    for feature in features:
        novelty[outside_column(feature)] = beyond_minmax[feature]
    return novelty


def outside_column(feature: str) -> str:
    return f"{feature}{OUTSIDE_SUFFIX}"


def _beyond(test: pd.DataFrame, ranges: pd.DataFrame, features: list[str], low: str, high: str) -> pd.DataFrame:
    # NaN compares False on both sides, so a missing value is never "outside".
    values = test[list(features)]
    return (values.lt(ranges[low], axis=1)) | (values.gt(ranges[high], axis=1))


def error_vs_novelty(novelty: pd.DataFrame, actual: pd.Series, preds: np.ndarray) -> pd.DataFrame:
    daily = novelty.copy()
    daily["actual"] = np.asarray(actual, dtype=float)
    daily["pred"] = np.asarray(preds, dtype=float)
    daily["abs_error"] = np.abs(daily["actual"] - daily["pred"])
    return daily


def binned_error(daily: pd.DataFrame) -> pd.DataFrame:
    grouped = daily.groupby(MINMAX_COUNT)["abs_error"]
    return pd.DataFrame({"days": grouped.size(), "mae": grouped.mean()}).reset_index()


def outside_days_per_feature(novelty: pd.DataFrame, features: list[str]) -> pd.Series:
    counts = pd.Series({feature: int(novelty[outside_column(feature)].sum()) for feature in features})
    counts.name = "days_outside"
    return counts
