# Design Storm experiments: running Jake's notebooks locally

Runnable copies of Jake Slawson's notebooks (originals in `../scripts`, untouched). Built 2026-08-25.

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
3. In the two model notebooks, cells 1-5 are replaced by one cell. Jake's version builds the target series from two internal lab exports (`PL-FTH-INF_cleaned.csv`, `PL-FTH-HW_cleaned.csv`) that were not shared. `FoothillsInfluent.csv` is the output of that step, so it is loaded directly.

Kernel name is normalised to `python3` (Jake's carry his conda kernel name).

## Reproduction check

Six of fourteen figures are byte-identical to the ones Jake sent (md5): both alkalinity prediction comparisons, alkalinity correlation matrix, alkalinity feature and permutation importance, and the TOC CatBoost comparison. The remaining eight differ only where scikit-learn's random forest is involved, which is version-sensitive. The joins, features, and CatBoost runs reproduce exactly.

Fresh API pulls (run 2026-08-25) match Jake's CSVs row for row apart from one extra day at the end of each series and one revised USGS reading. All four public endpoints work without keys.

## Results, as run 2026-08-25

Test set is the chronologically last half of the data (`shuffle=False`).

**TOC** (target: mg/L at Foothills influent)

| Model | Test R^2 | Test RMSE | Test MAPE |
|---|---|---|---|
| Linear, `turb_flow` only (baseline) | -0.14 | 0.69 | |
| Random forest, grid search | 0.56 | 0.43 | 12.8% |
| Random forest, fixed 45/10/45 split | -0.99 | 0.38 | 12.9% |
| CatBoost | **0.65** | **0.38** | 12.0% |

Cross-validation mean R^2 for the forest was -0.79 with std 0.62. The model does not generalise across time folds; the single test-split number is fragile. CatBoost feature importance: `turb_flow` 33%, `Specific_Cond_Mean` 17%, `swe_7day` 15%.

**Alkalinity** (target: mg/L)

| Model | Test R^2 | Test RMSE | Test MAPE |
|---|---|---|---|
| Linear, `Specific_Cond_Mean` only (baseline) | 0.51 | 6.29 | |
| Random forest, grid search | 0.68 | 5.20 | 7.0% |
| CatBoost | **0.71** | **5.00** | 6.8% |

CatBoost feature importance: `Specific_Cond_Mean` 33%, `pH_Median` 26%.

**Alkalinity classifier** (below 60 mg/L, yes or no; 59% of days are below)

| | Predicted high | Predicted low |
|---|---|---|
| Actual high (227) | 200 | 27 false alarms |
| Actual low (151) | 59 missed | 92 caught |

Accuracy 77%, precision 77%, recall 61%. The 2026 season plot (`figures/AlkalinityClassificationPerformance_limit.png`) shows a run of roughly three weeks in late July and early August where the model predicted low and the water was high.

## Things noticed in the code

- **The lag is not uniformly four days.** Alkalinity shifts USGS by 4 days. TOC shifts USGS by 2 (`usgs.shift(2, freq='D')`) under a comment that says four. Precipitation is shifted 6 in both. The deck's "four days ahead" is a simplification.
- **The April filter removes January to March of every year.** `(index.month >= 4) & (index.year >= 2022)` is commented "Trim to April 2022" but is not a date cutoff. In practice it changes little: the USGS sonde has almost no readings from December to March (the instrument is likely out of the river over winter), so winter would drop out at the join anyway. Still a latent bug if the sonde ever runs year-round.
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
  fresh-data/            CSVs pulled from the APIs on 2026-08-25
  ablation/              deterministic feature ablation (see its README)
  rolling/               rolling-origin (per-year) evaluation on top of ablation/
```
