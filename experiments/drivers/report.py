"""Tabulate episodes, per-model detections, and index coverage for run.py. Pure."""

from dataclasses import asdict

import pandas as pd

from drivers.episodes import RECALL_COLUMNS, Detection, Episode, beyond_threshold, recall_by_driver

EPISODE_COLUMNS = ["start", "end", "days", "peak_value", "peak_date", "driver"]
COVERAGE_COLUMNS = ["year", "raw_excursion_days", "on_anchored_index", "not_covered"]
DETECTION_FIELDS = ("detected", "lead")

DetectionsByModel = dict[str, list[Detection]]


def episode_table(found: list[Episode], labels: list[str], detections_by_model: DetectionsByModel) -> pd.DataFrame:
    rows = [
        {**asdict(episode), "driver": driver, **_detection_columns(i, detections_by_model)}
        for i, (episode, driver) in enumerate(zip(found, labels))
    ]
    table = pd.DataFrame(rows, columns=EPISODE_COLUMNS + _model_columns(detections_by_model))
    for model in detections_by_model:
        table[f"{model}_lead"] = table[f"{model}_lead"].astype("Int64")
    return table


def _detection_columns(i: int, detections_by_model: DetectionsByModel) -> dict:
    return {
        f"{model}_{field}": getattr(detections[i], field)
        for model, detections in detections_by_model.items()
        for field in DETECTION_FIELDS
    }


def _model_columns(detections_by_model: DetectionsByModel) -> list[str]:
    return [f"{model}_{field}" for model in detections_by_model for field in DETECTION_FIELDS]


def recall_table(found: list[Episode], labels: list[str], detections_by_model: DetectionsByModel) -> pd.DataFrame:
    blocks = [
        recall_by_driver(list(zip(found, labels, detections))).assign(model=model)
        for model, detections in detections_by_model.items()
    ]
    if not blocks:
        return pd.DataFrame(columns=["model", *RECALL_COLUMNS])
    return pd.concat(blocks, ignore_index=True)[["model", *RECALL_COLUMNS]]


def coverage_table(raw: pd.Series, anchored: pd.DatetimeIndex, threshold: float, above: bool) -> pd.DataFrame:
    beyond = raw[beyond_threshold(raw, threshold, above)]
    per_day = pd.DataFrame({"year": beyond.index.year, "covered": beyond.index.isin(anchored)})
    per_year = per_day.groupby("year")["covered"].agg(raw_excursion_days="count", on_anchored_index="sum")
    per_year["not_covered"] = per_year["raw_excursion_days"] - per_year["on_anchored_index"]
    return per_year.reset_index()[COVERAGE_COLUMNS]
