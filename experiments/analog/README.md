# Analog years: past snowpack curves that resemble 2026, and what followed

Item 4 of exploration-notes section 7.3. The USGS sonde starts in 2022, so there are no TOC or alkalinity labels before then. The SNOTEL station and the DWR gage go back much further, so the question here is narrower: has Michigan Creek seen a snow year like 2026 before, and what did the South Platte above Strontia do in that year and the next.

## Run

From `experiments/`:

```
.venv/bin/python -m pytest analog/tests -q     # 13 tests, pure functions and the offline run
.venv/bin/python -m analog.run                 # offline, from analog/data/*.csv, writes analog/results/
.venv/bin/python -m analog.run --fetch         # network: refresh analog/data/*.csv and data/README.md
```

Two offline runs produce byte-identical CSVs (checked 2026-08-28).

## Data

`data/README.md` records the fetch (2026-08-28), the literal request parameters, and row counts. In short: NRCS returned the whole Michigan Creek record on the first request, 10,194 daily SWE readings from 1998-09-30, which is 28 water years (1999 to 2026) plus a single 1998-09-30 reading that forms a one-day row for water year 1998. DWR returned 45,895 streamflow rows from 1900-01-01 in one page, 127 water years after reindexing to every calendar day. Water year 2026 runs to 2026-08-27 in both files (331 days of flow), so its flow maximum and mean are for October through late August.

