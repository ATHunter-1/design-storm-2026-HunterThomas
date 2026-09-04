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

Results in `results/`: `labels.csv` (every in-kit water year with its April 1 SWE, fraction of the reference median, label, days of data, and the reference itself on every row), `<target>-<models>.csv` (one row per model and direction), and `.meta.json` with the same keys as `ablation/` (input md5s over `data/*.csv` plus `analog/data/MichiganCreek_full.csv`, library versions, git commit). Two runs on 2026-08-28, and again on 2026-09-04 with the updated data, produced byte-identical CSVs. Labels still come from Michigan Creek (the record sections 7 and 9 were built on); the model frames use the updated data and lags.

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
| wet to dry | 2023, 2024, 2025 | 501 / 182 | 0 | 480 / 183 | 53 |
| dry to wet | 2026 | 182 / 501 | 128 | 183 / 480 | 324 |

**Only one dry year.** The dry side is water year 2026 alone (October 2025 to August 19, 2026) in both directions. Wet to dry is therefore a single-year test and dry to wet a single-year training set, and per the bead both are reported as indicative only. Dry to wet is the weaker of the two: 182 training days with no TOC excursion and a TOC range of 1.2 to 2.7 mg/L.

## Results, run 2026-09-04 (Sep 4 data, 2-day TOC lags, Hoosier Pass SNOTEL)

### TOC

| Direction | Model | R^2 | RMSE (mg/L) | Excursion recall | Excursion precision |
|---|---|---|---|---|---|
| wet to dry | forest | -2.55 | 0.26 | none to catch | no alarms raised |
| wet to dry | CatBoost | -2.11 | 0.24 | none to catch | no alarms raised |
| dry to wet | forest | -0.51 | 1.21 | 0.00 | no alarms raised |
| dry to wet | CatBoost | -0.55 | 1.22 | 0.00 | no alarms raised |

Water year 2026 has no day above 3 mg/L, so recall is undefined there; on this run neither model raises a false alarm (the Aug 28 run's forest had raised two). R^2 is deeply negative because the year is a flat line and any error counts against a tiny variance; RMSE of 0.24 to 0.26 mg/L is the number to read, and it sits beside the rolling 2026 fold (0.20 to 0.21). Trained on 2026 alone, neither model predicts a single excursion in the wet years (recall 0.00 on 128 days, actuals up to 7.3).

### Alkalinity

| Direction | Model | R^2 | RMSE (mg/L) | Excursion recall | Excursion precision |
|---|---|---|---|---|---|
| wet to dry | forest | 0.07 | 4.25 | 0.60 | 0.52 |
| wet to dry | CatBoost | -0.73 | 5.78 | 0.34 | 0.60 |
| dry to wet | forest | -0.03 | 10.86 | 0.40 | 0.92 |
| dry to wet | CatBoost | 0.08 | 10.25 | 0.58 | 0.93 |

In the dry year 29% of days are below 60 (53 of 183); in the wet years 68% (324 of 480), so the dry-to-wet precision of 0.92 to 0.93 is barely above the base rate. The dry-trained models cluster their predictions in the middle of the range they saw, which is all a model that only saw a quiet year can do.

## Reading

**Does a wet-trained model hold up on the dry year?** For TOC, yes in the only sense available: the models trained on 2023 to 2025 report a quiet year as quiet (errors around 0.25 mg/L, no false alarms on this run), but with zero excursion days there is no dry-year flush to catch and nothing here tests the "wrong physics" concern in section 7.2. For alkalinity, no: R^2 at or below zero, errors of 4 to 6 mg/L, and the models catch a third (CatBoost) to three fifths (forest) of the low days with about half of their alarms real, which is the operational problem section 4.1 flagged for 2026, now isolated from the 2022 training rows and extended to cover October to December 2025.

**The reverse is worse, and one year is not a regime.** A model trained on the drought year alone never predicts a TOC excursion (recall 0 on 128 days) and misses 40 to 60% of the wet years' low-alkalinity days with errors of 10 mg/L. That is an extrapolation failure (the training range does not contain the test range), and it is what will happen to any model refit on 2026 alone. It is also the weaker direction by construction: 182 to 183 training days from one water year.

**What this adds to the drought question.** The novelty exploration (7.4) found that 2026's inputs sit inside the training box, so the alkalinity errors are not out-of-range inputs. This split shows that models with no 2026 in training still miss the dry year's alkalinity by 4 to 6 mg/L, which is the regime story in 7.2 showing in the target rather than in the inputs: the same conductance and pH mean something different in a baseflow-dominated year. The data to settle the TOC side is a dry year with rain-driven excursions, which 2026 has not supplied.

## Caveats

- One dry year, one station, and the same 2026 that every other subsection studies. The split cannot separate "dry regime" from "2026 in particular".
- Water year 2026 is incomplete (data to August 19), and its test set includes October to December 2025, when the snowpack that defines the label had not yet failed to arrive; a substantial share of the 53 low-alkalinity days fall in those months (23 of 55 on the Aug 28 run).
- Both directions are single-year on the dry side and reported as indicative per the bead.
- `excursion_days`, recall, and precision use the same thresholds as `ablation/` (TOC above 3 mg/L, alkalinity below 60 mg/L).
