"""Rolling-origin folds: train on every year before N, test on year N. Pure."""

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class Fold:
    test_year: int
    train_years: tuple[int, ...]
    train: pd.DataFrame
    test: pd.DataFrame


def rolling_origin_folds(frame: pd.DataFrame) -> list[Fold]:
    years = sorted(frame.index.year.unique())
    return [_fold(frame, test_year, tuple(y for y in years if y < test_year)) for test_year in years[1:]]


def _fold(frame: pd.DataFrame, test_year: int, train_years: tuple[int, ...]) -> Fold:
    year = frame.index.year
    return Fold(
        test_year=test_year,
        train_years=train_years,
        train=frame[year < test_year],
        test=frame[year == test_year],
    )
