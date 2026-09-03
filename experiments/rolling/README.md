# Rolling-origin evaluation

Train on every year before N, test on year N, for each N. Turns the ablation's single "R^2 on the second half" into one score per season, which is the only way to see whether a feature verdict is really a verdict about one year.

Built test-first, on top of `ablation/` (imports its frame builder, fitters, and excursion metric; changes nothing there).

## Run

From `experiments/`:

```
.venv/bin/python -m pytest rolling/tests -q          # 13 tests, pure functions only
.venv/bin/python -m rolling.run                      # both targets, jake_full vs the contested drop
.venv/bin/python -m rolling.run --target TOC --labels jake_full drop:swe_7day drop:precip_7day
```

Any `label` from the ablation configs works (`jake_full`, `drop:<feature>`, the minimal sets). Rows are anchored to `jake_full` exactly as in the ablation. Results in `results/`: one CSV with a row per (label, model, test year), a `.summary.csv` with mean, min, and max R^2 across years, and a `.meta.json`.

## Folds

Data runs April 2022 to August 2026, with no January to March in any year. Folds:

| Test year | Trained on | TOC rows train / test | TOC excursion days (above 3) | Alk excursion days (below 60) |
|---|---|---|---|---|
| 2023 | 2022 | 196 / 191 | 65 | 170 |
| 2024 | 2022-23 | 387 / 126 | 60 | 72 |
| 2025 | 2022-24 | 513 / 204 | 3 | 102 |
| 2026 (to Aug) | 2022-25 | 717 / 135 | 0 | 32 |

That table is most of the finding.

## Results, run 2026-08-25

### TOC

| Test year | jake_full forest | jake_full CatBoost | drop swe forest | drop swe CatBoost |
|---|---|---|---|---|
| 2023 (R^2 / RMSE) | -0.13 / 1.35 | -0.12 / 1.34 | -0.02 / 1.29 | -0.06 / 1.31 |
| 2024 | 0.46 / 0.65 | **0.62** / 0.55 | **0.69** / 0.50 | 0.51 / 0.62 |
| 2025 | -0.34 / 0.33 | -0.31 / 0.32 | -0.24 / 0.31 | -0.14 / 0.30 |
| 2026 | -2.00 / 0.27 | -1.54 / 0.25 | -2.54 / 0.30 | -2.82 / 0.31 |

Excursion recall on the two years that had excursions: 2023, 0.23 forest and 0.11 CatBoost (trained on 2022 only, they missed the big year); 2024, 0.57 and 0.72.

Reading:

- **There is one and a half informative years.** 2023 was the big TOC year (65 days above 3, RMSE around 1.3 for everything). Nothing trained on 2022 alone could see it coming. 2024 was the second-biggest and is the only year where the model, now with 2023 in training, does real work. 2025 had three excursion days and 2026 none, so R^2 there is noise around a flat line (RMSE 0.25 to 0.33 mg/L, which is fine) and says nothing about the model.
- **The snowpack disagreement survives.** In 2024, the only year that can adjudicate, dropping `swe_7day` moves the forest up 23 points and CatBoost down 11. Same feature, same year, opposite verdicts. This is not a 2023 story; it is a "one year of evidence" story. No experiment on this data will settle whether snowpack belongs. Jake's own line, "don't expect it to get much better without more data," is exactly right, and the data it needs is another big year.
- **Jake's single-split numbers (0.56 forest, 0.65 CatBoost) are a weighted average of a good 2024 and two quiet years.** Anyone quoting them should say "on 2024 to 2026, of which only 2024 had excursions."

### Alkalinity

| Test year | jake_full forest | jake_full CatBoost | drop turb_flow forest | drop turb_flow CatBoost |
|---|---|---|---|---|
| 2023 | -0.31 | 0.33 | -0.75 | **0.43** |
| 2024 | **0.38** | 0.14 | 0.35 | 0.07 |
| 2025 | 0.75 | 0.80 | 0.72 | **0.81** |
| 2026 | -0.52 | -0.49 | -0.56 | -0.87 |
| mean | 0.07 | **0.19** | -0.06 | 0.11 |

Excursion recall stays between 0.63 and 0.93 in every year for every configuration; precision falls to 0.40 to 0.50 in 2026.

Reading:

- **Alkalinity swings from -0.5 to +0.8 depending on the year.** 2025 is the good year for everyone. 2026 is bad for everyone, with 32 low days and precision under 0.5, which is the "back and forth around 60" Jake describes in the deck, now with a number on it.
- **Keep `turb_flow`.** The ablation's single split said dropping it gained 1.5 points for CatBoost. Across years it costs 8 points on the mean for CatBoost and 13 for the forest, and it helps in exactly the two years it happened to help. Single-split ablation deltas of a couple of points are noise on this data.
- **The classifier's problem is the target, not the features.** Recall holds up in every configuration and every year. What moves is precision, and it moves with how much of the year sits within a few mg/L of 60. That is the case for predicting the compliance matrix cell (or the distance to 60) rather than the binary. See `exploration-notes.md`, section 1.1.

## What this changes in the ablation's conclusions

- "Alkalinity: eight to six is free" stands; the specific feature to drop is not `turb_flow`.
- "TOC: the turbidity family collapses to two" stands (recall is unchanged everywhere).
- "Whether snowpack belongs depends on which model you ask" becomes "depends on 2024, and 2024 cannot decide."
- Any claim of the form "model X gets R^2 0.6" should carry the year.
