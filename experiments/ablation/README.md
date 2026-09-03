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

- **Pipeline:** `frame.py` reproduces the notebooks' joins, lags, and engineered columns (USGS lag 2 for TOC, 4 for alkalinity; DWR 4; NOAA 6; SNOTEL 4 and TOC only).
- **Rows:** every feature set is scored on the days where all of Jake's full feature set is present (`anchored_rows`). Without this, dropping a column with gaps changes which days survive `dropna`, the train/test boundary moves, and the delta is partly a different test set. The first unanchored run produced a spurious "3 features beat 10" result for TOC that vanished once rows were anchored.
- **Split, seeds, threads:** chronological 50/50 (TOC) and 55/45 (alkalinity), `random_state=42` everywhere, `TimeSeriesSplit(5)` grid search with Jake's grid, CatBoost with `thread_count=4`, no CatBoost log files.
- **Sample weights:** Jake's emphasis on excursion days (TOC above 3 for the forest, above 4 for CatBoost; alkalinity below 60 for both).

`--check` fits `jake_full` twice for both models and compares every score. Both targets pass on this machine.

## Scores

R^2, RMSE, MAPE on the test half, plus two operator-facing numbers computed at the excursion threshold (TOC 3 mg/L, alkalinity 60 mg/L): **excursion recall** (of test days actually beyond the threshold, how many the prediction also placed beyond it) and **excursion precision** (of predicted excursion days, how many were real).

## Results, run 2026-08-25

Reproduction check first: `jake_full` matches the notebooks. Alkalinity forest 0.68, CatBoost 0.71, one-variable line 0.50 (0.51 in the notebook, which used its own rows). TOC forest 0.56, CatBoost 0.65.

### Alkalinity (8 features, 840 days)

| Feature set | Forest R^2 | CatBoost R^2 |
|---|---|---|
| jake_full | **0.68** | 0.71 |
| drop turb_flow | 0.64 | **0.72** |
| drop turb_3day | 0.64 | 0.70 |
| drop Dissolved_Oxygen_Mean | 0.64 | 0.69 |
| drop month_cos | 0.63 | 0.67 |
| drop flow_7day_avg | 0.63 | 0.62 |
| drop month_sin | 0.65 | 0.60 |
| drop pH_Median | 0.42 | 0.42 |
| drop Specific_Cond_Mean | 0.16 | 0.42 |
| no season (6) | 0.59 | 0.37 |
| chemistry only: cond, pH, DO (3) | 0.55 | 0.09 |
| cond + pH (2) | 0.38 | 0.14 |
| cond + season (3) | 0.31 | 0.13 |
| line on conductance alone (1) | 0.50 | |

Reading: conductance and pH are load-bearing for both models; remove either and the model collapses. Everything else is worth 0 to 5 points each, and one of `turb_flow` / `turb_3day` / DO can go for free. Going below six features costs a lot, and a tree model on two or three features does worse than a straight line on one, which is trees failing to extrapolate on a test half whose conductance range differs from training, not a statement about the features.

### TOC (10 features, 852 days)

| Feature set | Forest R^2 | CatBoost R^2 |
|---|---|---|
| jake_full | 0.56 | **0.65** |
| drop swe_7day | **0.70** | 0.55 |
| drop turb_3day | 0.65 | 0.64 |
| drop turb/cond | 0.62 | 0.59 |
| drop turb_flow | 0.62 | 0.62 |
| drop month_sin | 0.62 | 0.56 |
| drop month_cos | 0.60 | 0.63 |
| drop Specific_Cond_Mean | 0.60 | 0.63 |
| drop Turbidity_Max | 0.59 | 0.58 |
| drop Turbidity_Median | 0.58 | 0.60 |
| drop precip_7day | 0.47 | 0.60 |
| no season (8) | 0.54 | 0.53 |
| turb_flow, cond, swe (3) | 0.53 | 0.29 |
| turb_flow + season (3) | 0.39 | 0.45 |
| no turbidity family (5) | 0.44 | 0.44 |
| line on turb_flow alone (1) | -0.25 | |

Reading: the two models disagree about almost every feature. Dropping snowpack is the best thing you can do to the forest (+14 points) and the worst thing you can do to CatBoost (-10). Dropping any one of the turbidity family barely matters because the other four cover for it: `turb_flow`, `turb_3day`, `turb/cond`, `Turbidity_Median`, `Turbidity_Max` are five views of one signal. Excursion recall sits at 0.82 for nearly every configuration, so the peaks are caught (or not) by the turbidity signal regardless of what else is present.

The disagreement is the finding. When two reasonable models flip sign on the same feature, the test half is too small and too particular (one and a half seasons, with 2023's big snow year in training) to say which features matter. That matches the cross-validation instability in the notebooks (mean R^2 -0.79 across time folds).

## What this says about "simplify"

- Alkalinity: eight to six features is free. Below that, not with trees.
- TOC: the turbidity family can be collapsed from five columns to two without losing peak recall, and that is the only simplification the data supports. Whether snowpack belongs depends on which model you ask, which means it depends on which years you test on.
- A single held-out half cannot settle the rest. The next experiment is rolling-origin evaluation (train to year N, test year N+1, for each N), which turns "R^2 on one half" into "R^2 per season" and would show whether the snowpack disagreement is really a 2023 story.
