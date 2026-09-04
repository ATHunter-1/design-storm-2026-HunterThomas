# Design Storm experiments: running Jake's notebooks locally

Runnable copies of Jake Slawson's notebooks (originals in `../scripts`, untouched). Built 2026-08-25; re-run 2026-09-04 against his Sep 4 update (data through Aug 19, TOC lags at 2 days, Hoosier Pass SNOTEL data in place of Michigan Creek).

## Run it

```
uv venv --python 3.13 .venv
uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python patch_notebooks.py
.venv/bin/jupyter nbconvert --to notebook --execute --ExecutePreprocessor.timeout=1800 TOC_SoftSensor.ipynb --output-dir runs
```

Same `nbconvert` line for the other five notebooks. Executed copies with outputs land in `runs/` (gitignored, regenerable). Figures land in `figures/`, fresh API pulls in `fresh-data/`.

## What `patch_notebooks.py` changes

Three edits, nothing else:

1. Hardcoded OneDrive paths become relative paths. `../data` for Jake's CSVs, `fresh-data/` for new API pulls, `figures/` for plots.
2. The `truststore` cells are removed. They exist for Denver Water's corporate TLS interception and fail elsewhere.
3. In the two model notebooks, cells 1-5 are replaced by one cell. Jake's version builds the target series from two internal lab exports (`PL-FTH-INF_cleaned.csv`, `PL-FTH-HW_cleaned.csv`) that were not shared. `FoothillsInfluent.csv` is the output of that step, so it is loaded directly. The replacement cell reads SNOTEL from `../data/HoosierPass.csv`, the file Jake shipped; his notebook reads a `BuckskinJoe.csv` that was not in the zip (see Reproduction check).

Kernel name is normalised to `python3` (Jake's carry his conda kernel name).

## Reproduction check

**Against the Aug 25 materials** (checked 2026-08-25): six of fourteen figures byte-identical (both alkalinity prediction comparisons, alkalinity correlation matrix, alkalinity feature and permutation importance, the TOC CatBoost comparison); the other eight differed only where scikit-learn's random forest is involved, which is version-sensitive. The joins, features, and CatBoost runs reproduced exactly.

**Against the Sep 4 update** (checked 2026-09-04): none of the eleven figures match, and the reasons are informative rather than alarming.

- Jake's Sep 4 TOC notebook fetches and reads Buckskin Joe SNOTEL (station 938), but the zip ships `HoosierPass.csv`, whose values match station 531 on the NRCS feed and differ from Buckskin Joe on every day. Our runs use the shipped file. A control run of the patched TOC notebook against a fresh Buckskin Joe pull (2026-09-04, endDate 2026-08-19 as in his grabber) also matches none of his six TOC figures, including the CatBoost comparison that matched byte-for-byte on Aug 25, so his figure run used a data state that differs from both the shipped CSV and a fresh pull. Which station (and which snapshot) the model is on now is a question for Jake.
- Jake's Sep 4 alkalinity regression figures are byte-identical to his Aug 25 ones (only the classification-performance figure changed), so they predate the data refresh; ours are built on the refreshed data.

Fresh API pulls (2026-09-04): DWR flow matches the shipped CSV on every overlapping value (formatting differs: ISO dates, trailing `.0`); NOAA has 8 revised values plus extra trailing days; a fresh Buckskin Joe pull is in `fresh-data/BuckskinJoe.csv` for the station comparison. All endpoints still work without keys (the update zip carries Jake's `waterdata_api.env` with a USGS key; the USGS pull works without it).

## Results, as run 2026-09-04 (Sep 4 data, 2-day TOC lags, Hoosier Pass SNOTEL)

Test set is the chronologically last half of the data (`shuffle=False`).

**TOC** (target: mg/L at Foothills influent)

| Model | Test R^2 | Test RMSE | Test MAPE |
|---|---|---|---|
| Linear, `turb_flow` only (baseline) | | 0.63 | |
| Random forest, grid search | 0.66 | 0.38 | 10.7% |
| Random forest, fixed 45/10/45 split | -0.28 | 0.30 | 10.6% |
| CatBoost | **0.74** | **0.33** | 10.8% |

Both headline models improved over the Aug 25 run (forest 0.56 to 0.66, CatBoost 0.65 to 0.74); the changes in between are the 2-day lags, the Hoosier Pass snowpack series, and three more weeks of quiet data in the test half. Cross-validation mean R^2 for the forest was -0.66 with std 0.66: still unstable across time folds, so the single test-split number remains fragile. Feature importance: `turb_flow` 34%, `swe_7day` 17%, `Specific_Cond_Mean` 15%.

**Alkalinity** (target: mg/L)

| Model | Test R^2 | Test RMSE | Test MAPE |
|---|---|---|---|
| Linear, `Specific_Cond_Mean` only (baseline) | | 6.30 | |
| Random forest, grid search | 0.61 | 5.76 | 7.8% |
| CatBoost | **0.68** | **5.20** | 7.2% |

Both slipped a little from the Aug 25 run (0.68 and 0.71); the alkalinity notebook's lags did not change, so this is the data refresh alone. Feature importance: `Specific_Cond_Mean` 33%, `pH_Median` 29%.

**Alkalinity classifier** (below 60 mg/L, yes or no; 58% of all days are below)

| | Predicted high | Predicted low |
|---|---|---|
| Actual high (225) | 205 | 20 false alarms |
| Actual low (152) | 60 missed | 92 caught |

Accuracy 79%, precision 82%, recall 61%. The 2026 season plot (`figures/AlkalinityClassificationPerformance_limit.png`) still shows the late-July run where the model predicted low and the water was high.

## Things noticed in the code

- **The lag is not uniformly four days, and Jake now says not to lean on four.** As of the Sep 4 update the TOC notebook shifts USGS, SNOTEL, and DWR by 2 days and rain by 4; alkalinity keeps 4 and 6. His email: 2 days recently scored slightly better, the number is subject to change, transport itself is about 4 hours (raw water group), and a day-plus of warning is what operators need.
- ~~**The April filter removes January to March of every year.**~~ Fixed in the Sep 4 update: now `index >= '2022-04-01'`, a real date cutoff.
- **The target is a blend of two sampling points.** Jake's original concatenates the influent (`PL-FTH-INF`) and headworks (`PL-FTH-HW`) series and takes the daily median. `FoothillsInfluent.csv` is presumably that blend.
- **Day-of-year features are computed from the wrong frame.** `combined_df.index.dayofyear` is assigned into `combined_df_TOC` / `combined_df_alk`. Works today because the frames happen to align; fragile.
- **A turbidity model exists but was not sent.** Six `Turb*` figures dated Aug 24 and leftover "Foothills Influent Turb" plot labels in the TOC notebook.
- **The baseline matters.** For alkalinity a one-variable straight line gets R^2 0.51 and the forest gets 0.68, so the extra complexity earns about 17 points. For TOC the line is worse than predicting the mean on the test half (-0.14), so the nonlinearity is doing real work there.

## Layout

```
experiments/
  patch_notebooks.py     makes the runnable copies from ../scripts
  requirements.txt       pinned versions that ran
  *.ipynb                patched copies (regenerate with patch_notebooks.py)
  runs/                  executed notebooks with outputs (gitignored)
  figures/               plots from the model runs
  fresh-data/            CSVs pulled from the APIs on 2026-09-04
  ablation/              deterministic feature ablation (see its README)
  rolling/               rolling-origin (per-year) evaluation on top of ablation/
```
