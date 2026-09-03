"""Which feature sets to compare, and how to tabulate the per-year scores. Pure."""

from dataclasses import asdict

import pandas as pd

from ablation.configs import JAKE_FEATURES, ablation_configs
from rolling.evaluate import FoldScores

CONTESTED_FEATURE = {"TOC": "swe_7day", "Alk": "turb_flow"}
KEY_COLUMNS = ["label", "model", "test_year"]


def comparison_sets(target: str, labels: list[str] | None = None) -> dict[str, tuple[str, ...]]:
    wanted = labels or ["jake_full", f"drop:{CONTESTED_FEATURE[target]}"]
    available = {c.label: c.features for c in ablation_configs(target, ("catboost",))}
    return {label: available[label] for label in wanted}


def results_table(scores_by_run: dict[tuple[str, str], list[FoldScores]]) -> pd.DataFrame:
    rows = [
        {"label": label, "model": model, **asdict(scores)}
        for (label, model), fold_scores in scores_by_run.items()
        for scores in fold_scores
    ]
    return pd.DataFrame(rows)[KEY_COLUMNS + [c for c in rows[0] if c not in KEY_COLUMNS]]


def summarise(table: pd.DataFrame) -> pd.DataFrame:
    grouped = table.groupby(["label", "model"], sort=False)
    summary = grouped.agg(
        years=("test_year", "count"),
        r2_mean=("r2", "mean"),
        r2_min=("r2", "min"),
        r2_max=("r2", "max"),
        rmse_mean=("rmse", "mean"),
        recall_mean=("excursion_recall", "mean"),
        precision_mean=("excursion_precision", "mean"),
    )
    return summary.reset_index()
