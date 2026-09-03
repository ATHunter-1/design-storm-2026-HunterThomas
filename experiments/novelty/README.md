# Novelty score

For every test day in a rolling-origin fold, how many of the model's inputs sit outside the range it saw in training, and does prediction error rise with that count? If it does, the bad days are extrapolation and the out-of-range inputs are named. Motivation and the extrapolation argument: `../../exploration-notes.md` section 7.2.

Built test-first on top of `ablation/` and `rolling/` (imports only; changes nothing there). Same rows, folds, fitters, seeds, and grid as `rolling/`, so every prediction here is the one `rolling/` scored.

## Run

From `experiments/`:

```
.venv/bin/python -m pytest novelty/tests -q        # 8 tests, pure functions plus the fold loop on a toy frame
.venv/bin/python -m novelty.run                    # both targets, jake_full, rf_grid + catboost
.venv/bin/python -m novelty.run --target TOC --models catboost
.venv/bin/python -m novelty.run --replot           # redraw figures from results/*-daily.csv, no refit
```

Two full runs produced byte-identical CSVs (checked 2026-08-28).

## Two counts per day

- `n_outside_minmax`: features strictly below the training minimum or above the training maximum. This is the count the figure's top row and the binned tables use. A day with 0 sits inside the box the model has seen.
- `n_outside_quantiles`: features beyond the training 5th or 95th percentile. Softer: the day is inside the box but in a corner the model saw fewer than 5% of the time.

A NaN input is never counted as outside (it would already have dropped the row at anchoring).

## Outputs

Per target in `results/`:

- `<target>-daily.csv`: one row per test day per fold per model: date, test_year, model, both counts, one `<feature>_outside` boolean per feature (min/max), actual, pred, abs_error.
- `<target>-binned.csv`: per fold and model, one row per distinct `n_outside_minmax` with `days` and `mae`.
- `<target>-features.csv`: per fold and feature, the number of test days outside the training min/max, with the fold's test-day count.
- `<target>.meta.json`: input md5s, library versions, git commit (same keys as `ablation/`).

`figures/<target>-error-vs-novelty.png`: absolute error against novelty, one column per test year, top row min/max count, bottom row quantile count.

## Results, run 2026-08-28

### The 2026 answer: no min/max novelty at all

In the 2026 fold (trained 2022 to 2025), **every test day scores 0 on `n_outside_minmax` for both targets** (135 TOC days, 133 alkalinity days, all 10 and all 8 features inside the training box). So the question "does MAE rise with novelty count in 2026" has a flat answer for every model:

| Target | Model | 2026 days at count 0 | MAE at count 0 | Days at count 1 or more |
|---|---|---|---|---|
| TOC | rf_grid | 135 | 0.231 | 0 |
| TOC | catboost | 135 | 0.194 | 0 |
| Alk | rf_grid | 133 | 4.368 | 0 |
| Alk | catboost | 133 | 4.277 | 0 |

MAE does not rise with min/max novelty in 2026 because there is none. The premise in section 7.2 (zero SWE in June, flow below any training day) does not survive contact with the model's actual inputs: `swe_7day` is 0 every summer after melt-out in 2022 to 2025, so 0 in June 2026 is familiar, and the 2026 minimum of `flow_7day_avg` (188 cfs) sits above the training minimum (175 cfs). 2026 is a quiet year inside the envelope, not outside it. Whatever is wrong with the 2026 predictions (alkalinity R^2 -0.5 in `rolling/`), it is not mechanical extrapolation in the min/max sense.

### 2026 by the softer count (5th/95th percentile)

From `<target>-daily.csv`, binned on `n_outside_quantiles`:

| Target | Model | count 0 (days, MAE) | 1 | 2 | 3 | 4 | 5 | Spearman(count, error) |
|---|---|---|---|---|---|---|---|---|
| TOC | rf_grid | 98, 0.231 | 27, 0.251 | 3, 0.167 | 4, 0.181 | 2, 0.175 | 1, 0.253 | 0.06 |
| TOC | catboost | 98, 0.180 | 27, 0.253 | 3, 0.140 | 4, 0.159 | 2, 0.201 | 1, 0.305 | 0.19 |
| Alk | rf_grid | 65, 3.11 | 51, 4.45 | 14, 9.09 | 1, 10.87 | 2, 7.05 | | 0.40 |
| Alk | catboost | 65, 2.99 | 51, 4.53 | 14, 8.96 | 1, 9.54 | 2, 4.50 | | 0.41 |

