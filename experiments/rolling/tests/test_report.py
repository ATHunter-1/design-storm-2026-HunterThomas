import pandas as pd

from ablation.configs import JAKE_FEATURES
from rolling.evaluate import FoldScores
from rolling.report import comparison_sets, results_table, summarise


def _scores(year, r2):
    return FoldScores(year, 100, 50, 5, r2, 0.3, 0.1, 0.8, 0.6)


def test_default_comparison_pits_jake_full_against_the_contested_drop():
    sets = comparison_sets("TOC")
    assert sets["jake_full"] == tuple(JAKE_FEATURES["TOC"])
    assert sets["drop:swe_7day"] == tuple(f for f in JAKE_FEATURES["TOC"] if f != "swe_7day")


def test_alk_default_comparison_drops_turb_flow():
    sets = comparison_sets("Alk")
    assert "drop:turb_flow" in sets
    assert "turb_flow" not in sets["drop:turb_flow"]


def test_explicit_labels_override_the_default():
    sets = comparison_sets("TOC", labels=["drop:precip_7day"])
    assert list(sets) == ["drop:precip_7day"]


def test_results_table_has_one_row_per_config_model_year():
    table = results_table({("jake_full", "linear"): [_scores(2023, 0.5), _scores(2024, 0.7)]})
    assert len(table) == 2
    assert list(table.columns[:3]) == ["label", "model", "test_year"]
    assert table["r2"].tolist() == [0.5, 0.7]


def test_summary_gives_mean_and_spread_of_r2_per_config_and_model():
    table = results_table({
        ("jake_full", "linear"): [_scores(2023, 0.5), _scores(2024, 0.7)],
        ("drop:x", "linear"): [_scores(2023, 0.6), _scores(2024, 0.6)],
    })
    summary = summarise(table).set_index("label")
    assert summary.loc["jake_full", "r2_mean"] == 0.6
    assert summary.loc["drop:x", "r2_min"] == 0.6
    assert summary.loc["jake_full", "r2_min"] == 0.5
