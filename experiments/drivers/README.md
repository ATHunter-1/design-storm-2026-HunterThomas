# Driver attribution

Groups consecutive TOC excursion days (above 3 mg/L) into episodes, labels each episode by its likely physical driver (snowmelt or rain), and reports per model how many episodes of each driver it caught and how early. Turns day-level "recall 0.82" into "caught N of M melt episodes and N of M rain episodes", and shows what a rain-driven (drought summer) excursion looks like to a model trained on snow years.

Built test-first on top of `ablation/` and `rolling/` (imports only; nothing there changes). TOC only: alkalinity is below 60 on 59% of days, which is a regime, not episodes.

## Run

From `experiments/`:

```
.venv/bin/python -m pytest drivers/tests -q     # 23 tests, pure functions only
.venv/bin/python -m drivers.run                  # rf_grid and catboost
.venv/bin/python -m drivers.run --models catboost
```

Fits Jake's grid-searched forest and CatBoost on each rolling-origin fold (train on years before N, test on year N), so the per-day predictions are the same ones `rolling/` scores. Results in `results/`: `episodes.csv` (one row per episode with driver, detection, and lead per model), `recall-by-driver.csv`, `coverage.csv` (raw excursion days per year and how many the anchored index misses), and `episodes.meta.json` (input md5s, versions, git commit). Two consecutive runs on 2026-08-28, and again on 2026-09-04 with the updated data, produced byte-identical CSVs.

## Definitions

Two frames are in play:

- **full**: `ablation.frame.build_frame` for TOC, 1115 rows, every engineered column, NaN where a source is missing.
- **anchored**: `ablation.scoring.anchored_rows` on Jake's ten TOC features, 856 rows. The only index with predictions; it drops whole days wherever any feature is missing and has no `flow_7day_avg`.

**Episodes** are found on the anchored index, over the fold test rows (2023 to 2026): a maximal run of consecutive calendar days with TOC above 3 mg/L. A missing calendar day ends an episode, so a gap in the scored index truncates or splits an episode (see Coverage). Each episode records start, end, days, peak value, and peak date.

**Driver labels** read the full frame over the episode's days plus the 7 days before its start (`LOOKBACK_DAYS`), skipping missing days:

- `snowmelt`: `swe_7day` is falling over the window (last non-NaN value below the first) and `flow_7day_avg` on the peak date is at or above the full-frame median.
- `rain`: `precip_7day` on any day in the window is at or above the full-frame 90th percentile (`RAIN_QUANTILE`) and flow on the peak date is below the median.
- `mixed`: both conditions hold. `unclear`: neither.

Because snowmelt needs flow at or above the median and rain needs it below, `mixed` cannot occur under this definition; flow is the tiebreaker. Kept as specified. The 2025-05-16 episode (SWE falling, a rain spike, low river) is the case that would have wanted it.

**Detection**: any prediction beyond 3 mg/L dated from 4 days before the episode's start (`DEFAULT_LEAD_DAYS`) to its end. Lead is the first such prediction date minus the start date, so negative means the model called it before the episode began.

## Episodes, run 2026-09-04 (Sep 4 data, 2-day TOC lags, Hoosier Pass SNOTEL)

| Start | End | Days | Peak (mg/L) | Peak date | Driver | Forest | CatBoost |
|---|---|---|---|---|---|---|---|
| 2023-05-14 | 2023-07-17 | 65 | 7.3 | 2023-05-19 | snowmelt | caught, +1 day | caught, +10 days |
| 2024-04-15 | 2024-06-07 | 54 | 6.4 | 2024-05-18 | snowmelt | caught, +5 days | caught, same day |
| 2024-08-28 | 2024-09-02 | 6 | 3.3 | 2024-08-28 | unclear | missed | missed |
| 2025-05-16 | 2025-05-17 | 2 | 3.1 | 2025-05-16 | rain | caught, -1 day | caught, -1 day |
| 2025-06-11 | 2025-06-11 | 1 | 3.1 | 2025-06-11 | snowmelt | caught, -4 days | caught, -4 days |

2026 had no TOC excursion days, so no episodes (and no 2026 row in `coverage.csv`).

## Recall by driver

| Model | Driver | Episodes | Caught | Recall | Mean lead (days) |
|---|---|---|---|---|---|
| Forest (rf_grid) | snowmelt | 3 | 3 | 1.00 | +0.7 |
| Forest (rf_grid) | rain | 1 | 1 | 1.00 | -1.0 |
| Forest (rf_grid) | unclear | 1 | 0 | 0.00 | |
| CatBoost | snowmelt | 3 | 3 | 1.00 | +2.0 |
| CatBoost | rain | 1 | 1 | 1.00 | -1.0 |
| CatBoost | unclear | 1 | 0 | 0.00 | |

## Coverage

Raw TOC excursion days come from `FoothillsInfluent.csv` (the `TOC` column of the full frame). The anchored index misses **54** of them in the test years:

| Year | Raw excursion days | On anchored index | Not covered |
|---|---|---|---|
| 2022 (training only) | 11 | 11 | 0 |
| 2023 | 70 | 65 | 5 (Aug 5 to 9) |
| 2024 | 109 | 60 | 49 (Jun 8 to Aug 27) |
| 2025 | 3 | 3 | 0 |

The 2024 gap is the USGS sonde: conductance and turbidity columns are absent on 48 to 54 of those 49 days, so every turbidity-family feature is NaN and anchoring drops the day. The 2024 melt episode's end date (Jun 7) is where the sonde record stops, not where TOC fell below 3; the raw series stays above 3 through late August, so 2024 was most likely one long episode from Apr 15 into September, and the "unclear" Aug 28 episode may be the tail of it rather than a separate event.

## Reading

- **Every melt episode is caught, usually a little late.** On the two big melt years the forest first crossed 3 mg/L one day into the 2023 episode and five days into 2024's; CatBoost ten days in and same-day. On a 54-day episode that still leaves weeks of warning, but the lead is built into the lagged features (now uniformly 2 days upstream for TOC) and the model spends it. The two short 2025 episodes were called one and four days early.
- **The one miss is the late-summer, no-snow episode.** 2024-08-28 to 09-02: SWE flat at zero, a rain signal (`precip_7day` 0.357, above the 90th percentile), on a river still above median flow, so the rule declines to name it. That is the shape a drought-summer excursion would take, and both models, trained on melt-shaped years, missed all six days of it. One episode is not a rate; it is the one example the record has.
- **Episode recall and day recall answer different questions.** `rolling/` reports 2023 day-level recall of 0.52 (forest) and 0.29 (CatBoost) because many of the 65 days were predicted below 3; the episode was still "caught" because at least one day crossed. The operator's sentence is the episode one ("the model will tell you the flush has started"); the day one says how much of the flush it tracks.
- **Drought summer, for the model:** with no melt, excursions would be short, rain-driven, on a low river. This record has one rain episode (two days, caught a day early by both models) and one unclear late-summer episode (missed by both). The useful next data is not another snow year but the rain-driven episodes of a dry year, captured as they happen.