- **TOC 2026: flat.** Error is 0.2 to 0.3 mg/L at every count for both models. Which inputs were in the tails: `turb_flow` below the 5th percentile on 25 days, `turb_3day` and `Turbidity_Median` below on 7, `turb/cond` above the 95th on 7, `Turbidity_Max` above on 3 and below on 7, `precip_7day` above on 2. Snowpack: 0 days in either tail (2026 `swe_7day` maximum 5.1 in, training 95th percentile 11.6; that 5.1 is the 7-day mean over the four suspect 9.0 readings of May 12 to 15 noted in section 7.1, so the real 2026 snow signal is lower still and even further inside the box). A low, clear river is a corner of the box, and the models handle it.
- **Alkalinity 2026: rises.** Days with no input in the tails have MAE 3.0 to 3.1 mg/L; days with two have 9.0 to 9.1 (14 days), three times worse, for both models. The tail inputs: `pH_Median` above the 95th percentile (8.4) on 35 days (2026 pH reached the training maximum, 8.6), `flow_7day_avg` below the 5th percentile (247 cfs) on 26 days, `turb_flow` below on 19, `turb_3day` and `Dissolved_Oxygen_Mean` below on 5. So the 2026 alkalinity days the models get most wrong are high-pH, low-flow days, a combination that occurred on under 5% of training days. This is the quantitative version of "2026 is the quietest water in the record", and it is the closest this experiment comes to naming the extrapolation.

### Earlier folds, min/max count (from `<target>-binned.csv`)

**TOC 2023** (trained on 2022 only): MAE rises monotonically with count for both models.

| count | days | rf_grid MAE | catboost MAE |
|---|---|---|---|
| 0 | 107 | 0.53 | 0.53 |
| 1 | 56 | 0.77 | 0.58 |
| 2 | 6 | 1.52 | 1.50 |
| 3 | 4 | 1.81 | 1.79 |
| 4 | 8 | 2.27 | 2.27 |
| 5 | 5 | 3.92 | 3.96 |
| 6 | 5 | 4.02 | 4.07 |

Features outside on the most days in 2023: `turb_flow` 33, `month_cos` 27, `turb_3day` 25, `turb/cond` 22, `precip_7day` 19, `Turbidity_Median` 19, `swe_7day` 16 (of 191). This is the 2023 flush: 2022 had no year like it, so its peak days were outside on five or six inputs at once, and both models missed them by around 4 mg/L. Novelty and error share a cause here (the flush is both the novel input and the missed output), so the table says "2022 could not teach 2023" rather than something about the model class.

**TOC 2024**: only `swe_7day` went outside (52 of 126 days, the 2024 snowpack peaked above anything in 2022 to 2023). MAE 0.41 to 0.66 (rf_grid) and 0.33 to 0.52 (catboost) from count 0 to 1. Modest rise.

**TOC 2025**: 0 on every day.

**Alkalinity 2023**: 82 of 186 days had at least one input outside (`turb_flow` 36, `Dissolved_Oxygen_Mean` 35, `month_cos` 25, `turb_3day` 25, `flow_7day_avg` 24). MAE does **not** rise: catboost 4.53 at count 0 down to 1.31 at count 4; rf_grid 5.91, 4.94, 6.27, 6.67, 0.83. **Alkalinity 2024**: `pH_Median` outside on 14 days; MAE falls from 5.40 to 3.85 (catboost) and 4.61 to 1.86 (rf_grid). For alkalinity, being outside the training range on a turbidity or flow input does not hurt, which is consistent with the ablation: those inputs are worth 0 to 5 points and conductance and pH carry the model.

## What this changes

- Section 7.2's "mechanical" explanation for the 2026 miss is not supported for either target at the min/max level. 2026's inputs are inside the box.
- For alkalinity the softer count does find the bad days: high pH with low flow, 14 to 17 days, MAE three times the rest. Section 7.2's "physical" explanation (a dry-year regime the model has not learned) is the one left standing, and the regime-split exploration (7.3, item 2) is the experiment that tests it.
- For TOC 2026 there is nothing to explain: no excursions, error 0.2 mg/L, inputs familiar. The 2023 table is the real extrapolation story in this data, and it says the first big year after a quiet one is the one the model cannot see coming.
