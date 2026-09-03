import numpy as np
import pandas as pd

from ablation.scoring import anchored_rows

FRAME = pd.DataFrame({
    "a": [1.0, 2.0, 3.0, 4.0],
    "b": [1.0, np.nan, 3.0, 4.0],
    "y": [10.0, 20.0, 30.0, 40.0],
})


def test_without_anchor_rows_depend_on_chosen_features():
    assert len(anchored_rows(FRAME, "y", ["a"], None)) == 4
    assert len(anchored_rows(FRAME, "y", ["b"], None)) == 3


def test_with_anchor_every_feature_set_sees_the_same_rows():
    assert len(anchored_rows(FRAME, "y", ["a"], anchor=["a", "b"])) == 3
    assert len(anchored_rows(FRAME, "y", ["b"], anchor=["a", "b"])) == 3


def test_anchor_does_not_add_columns_beyond_what_is_needed():
    rows = anchored_rows(FRAME, "y", ["a"], anchor=["a", "b"])
    assert list(rows.columns) == ["a", "b", "y"]
