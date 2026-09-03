# Period-of-record pulls for the analog-years exploration

Fetched 2026-08-28 by `python -m analog.run --fetch` (`analog/fetch.py`). No keys needed.

`MichiganCreek_full.csv`: NRCS AWDB `https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/data`, station `937:CO:SNTL` (Michigan Creek), element WTEQ, daily, `beginDate` 1900-01-01, `endDate` 2026-09-30. 10194 rows, 1998-09-30 to 2026-08-27, 29 water years, 1 blank readings. Columns `DATE,SWE` as in Jake's `data/MichiganCreek.csv` (ISO dates, oldest first, as in `fresh-data/`). The service returned the whole record on the first try.

`SouthPlatteFlow_full.csv`: Colorado DWR `https://dwr.state.co.us/Rest/GET/api/v2/surfacewater/surfacewatertsday/`, `abbrev` PLASPLCO (South Platte above Strontia), `min-measDate` 01-01-1900, `max-measDate` 09-30-2026, `pageSize` 50000, paged until a page came back short. `measType == Streamflow` only, -999 flags blanked, reindexed to every calendar day as the notebook does. 46260 rows, 1900-01-01 to 2026-08-27, 365 blank days. Columns `measDate,Flow_CFS` as in `data/SouthPlatteFlow.csv`.

Check on the four suspect May 2026 rows in Jake's kit file (exploration-notes section 7.1). NRCS readings for 2026-05-10 to 2026-05-16: 05-10: 0, 05-11: 0, 05-12: 9, 05-13: 9, 05-14: 9, 05-15: 9, 05-16: 0.