**The four suspect May 2026 readings are in the NRCS record too.** The kit file shows SWE 9.0 on May 12 to 15, 2026 with 0.0 on May 10, 11, and from May 16 on (section 7.1). The NRCS pull shows the same seven values: 0, 0, 9, 9, 9, 9, 0. As of 2026-08-28 the service has not flagged or removed them. Because they decide what "2026's shape" means, `run.py` writes two rankings: one on the file as fetched (the bead's specification) and one with those four days masked to missing (`SUSPECT_SWE_DATES` in `run.py`, `mask_days` in `similarity.py`).

## Functions (`similarity.py`, pure)

- `water_year_table(swe, flow)`: one row per water year. From `snowpack.wateryear.summarise_by_water_year`: `peak_swe`, `april1_swe`, `days_peak_to_meltout`, `days_with_data`; derived here `peak_day_of_water_year` (days from October 1 of the preceding calendar year, so November 1 is day 31). From flow, grouped by the same water year: `flow_max`, `flow_max_day_of_water_year`, `flow_mean`. Outer join, so pre-1999 years carry flow only.
- `analog_ranking(table, reference_year, columns)`: z-score each column over every year that has all of them (population standard deviation; a constant column contributes nothing), Euclidean distance from the reference year, sorted ascending with the raw values alongside. The reference year is excluded from its own ranking; years missing any ranking column are left out.
- `following_year(table, years)`: the next water year's row for each analog, NaN when it is not in the table.
- `mask_days(swe, dates)`: the named dates set to missing, everything else untouched.

`run.py` ranks on snowpack shape only (`SHAPE_COLUMNS`: `peak_swe`, `peak_day_of_water_year`, `days_peak_to_meltout`) and keeps the top 5. Flow columns ride along for reading, not for ranking. `.meta.json` has the same keys as `ablation/`'s metadata with `inputs_md5` over `analog/data/*.csv`.

## Results, run 2026-08-28

Days are counted from October 1. SWE in inches at Michigan Creek; flow in cfs at PLASPLCO. All years are water years, so the flow numbers differ from the calendar-year table in section 7.1.

### As fetched (`results/analogs-2026.csv`, `results/following-years.csv`)

Water year 2026 as fetched: peak 9.0 on May 12 (day 223), melt-out May 16 (4 days), April 1 SWE 0.8.

| Analog | Distance | Peak SWE | Peak date | Days to melt-out | April 1 SWE | Flow max | Flow mean | Next year | Next peak SWE | Next April 1 | Next flow max | Next flow mean |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2004 | 1.57 | 9.2 | Apr 30 | 23 | 6.6 | 1050 | 330 | 2005 | 12.3 | 10.4 | 1010 | 401 |
| 2015 | 1.72 | 11.9 | May 19 | 22 | 9.1 | 3830 | 732 | 2016 | 13.0 | 10.8 | 1080 | 466 |
| 2010 | 1.99 | 10.4 | May 3 | 29 | 8.5 | 1270 | 423 | 2011 | 16.1 | 14.3 | 1350 | 441 |
| 2024 | 2.00 | 13.1 | May 12 | 23 | 12.0 | 1390 | 459 | 2025 | 10.0 | 9.3 | 734 | 391 |
| 2005 | 2.11 | 12.3 | May 1 | 26 | 10.4 | 1010 | 401 | 2006 | 15.6 | 15.3 | 1110 | 420 |

### Suspect days masked (`results/analogs-2026-masked.csv`, `results/following-years-masked.csv`)

Water year 2026 with May 12 to 15 masked: peak 4.9 on March 16 (day 166), melt-out April 12 (27 days), April 1 SWE 0.8.

| Analog | Distance | Peak SWE | Peak date | Days to melt-out | April 1 SWE | Flow max | Flow mean | Next year | Next peak SWE | Next April 1 | Next flow max | Next flow mean |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2002 | 1.74 | 6.8 | Mar 27 | 45 | 6.6 | 748 | 399 | 2003 | 13.6 | 11.8 | 750 | 334 |
| 2022 | 2.53 | 8.4 | Apr 18 | 40 | 7.6 | 970 | 422 | 2023 | 9.6 | 9.1 | 1090 | 409 |
| 2018 | 2.56 | 9.1 | Apr 21 | 26 | 6.3 | 751 | 382 | 2019 | 14.6 | 14.3 | 1540 | 430 |
| 2023 | 2.86 | 9.6 | Apr 24 | 34 | 9.1 | 1090 | 409 | 2024 | 13.1 | 12.0 | 1390 | 459 |
| 2017 | 2.90 | 9.8 | Apr 4 | 53 | 8.8 | 1060 | 434 | 2018 | 9.1 | 6.3 | 751 | 382 |

2012, the other usual Colorado suspect, is eighth (distance 3.26): peak 7.1 on March 1, April 1 SWE 5.9, but 64 days to melt-out, the slowest tail in the record, which is why the shape distance keeps it out of the top five.

### Where 2026 sits in the record

- Flow: max 620 cfs (July 18) and mean 323 cfs through August 27. The lowest annual maximum since 1999 (next: 2025 at 734, 2002 at 748) and the third lowest in 127 water years, after 1963 (530) and 1902 (593).
- Snow, as fetched: fourth-lightest peak of 28 (after 2002 at 6.8, 2012 at 7.1, 2022 at 8.4); lowest April 1 SWE by 5.1 inches (2012 at 5.9 is next).
- Snow, masked: lightest peak by 1.9 inches, lowest April 1 SWE, and the earliest melt-out by 22 days (2012 reached zero on May 4).
- Period-of-record median April 1 SWE, 1999 to 2026: 10.05 inches (10.1 without 2026). Section 9's 75% line is then 7.5 inches; below it are 2012 (5.9), 2018 (6.3), 2002 (6.6), 2004 (6.6), 2013 (7.4), and 2026 (0.8). 2022 sits just above at 7.6. This is the reference the regime-split exploration was waiting for.

## Reading

**"Light, late, fast" is three-quarters artifact.** The description of 2026 that motivated this exploration (light peak, late peak, fast melt-out) comes from the four May readings. Taken at face value, the closest years are ordinary-to-good snow years that happened to peak late and melt fast (2004, 2015, 2010, 2024, 2005), none of them dry, each followed by a near-normal or wet year. That ranking answers a question nobody asked. NRCS still serves those four days, so whether to treat them as real is a question for Jake (section 5); everything below uses the masked curve.

**Light and early has precedent in kind, not in degree.** With the suspect days out, 2026's nearest neighbours are the Colorado dry years people name from memory: 2002 first, then 2022 and 2018, with 2012 further down for its slow tail. So the regime is not new to this station. The size is: 2026 carried less snow at peak than any year in the record, had almost nothing on April 1, and was bare three weeks earlier than the earliest previous melt-out. On this station 2026 is outside the 28-year envelope on all three shape measures, which matches the novelty finding (section 7.4) that the model's inputs were nonetheless inside their training ranges: the snowpack inputs the model sees are zero every summer anyway.

**What followed a dry year.** Snow came back to median or above the next year in four of the five masked analogs (2003 at 13.6, 2019 at 14.6, 2024 at 13.1, 2023 at 9.6); the exception is 2017 to 2018, a below-median year followed by a dry one. The river did not always follow the snow. After 2002, water year 2003 had a 13.6 inch peak but the gage stayed at 750 cfs max and 334 cfs mean, the third-lowest mean since 1999. **(general knowledge, hypothesis)** Upstream reservoirs refilling after 2002 would explain that, and section 1.2 says the gage is partly Denver Water's releases. After 2018, 2019 brought 1540 cfs; after 2022, 2023 brought 1090 cfs and the biggest TOC year in the kit (70 days above 3 mg/L, section 7.1). So the year after a dry year at this gage has ranged from 750 to 1540 cfs at peak, and the one dry-to-wet transition the sonde has seen (2022 to 2023) is the big-flush case. That is the one data point behind the carry-over hypothesis in section 7.2, and it is consistent with it without proving it.

**Dry-year peak flow comes late.** In 2002, 2003, 2018, 2022, and 2026 the annual maximum fell outside the melt window (June 1, then September 8, September 16, September 2, July 18), where in ordinary years it lands in late May or June. That is the flow-side signature of section 7.2's "wrong physics" point: in a dry year the biggest water is rain or release, not melt.

## Caveats

- One station, one gage. Michigan Creek is the predictor Jake chose, not a basin index; the gage is below Denver Water infrastructure (section 1.2), so flow is management as well as weather.
- Shape distance is three numbers with equal weight after standardising. On the masked curve, every subset of the four candidate columns (the three used plus `april1_swe`, eleven subsets) puts some mix of 2002, 2018, 2022, 2012, and 2004 in the top five, but which one leads depends on the columns: 2002 with the specified three, 2018 when melt-out speed is in and peak day is out, 2012 when April 1 SWE is in alongside peak day. The set of dry-year neighbours is stable; the order within it is not.
- No TOC or alkalinity claims about analog years: the sonde did not exist.
- Water year 2026 is incomplete (to August 27). September flow is usually low, so the maximum is unlikely to move; the mean may drift down.
