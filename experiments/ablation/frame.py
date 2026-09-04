"""Build the modelling frame exactly as Jake's notebooks do.

Every shift, join, and rolling window here mirrors TOC_SoftSensor.ipynb and
Alkalinity_Soft_Sensor.ipynb. The two notebooks differ in small ways (USGS lag,
whether SNOTEL is joined, which engineered columns exist), so each target has
its own recipe rather than a shared one with flags.
"""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

DAYS_IN_YEAR = 365
MONTHS_IN_YEAR = 12


@dataclass(frozen=True)
class Recipe:
    target: str
    usgs_lag_days: int
    dwr_lag_days: int
    precip_lag_days: int
    sntl_lag_days: int | None


RECIPES = {
    "TOC": Recipe(target="TOC", usgs_lag_days=2, dwr_lag_days=2, precip_lag_days=4, sntl_lag_days=2),
    "Alk": Recipe(target="Alk", usgs_lag_days=4, dwr_lag_days=4, precip_lag_days=6, sntl_lag_days=None),
}


@dataclass(frozen=True)
class Sources:
    foothills: pd.DataFrame
    usgs: pd.DataFrame
    dwr: pd.DataFrame
    precip: pd.DataFrame
    sntl: pd.DataFrame


def load_sources(data_dir: Path) -> Sources:
    return Sources(
        foothills=pd.read_csv(data_dir / "FoothillsInfluent.csv"),
        usgs=pd.read_csv(data_dir / "USGS_South_Platte.csv"),
        dwr=pd.read_csv(data_dir / "SouthPlatteTelemetry.csv"),
        precip=pd.read_csv(data_dir / "USC00058022.csv"),
        sntl=pd.read_csv(data_dir / "HoosierPass.csv"),
    )


def build_frame(sources: Sources, recipe: Recipe) -> pd.DataFrame:
    frame = _target_series(sources.foothills, recipe.target)
    frame = frame.join(_usgs_lagged(sources.usgs, recipe.usgs_lag_days), how="left")
    if recipe.sntl_lag_days is not None:
        frame = frame.join(_sntl_lagged(sources.sntl, recipe.sntl_lag_days), how="left")
    frame = frame.join(_dwr_lagged(sources.dwr, recipe.dwr_lag_days), how="left")
    frame = frame.join(_precip_lagged(sources.precip, recipe.precip_lag_days), how="left")
    frame = _add_month_encoding(frame)
    frame = frame.dropna(subset=[recipe.target]).copy()
    return _add_engineered_features(frame, recipe.target)


def _target_series(foothills: pd.DataFrame, target: str) -> pd.DataFrame:
    fth = foothills.copy()
    fth["DATE"] = pd.to_datetime(fth["DATE"])
    return (
        fth.set_index("DATE")
        .rename(columns={"TOC_mg_L": "TOC", "Alk_mg_L": "Alk"})[[target]]
        .sort_index()
    )


def _usgs_lagged(usgs: pd.DataFrame, lag_days: int) -> pd.DataFrame:
    df = usgs.copy()
    df["DATE"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)
    df = df.drop(columns="Date").set_index("DATE")
    return df.shift(lag_days, freq="D")


def _sntl_lagged(sntl: pd.DataFrame, lag_days: int) -> pd.DataFrame:
    df = sntl.copy()
    df["DATE"] = pd.to_datetime(df["DATE"])
    df = df.set_index("DATE")
    df["SWE"] = pd.to_numeric(df["SWE"], errors="coerce")
    return df.shift(lag_days, freq="D")


def _dwr_lagged(dwr: pd.DataFrame, lag_days: int) -> pd.DataFrame:
    df = dwr.copy()
    df["DATE"] = pd.to_datetime(df["Date"])
    df = df.drop(columns="Date").set_index("DATE")
    return df.shift(lag_days, freq="D")


def _precip_lagged(precip: pd.DataFrame, lag_days: int) -> pd.DataFrame:
    df = precip.copy()
    df["DATE"] = pd.to_datetime(df["DATE"])
    df = df.set_index("DATE")
    return df.shift(lag_days, freq="D")


def _add_month_encoding(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    frame["Month"] = frame.index.month
    month_radians = 2 * np.pi * (frame["Month"] - 1) / MONTHS_IN_YEAR
    frame["month_sin"] = np.sin(month_radians)
    frame["month_cos"] = np.cos(month_radians)
    return frame


def _add_engineered_features(frame: pd.DataFrame, target: str) -> pd.DataFrame:
    frame = _add_shared_features(frame)
    if target == "TOC":
        frame = _add_toc_only_features(frame)
    return frame


def _add_shared_features(frame: pd.DataFrame) -> pd.DataFrame:
    frame["flow_delta"] = frame["Flow_CFS"].diff()
    frame["flow_7day_avg"] = frame["Flow_CFS"].rolling(window=7).mean()
    frame["turb_3day"] = frame["Turbidity_Median"].rolling(window=3).mean()
    day_of_year = frame.index.dayofyear
    frame["doy_sin"] = np.sin(2 * np.pi * day_of_year / DAYS_IN_YEAR)
    frame["doy_cos"] = np.cos(2 * np.pi * day_of_year / DAYS_IN_YEAR)
    frame["turb_flow"] = frame["turb_3day"] * frame["flow_7day_avg"]
    frame["precip_7day"] = frame["PRCP"].rolling(window=7).mean()
    frame["precip_3day"] = frame["PRCP"].rolling(window=3).mean()
    return frame


def _add_toc_only_features(frame: pd.DataFrame) -> pd.DataFrame:
    frame["gage_ht_7day"] = frame["GageHeight_ft"].rolling(window=7).mean()
    frame["gage_ht_3day"] = frame["GageHeight_ft"].rolling(window=3).mean()
    frame["precip_daily_dwr"] = frame["Precip"].diff()
    frame["swe_7day"] = frame["SWE"].rolling(window=7).mean()
    frame["swe_3day"] = frame["SWE"].rolling(window=3).mean()
    frame["cond_7day"] = frame["Specific_Cond_Mean"].rolling(window=7).mean()
    frame["cond_3day"] = frame["Specific_Cond_Mean"].rolling(window=3).mean()
    frame["turb_cond"] = frame["Specific_Cond_Mean"] * frame["turb_3day"]
    frame["turb/cond"] = frame["Specific_Cond_Mean"] / frame["turb_3day"]
    return frame
