"""Group excursion days into episodes, label each by physical driver, score recall per driver. Pure.

Episodes live on the anchored index (the days the model was scored on). Driver
labels read the full unanchored frame, which still has `flow_7day_avg` and the
days that anchoring dropped.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

LOOKBACK_DAYS = 7
RAIN_QUANTILE = 0.90
DEFAULT_LEAD_DAYS = 4

SNOWMELT = "snowmelt"
RAIN = "rain"
MIXED = "mixed"
UNCLEAR = "unclear"
DRIVER_ORDER = (SNOWMELT, RAIN, MIXED, UNCLEAR)

SWE_COLUMN = "swe_7day"
FLOW_COLUMN = "flow_7day_avg"
PRECIP_COLUMN = "precip_7day"

ONE_DAY = pd.Timedelta(days=1)


@dataclass(frozen=True)
class Episode:
    start: pd.Timestamp
    end: pd.Timestamp
    days: int
    peak_value: float
    peak_date: pd.Timestamp


def episodes(actual: pd.Series, threshold: float, above: bool) -> list[Episode]:
    beyond = actual[beyond_threshold(actual, threshold, above)].sort_index()
    return [_episode(beyond.loc[run], above) for run in _consecutive_runs(beyond.index)]


def beyond_threshold(values: pd.Series, threshold: float, above: bool) -> pd.Series:
    return values > threshold if above else values < threshold


def _consecutive_runs(dates: pd.DatetimeIndex) -> list[pd.DatetimeIndex]:
    if len(dates) == 0:
        return []
    breaks = np.flatnonzero((dates[1:] - dates[:-1]) != ONE_DAY) + 1
    starts, ends = [0, *breaks], [*breaks, len(dates)]
    return [dates[a:b] for a, b in zip(starts, ends)]


@dataclass(frozen=True)
class DriverCuts:
    flow_median: float
    rain_spike: float


def label_driver(episode: Episode, full: pd.DataFrame) -> str:
    cuts = _driver_cuts(full)
    window = _lookback_window(episode, full)
    flow_high = _flow_at_peak(episode, full) >= cuts.flow_median
    melt = _is_falling(window[SWE_COLUMN]) and flow_high
    rain = _has_rain_spike(window[PRECIP_COLUMN], cuts.rain_spike) and not flow_high
    return _label(melt, rain)


def _driver_cuts(full: pd.DataFrame) -> DriverCuts:
    return DriverCuts(
        flow_median=float(full[FLOW_COLUMN].median()),
        rain_spike=float(full[PRECIP_COLUMN].quantile(RAIN_QUANTILE)),
    )


def _lookback_window(episode: Episode, full: pd.DataFrame) -> pd.DataFrame:
    return full.sort_index().loc[episode.start - LOOKBACK_DAYS * ONE_DAY : episode.end]


def _flow_at_peak(episode: Episode, full: pd.DataFrame) -> float:
    if episode.peak_date not in full.index:
        return float("nan")
    return float(full.at[episode.peak_date, FLOW_COLUMN])


def _is_falling(values: pd.Series) -> bool:
    present = values.dropna()
    return len(present) >= 2 and present.iloc[-1] < present.iloc[0]


def _has_rain_spike(values: pd.Series, spike: float) -> bool:
    present = values.dropna()
    return len(present) > 0 and float(present.max()) >= spike


def _label(melt: bool, rain: bool) -> str:
    if melt and rain:
        return MIXED
    if melt:
        return SNOWMELT
    if rain:
        return RAIN
    return UNCLEAR


@dataclass(frozen=True)
class Detection:
    detected: bool
    lead: int | None


def episode_detection(
    episode: Episode, preds: pd.Series, threshold: float, above: bool, lead_days: int = DEFAULT_LEAD_DAYS
) -> Detection:
    window = preds.sort_index().loc[episode.start - lead_days * ONE_DAY : episode.end]
    hits = window[beyond_threshold(window, threshold, above)]
    if hits.empty:
        return Detection(detected=False, lead=None)
    return Detection(detected=True, lead=int((hits.index[0] - episode.start).days))


RECALL_COLUMNS = ["driver", "episodes", "detected", "recall", "mean_lead"]


def recall_by_driver(detections: list[tuple[Episode, str, Detection]]) -> pd.DataFrame:
    by_driver: dict[str, list[Detection]] = {}
    for _, driver, detection in detections:
        by_driver.setdefault(driver, []).append(detection)
    rows = [_driver_row(driver, by_driver[driver]) for driver in sorted(by_driver, key=_driver_rank)]
    return pd.DataFrame(rows, columns=RECALL_COLUMNS)


def _driver_rank(driver: str) -> int:
    return DRIVER_ORDER.index(driver) if driver in DRIVER_ORDER else len(DRIVER_ORDER)


def _driver_row(driver: str, found: list[Detection]) -> dict:
    detected = [d for d in found if d.detected]
    return {
        "driver": driver,
        "episodes": len(found),
        "detected": len(detected),
        "recall": len(detected) / len(found),
        "mean_lead": float(np.mean([d.lead for d in detected])) if detected else float("nan"),
    }


def _episode(run: pd.Series, above: bool) -> Episode:
    peak_date = run.idxmax() if above else run.idxmin()
    return Episode(
        start=run.index[0],
        end=run.index[-1],
        days=len(run),
        peak_value=float(run[peak_date]),
        peak_date=peak_date,
    )
