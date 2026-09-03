"""Period-of-record pulls for the analog-years exploration. The I/O lives here.

Modelled on Jake's SNTL_grabber.ipynb and DWR_gage_grabber.ipynb, with the
begin dates pushed back to the start of each record. Run via
`python -m analog.run --fetch`; the analysis itself reads the saved CSVs.
"""

from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import requests

SNOTEL_URL = "https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/data"
SNOTEL_PARAMS = {
    "stationTriplets": "937:CO:SNTL",
    "elements": "WTEQ",
    "duration": "DAILY",
    "beginDate": "1900-01-01",
    "endDate": "2026-09-30",
}
DWR_URL = "https://dwr.state.co.us/Rest/GET/api/v2/surfacewater/surfacewatertsday/"
PAGE_SIZE = 50000
DWR_PARAMS = {
    "format": "json",
    "dateFormat": "spaceSepToSeconds",
    "abbrev": "PLASPLCO",
    "min-measDate": "01-01-1900",
    "max-measDate": "09-30-2026",
    "pageSize": PAGE_SIZE,
}
DWR_MISSING_FLAG = -999
STREAMFLOW = "Streamflow"
SWE_FILE = "MichiganCreek_full.csv"
FLOW_FILE = "SouthPlatteFlow_full.csv"
README_FILE = "README.md"
TIMEOUT_SECONDS = 300
ARTIFACT_CHECK_DATES = [f"2026-05-{day:02d}" for day in range(10, 17)]


def fetch_all(data_dir: Path) -> None:
    swe = snotel_frame(_get_json(SNOTEL_URL, SNOTEL_PARAMS))
    flow = dwr_frame(_all_dwr_rows())
    data_dir.mkdir(parents=True, exist_ok=True)
    swe.to_csv(data_dir / SWE_FILE, index=False)
    flow.to_csv(data_dir / FLOW_FILE, index=False)
    (data_dir / README_FILE).write_text(data_readme_text(date.today().isoformat(), swe, flow))


def _get_json(url: str, params: dict):
    response = requests.get(url, params=params, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()


def _all_dwr_rows() -> list[dict]:
    rows: list[dict] = []
    page_index = 1
    while True:
        page = _get_json(DWR_URL, {**DWR_PARAMS, "pageIndex": page_index}).get("ResultList", [])
        rows.extend(page)
        if is_last_page(page):
            return rows
        page_index += 1


def is_last_page(page: list) -> bool:
    return len(page) < PAGE_SIZE


def snotel_frame(payload) -> pd.DataFrame:
    values = pd.DataFrame(payload[0]["data"][0]["values"])
    return pd.DataFrame({"DATE": values["date"], "SWE": pd.to_numeric(values["value"], errors="coerce")})


def dwr_frame(rows: list[dict]) -> pd.DataFrame:
    raw = pd.DataFrame(rows)
    flow = raw[raw["measType"] == STREAMFLOW].copy()
    flow["measDate"] = pd.to_datetime(flow["measDate"])
    flow["Flow_CFS"] = pd.to_numeric(flow["value"], errors="coerce").replace(DWR_MISSING_FLAG, np.nan)
    daily = flow.set_index("measDate")[["Flow_CFS"]].sort_index().asfreq("D")
    return pd.DataFrame({"measDate": daily.index.strftime("%Y-%m-%d"), "Flow_CFS": daily["Flow_CFS"].to_numpy()})


def data_readme_text(fetch_date: str, swe: pd.DataFrame, flow: pd.DataFrame) -> str:
    return "\n".join([
        "# Period-of-record pulls for the analog-years exploration",
        "",
        f"Fetched {fetch_date} by `python -m analog.run --fetch` (`analog/fetch.py`). No keys needed.",
        "",
        _swe_paragraph(swe),
        "",
        _flow_paragraph(flow),
        "",
        _artifact_paragraph(swe),
        "",
    ])


def _swe_paragraph(swe: pd.DataFrame) -> str:
    dates = pd.to_datetime(swe["DATE"])
    water_years = dates.dt.year.where(dates.dt.month < 10, dates.dt.year + 1).nunique()
    return (
        f"`{SWE_FILE}`: NRCS AWDB `{SNOTEL_URL}`, station `{SNOTEL_PARAMS['stationTriplets']}` "
        f"(Michigan Creek), element WTEQ, daily, `beginDate` {SNOTEL_PARAMS['beginDate']}, "
        f"`endDate` {SNOTEL_PARAMS['endDate']}. {len(swe)} rows, {swe['DATE'].iloc[0]} to {swe['DATE'].iloc[-1]}, "
        f"{water_years} water years, {int(swe['SWE'].isna().sum())} blank readings. "
        "Columns `DATE,SWE` as in Jake's `data/MichiganCreek.csv` (ISO dates, oldest first, as in `fresh-data/`). "
        "The service returned the whole record on the first try."
    )


def _flow_paragraph(flow: pd.DataFrame) -> str:
    return (
        f"`{FLOW_FILE}`: Colorado DWR `{DWR_URL}`, `abbrev` {DWR_PARAMS['abbrev']} (South Platte above "
        f"Strontia), `min-measDate` {DWR_PARAMS['min-measDate']}, `max-measDate` {DWR_PARAMS['max-measDate']}, "
        f"`pageSize` {PAGE_SIZE}, paged until a page came back short. `measType == Streamflow` only, "
        f"{DWR_MISSING_FLAG} flags blanked, reindexed to every calendar day as the notebook does. "
        f"{len(flow)} rows, {flow['measDate'].iloc[0]} to {flow['measDate'].iloc[-1]}, "
        f"{int(flow['Flow_CFS'].isna().sum())} blank days. Columns `measDate,Flow_CFS` as in `data/SouthPlatteFlow.csv`."
    )


def _artifact_paragraph(swe: pd.DataFrame) -> str:
    readings = swe.set_index("DATE")["SWE"].reindex(ARTIFACT_CHECK_DATES)
    listed = ", ".join(f"{day[5:]}: {value:g}" for day, value in readings.items())
    return (
        "Check on the four suspect May 2026 rows in Jake's kit file (exploration-notes section 7.1). "
        f"NRCS readings for {ARTIFACT_CHECK_DATES[0]} to {ARTIFACT_CHECK_DATES[-1]}: {listed}."
    )
