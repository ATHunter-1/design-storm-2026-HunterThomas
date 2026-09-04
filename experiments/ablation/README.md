# Feature ablation

Answers Jake's last notebook comment ("see if we can remove redundant features/simplify the model") without waiting for a new sensor. Every feature set is scored on the same days with the same seeds, so the only thing that varies between rows is the feature list.

## Run

From `experiments/`:

```
.venv/bin/python -m pytest ablation/tests -q       # 16 pure-function tests
.venv/bin/python -m ablation.run --check           # fit jake_full twice, assert identical
.venv/bin/python -m ablation.run                   # both targets, rf_grid and catboost
.venv/bin/python -m ablation.run --target Alk --models catboost
```

Results land in `results/<target>-<models>.csv` with a `.meta.json` beside it recording input md5s, library versions, and the git commit. Diff two CSVs to compare runs.

## What is held fixed

- **Pipeline:** `frame.py` reproduces the notebooks' joins, lags, and engineered columns. Since Jake's Sep 4 update: TOC lags everything upstream 2 days (NOAA 4); alkalinity keeps USGS and DWR at 4, NOAA at 6; SNOTEL (Hoosier Pass file, TOC only) at 2.
- **Rows:** every feature set is scored on the days where all of Jake's full feature set is present (`anchored_rows`). Without this, dropping a column with gaps changes which days survive `dropna`, the train/test boundary moves, and the delta is partly a different test set. The first unanchored run produced a spurious "3 features beat 10" result for TOC that vanished once rows were anchored.
- **Split, seeds, threads:** chronological 50/50 (TOC) and 55/45 (alkalinity), `random_state=42` everywhere, `TimeSeriesSplit(5)` grid search with Jake's grid, CatBoost with `thread_count=4`, no CatBoost log files.
- **Sample weights:** Jake's emphasis on excursion days (TOC above 3 for the forest, above 4 for CatBoost; alkalinity below 60 for both).

`--check` fits `jake_full` twice for both models and compares every score. Both targets pass on this machine.

## Scores

R^2, RMSE, MAPE on the test half, plus two operator-facing numbers computed at the excursion threshold (TOC 3 mg/L, alkalinity 60 mg/L): **excursion recall** (of test days actually beyond the threshold, how many the prediction also placed beyond it) and **excursion precision** (of predicted excursion days, how many were real).

## Results, run 2026-09-04 (Sep 4 data, 2-day TOC lags, Hoosier Pass SNOTEL)

Reproduction check first: `jake_full` matches the notebooks. Alkalinity forest 0.61, CatBoost 0.68, one-variable line 0.51. TOC forest 0.66, CatBoost 0.74. (The Aug 25 run on the original materials: Alk 0.68 / 0.71, TOC 0.56 / 0.65.)

### Alkalinity (8 features, 836 days)

| Feature set | Forest R^2 | CatBoost R^2 |
|---|---|---|
| jake_full | 0.61 | **0.68** |
| drop turb_3day | 0.64 | **0.71** |
| drop turb_flow | 0.64 | 0.71 |
| drop Dissolved_Oxygen_Mean | 0.64 | 0.68 |
| drop month_cos | 0.63 | 0.67 |
| drop flow_7day_avg | 0.63 | 0.62 |
| drop month_sin | **0.65** | 0.58 |
| drop pH_Median | 0.43 | 0.41 |
| drop Specific_Cond_Mean | 0.26 | 0.46 |
| no season (6) | 0.54 | 0.39 |
| chemistry only: cond, pH, DO (3) | 0.55 | 0.05 |
| cond + pH (2) | 0.36 | 0.05 |
| cond + season (3) | 0.31 | 0.13 |
| line on conductance alone (1) | 0.51 | |

Reading: unchanged in shape from the Aug 25 run. Conductance and pH are load-bearing for both models; remove either and the model collapses. Everything else is worth 0 to 5 points each, and one of `turb_flow` / `turb_3day` / DO can go for free (dropping either turbidity column now slightly *helps* both models). Going below six features costs a lot, and a tree model on two or three features does worse than a straight line on one, which is trees failing to extrapolate on a test half whose conductance range differs from training, not a statement about the features.

### TOC (10 features, 856 days)

| Feature set | Forest R^2 | CatBoost R^2 |
|---|---|---|
| jake_full | 0.66 | 0.74 |
| drop swe_7day | 0.68 | 0.65 |
| drop turb_3day | 0.66 | 0.73 |
| drop turb/cond | 0.67 | 0.71 |
| drop turb_flow | 0.63 | 0.70 |
| drop month_sin | 0.66 | 0.74 |
| drop month_cos | 0.66 | **0.76** |
| drop Specific_Cond_Mean | **0.70** | 0.66 |
| drop Turbidity_Max | 0.65 | 0.69 |
| drop Turbidity_Median | 0.65 | 0.72 |
| drop precip_7day | 0.25 | 0.53 |
| no season (8) | 0.62 | 0.72 |
| turb_flow, cond, swe (3) | 0.10 | 0.47 |
| turb_flow + season (3) | 0.37 | 0.54 |
| no turbidity family (5) | 0.51 | 0.46 |
| line on turb_flow alone (1) | 0.06 | |

Reading, and what changed with the 2-day lags:

- **The snowpack flip is largely gone.** On the Aug 25 run, dropping `swe_7day` moved the forest +14 and CatBoost -10; now it is +2.5 and -9. The dramatic disagreement was partly an artifact of the old mixed lags.
- **Rain is the new load-bearing feature.** Dropping `precip_7day` costs the forest 41 points (0.66 to 0.25) and CatBoost 21. At the 4-day lag the rain signal is carrying weight it did not carry at 6.
- **The turbidity family still collapses.** Any single member can go for a point or two; the five columns remain five views of one signal, and excursion recall sits at 0.76 to 0.82 in nearly every configuration.
- The baseline line on `turb_flow` improved from -0.25 to 0.06: still explaining nothing, no longer actively worse than the mean.

## What this says about "simplify"

- Alkalinity: eight to six features is free. Below that, not with trees.
- TOC: the turbidity family can still be collapsed without losing peak recall. The snowpack question has cooled (small, model-dependent effect); `precip_7day` has replaced it as the feature the models cannot spare.
- A single held-out half cannot settle the rest; `rolling/` scores the same questions per year.
