# Snowpack by water year

Shared foundation for the regime-split and analog-years explorations. Groups the Michigan Creek SNOTEL series by water year (October 1 to September 30) so each winter's snow stays with its own melt, and labels years wet or dry by April 1 SWE (the rule is in `../../exploration-notes.md` section 9).

## Run

From `experiments/`:

```
.venv/bin/python -m pytest snowpack/tests -q     # 11 pure-function tests
.venv/bin/python -m snowpack.run                 # prints the table, writes results/wateryear.csv
```

## Functions (`wateryear.py`, pure)

- `assign_water_year(index)`: October to December dates go to the next year.
- `summarise_by_water_year(swe)`: one row per water year with `peak_swe`, `peak_date` (first day the maximum is reached), `april1_swe`, `meltout_date` (first zero after the peak, NaT if none), `days_peak_to_meltout`, `days_with_data`. Sorts ascending first; the kit CSV is newest-first.
- `wet_or_dry(summary, reference_median, dry_below=DRY_BELOW_FRACTION, column="april1_swe")`: `dry` below `dry_below * reference_median`, else `wet`; NaN years are omitted. `DRY_BELOW_FRACTION = 0.75`.

`run.py` owns the CSV parsing (`M/D/YYYY` dates, one non-numeric SWE row on 8/26/2025) and uses the in-kit median April 1 SWE as the fallback reference. The period-of-record median comes from the analog-years exploration.

## Result, run 2026-08-28

| Water year | Peak SWE (in) | Peak date | April 1 SWE (in) | Melt-out | Days peak to melt-out | Days with data | Label |
|---|---|---|---|---|---|---|---|
| 2022 (from Apr 2) | 8.4 | Apr 18 | none | May 28 | 40 | 182 | (no April 1 reading) |
| 2023 | 9.6 | Apr 24 | 9.1 | May 28 | 34 | 365 | wet |
| 2024 | 13.1 | May 12 | 12.0 | Jun 4 | 23 | 366 | wet |
| 2025 | 10.0 | Apr 5 | 9.3 | May 31 | 56 | 364 | wet |
| 2026 (to Aug 23) | 9.0 | May 12 | 0.8 | May 16 | 4 | 327 | dry |

In-kit median April 1 SWE 9.2 in; dry below 6.9 in.

**Caveat on 2026.** The 9.0 peak is four readings on May 12 to 15 sitting between zeros on both sides (0.0 on May 10 and 11, 0.0 from May 16). That looks like a sensor artifact. With those four days masked, water year 2026 peaks at 4.9 in on March 16 and melts out on April 12. The functions report the file as it is; the analog-years exploration can check the NRCS record for the same days.
