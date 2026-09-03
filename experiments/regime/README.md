# Regime split: train on wet years, test on dry, and the reverse

Item 2 of `exploration-notes.md` section 7.3. Labels each water year wet or dry by snowpack, then trains Jake's models on one regime and scores them on the other. Answers whether a model that learned snow-flush years transfers to a drought year.

Built test-first on top of `snowpack/` (water-year grouping and the wet/dry rule), `analog/` (the period-of-record SWE file), and `ablation/` (frame, fitters, excursion metric). Changes nothing in any of them.

## Run

From `experiments/`:

```
.venv/bin/python -m pytest regime/tests -q     # 17 tests, pure functions and the labels file
.venv/bin/python -m regime.run                 # both targets, rf_grid + catboost
.venv/bin/python -m regime.run --target Alk --models catboost
```

Results in `results/`: `labels.csv` (every in-kit water year with its April 1 SWE, fraction of the reference median, label, days of data, and the reference itself on every row), `<target>-<models>.csv` (one row per model and direction), and `.meta.json` with the same keys as `ablation/` (input md5s over `data/*.csv` plus `analog/data/MichiganCreek_full.csv`, library versions, git commit). Two runs on 2026-08-28 produced byte-identical CSVs.

## The measure

A water year is dry when its April 1 SWE at Michigan Creek is below 75% (`DRY_BELOW_FRACTION` in `snowpack.wateryear`) of the period-of-record median April 1 SWE at that station, and wet otherwise; the reference is the median over the 28 water years with an April 1 reading in `analog/data/MichiganCreek_full.csv`, 10.05 inches, so the dry line is 7.54 inches (rationale and sources in `exploration-notes.md` section 9).

`results/labels.csv`:

| Water year | April 1 SWE (in) | Fraction of 10.05 | Label | Days of data |
|---|---|---|---|---|
| 2022 | none (file starts April 2) | | unlabelled | 182 |
| 2023 | 9.1 | 0.91 | wet | 365 |
| 2024 | 12.0 | 1.19 | wet | 366 |
| 2025 | 9.3 | 0.93 | wet | 364 |
| 2026 | 0.8 | 0.08 | dry | 327 |

Reference median 10.05 inches from 28 years; fallback not used. The four suspect 9.0 readings on May 12 to 15, 2026 (section 7.1, confirmed in the NRCS record by `analog/`) do not touch April 1, so they have no effect on any label. Water year 2022 has no April 1 reading, so its rows (171 for TOC, 173 for alkalinity, all April to September 2022) are excluded from both directions and counted in `excluded_rows`.

**Fallback.** If the long record is missing or has fewer than 20 water years with an April 1 reading (`MIN_REFERENCE_YEARS` in `labels.py`), the reference is the median of the in-kit years (9.2 inches) and `labels.csv` says `fallback_used=True` with `reference_years=4`. Section 9 explains why that is the weaker measure. Not needed on this run.

## Functions

`split.py` (pure):

- `regime_folds(frame, labels)`: each row's water year from `snowpack.wateryear.assign_water_year(frame.index)`, mapped through `labels` (water year to `wet` or `dry`). Returns two `RegimeFold`s, `wet` to `dry` then `dry` to `wet`, each with `train_regime`, `test_regime`, `train_years`, `test_years` (the labelled years that actually have rows), `excluded_rows` (rows whose water year has no label), and the two frames. October to December rows belong to the following water year, so October to December 2025 is part of the dry 2026 test set.
- `score_regime_fold(fold, spec, features, model)`: fits with `ablation.scoring.FITTERS` (same seeds, grid, weights, threads) and returns `RegimeScores`, the fields of `rolling.evaluate.FoldScores` except `test_year` plus the five fold fields above.

`labels.py` (pure): `reference_from(full_summary, kit_summary)` picks the reference and records whether the fallback was used; `labels_table(kit_summary, reference)` builds the `labels.csv` table using `snowpack.wateryear.wet_or_dry`.

`run.py` loads the kit SNOTEL file with `snowpack.run.load_swe` and the long record with `analog.run.load_swe`, builds and anchors each target's frame exactly as `rolling/run.py` does (Jake's full feature set, `anchored_rows`), and scores both directions for both models.

## Folds

