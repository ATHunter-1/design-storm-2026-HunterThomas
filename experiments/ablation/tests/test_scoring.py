import numpy as np

from ablation.scoring import TARGETS, excursion_recall_precision


def test_toc_excursions_are_above_three():
    actual = np.array([2.0, 3.5, 4.0, 2.5])
    preds = np.array([2.0, 3.2, 2.9, 3.1])
    recall, precision = excursion_recall_precision(actual, preds, TARGETS["TOC"])
    assert recall == 0.5
    assert precision == 0.5


def test_alk_excursions_are_below_sixty():
    actual = np.array([55.0, 65.0, 58.0])
    preds = np.array([59.0, 59.0, 61.0])
    recall, precision = excursion_recall_precision(actual, preds, TARGETS["Alk"])
    assert recall == 0.5
    assert precision == 0.5


def test_no_actual_excursions_gives_nan_recall():
    actual = np.array([2.0, 2.0])
    preds = np.array([2.0, 2.0])
    recall, precision = excursion_recall_precision(actual, preds, TARGETS["TOC"])
    assert np.isnan(recall)
    assert np.isnan(precision)