Rows are on the anchored index (the days Jake's full feature set is present), grouped by water year.

| Direction | Trained on | TOC rows train / test | TOC excursion days in test (above 3) | Alk rows train / test | Alk excursion days in test (below 60) |
|---|---|---|---|---|---|
| wet to dry | 2023, 2024, 2025 | 494 / 187 | 0 | 480 / 187 | 55 |
| dry to wet | 2026 | 187 / 494 | 128 | 187 / 480 | 324 |

**Only one dry year.** The dry side is water year 2026 alone (October 2025 to August 23, 2026) in both directions. Wet to dry is therefore a single-year test and dry to wet a single-year training set, and per the bead both are reported as indicative only. Dry to wet is the weaker of the two: 187 training days with no TOC excursion and a TOC range of 1.2 to 2.7 mg/L.

## Results, run 2026-08-28

### TOC

| Direction | Model | R^2 | RMSE (mg/L) | Excursion recall | Excursion precision |
|---|---|---|---|---|---|
| wet to dry | forest | -3.49 | 0.30 | none to catch | 0.00 (2 false alarms) |
| wet to dry | CatBoost | -2.72 | 0.27 | none to catch | no alarms raised |
| dry to wet | forest | -0.53 | 1.22 | 0.00 | no alarms raised |
| dry to wet | CatBoost | -0.47 | 1.20 | 0.00 | no alarms raised |

Water year 2026 has no day above 3 mg/L, so recall is undefined there; the forest called two days above 3 (predicted range 2.42 to 3.06 against an actual 1.20 to 2.70) and CatBoost none. R^2 is deeply negative because the year is a flat line (mean 2.18, range 1.5 mg/L) and any error counts against a tiny variance; RMSE of 0.27 to 0.30 mg/L is the number to read, and it matches the rolling 2026 fold (0.25 to 0.27). Trained on 2026 alone, neither model predicts a single excursion in the wet years: predicted range 1.74 to 2.38 against 128 actual days up to 7.30.

### Alkalinity

| Direction | Model | R^2 | RMSE (mg/L) | Excursion recall | Excursion precision |
|---|---|---|---|---|---|
| wet to dry | forest | 0.08 | 4.21 | 0.62 | 0.54 (63 alarms, 55 real days) |
| wet to dry | CatBoost | -0.70 | 5.72 | 0.35 | 0.61 (31 alarms) |
| dry to wet | forest | -0.04 | 10.90 | 0.42 | 0.92 (146 alarms, 324 real days) |
| dry to wet | CatBoost | 0.12 | 10.04 | 0.63 | 0.94 (218 alarms) |

In the dry year 29% of days are below 60 (55 of 187); in the wet years 68% (324 of 480), so the dry-to-wet precision of 0.92 to 0.94 is barely above the base rate. The dry-trained models predicted 57 to 70 mg/L against an actual 39 to 92.5, which is what a model that only saw 51 to 75.5 can do.

## Reading

**Does a wet-trained model hold up on the dry year?** For TOC, yes in the only sense available: the models trained on 2023 to 2025 report a quiet year as quiet (errors under 0.3 mg/L, two false alarms from the forest and none from CatBoost), but with zero excursion days there is no dry-year flush to catch and nothing here tests the "wrong physics" concern in section 7.2. For alkalinity, no: R^2 at or below zero, errors of 4 to 6 mg/L, and the models catch a third (CatBoost) to two thirds (forest) of the low days with about half of their alarms real, which is the operational problem section 4.1 flagged for 2026, now isolated from the 2022 training rows and extended to cover October to December 2025.

**The reverse is worse, and one year is not a regime.** A model trained on the drought year alone never predicts a TOC excursion (recall 0 on 128 days) and misses 40 to 60% of the wet years' low-alkalinity days with errors of 10 mg/L. That is an extrapolation failure (the training range does not contain the test range), and it is what will happen to any model refit on 2026 alone. It is also the weaker direction by construction: 187 training days from one water year.

**What this adds to the drought question.** The novelty exploration (7.4) found that 2026's inputs sit inside the training box, so the alkalinity errors are not out-of-range inputs. This split shows that models with no 2026 in training still miss the dry year's alkalinity by 4 to 6 mg/L, which is the regime story in 7.2 showing in the target rather than in the inputs: the same conductance and pH mean something different in a baseflow-dominated year. The data to settle the TOC side is a dry year with rain-driven excursions, which 2026 has not supplied.

## Caveats

- One dry year, one station, and the same 2026 that every other subsection studies. The split cannot separate "dry regime" from "2026 in particular".
- Water year 2026 is incomplete (to August 23), and its test set includes October to December 2025, when the snowpack that defines the label had not yet failed to arrive. Those 52 to 54 rows contributed 23 of the 55 low-alkalinity days.
- Both directions are single-year on the dry side and reported as indicative per the bead.
- `excursion_days`, recall, and precision use the same thresholds as `ablation/` (TOC above 3 mg/L, alkalinity below 60 mg/L).
