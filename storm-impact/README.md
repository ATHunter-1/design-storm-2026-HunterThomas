# Storm Impact: static page (Scenario 2, Option A)

A single page that lines up sensor readings along the flow path, from the river
gage above Strontia Springs, through the reservoir by depth, to the Foothills plant.
Staff can use it to judge when a storm's impact reaches the plant. The page shows
the evidence, and the operator makes the timing call. See
[`../docs/scenario-2-planning.md`](../docs/scenario-2-planning.md) and
[`../docs/scenario-2-visualization-options-plan.md`](../docs/scenario-2-visualization-options-plan.md).

## Viewing

```
python3 serve.py          # from the repository root
open http://localhost:8765/storm-impact/
```

The page fetches `storm-impact.json`, so serve it. Opening the file directly will
not work. It uses no build step; only the sensor map needs the network (see below).

## What is on the page

1. **Flow-path timeline.** One row per stop on a shared time axis: Trumbull flow,
   river-gage turbidity (15-minute where the repo has it, USGS daily max otherwise),
   river-gage conductance, reservoir turbidity by depth band (median of each full
   sonde cast), and Foothills TOC (daily lab sample). Each row marks its peak. A
   dashed line marks the river peak.
2. **Reservoir depth chart.** Each sonde cast is drawn as a column, with time across
   and depth down. You can color it by turbidity (log scale) or by temperature,
   which shows the layering. Hover over a cell to read it.
3. **Past-storm comparison.** Aug 14-15 and Jul 28 side by side: the river peak, the
   reservoir peak, the plant TOC peak, each with a baseline, and the lags.
4. **Sensor map.** A Leaflet map in the style of `../sensor-snapshot-map.html`. Each
   marker's colour and size show that sensor's reading at the cursor, placed on a
   per-storm scale from baseline to peak. River and reservoir turbidity use a log
   scale; TOC uses a linear one; flow runs from its window start to twice that. A
   dark ring marks a stop whose peak has passed. A selector picks which depth band
   the reservoir marker shows. The "At the cursor" cards list every reading, its
   timestamp, and its scale.

The slider and the Play button move one time cursor through every view at once.

The map needs a network connection for Leaflet (unpkg) and the OpenStreetMap
tiles. If Leaflet cannot load, the page falls back to a simple offline SVG map.
Everything else works offline.

## Files

| Path | What it is |
|---|---|
| `index.html` | Hand-written page: vanilla JS and SVG/canvas, plus Leaflet for the sensor map. |
| `build_data.py` | Generates `storm-impact.json`. Uses only the standard library and works offline. |
| `storm-impact.json` | Generated file. Do not edit it by hand. Rebuild it with `python3 storm-impact/build_data.py`. |

`build_data.py` reads `data/USGS_South_Platte.csv`, `data/Strontia 0407_0819.xlsx`,
`data/FoothillsInfluent.csv`, `strontia-brief/series/*.json`,
`strontia-brief/places.json`, and `strontia-brief/basins/*.json`. It writes only
`storm-impact.json`. When it runs, it prints the daily depth-band median table,
which matches the table in `docs/scenario-2-planning.md`.

## Assumptions and limits

- Every reading is provisional. USGS and Denver Water may revise these values.
- A **cast** is a run of sonde readings with no gap longer than 20 minutes. A
  cast counts as **full** when it reaches past 40 in "Vertical Position." Short
  casts only sample the top few units. They appear on the depth chart but are left
  out of the band lines and the peak search.
- "Vertical Position" has no unit in the file. It is probably depth in metres, but
  Denver Water still needs to confirm that. The file also does not state the
  sonde's location or the time zone of its clock, so times are shown as recorded.
- The repo has 15-minute river data only for Aug 14 noon to Aug 15 6 PM. At every
  other time, the page shows USGS daily summaries. For Jul 28, the river peak time
  is unknown, so the page places it at noon when it counts lag in hours.
- Plant timing is accurate only to the day, because TOC comes from a daily lab
  sample.
- The page does not predict, model, prove causes, or recommend treatment.

## Data terms

Denver Water's two notices apply to this page and to `storm-impact.json`. They
appear in full at the bottom of the page and in [`../data/TERMS.md`](../data/TERMS.md).
Redistribution is restricted, so read those notices before you publish anything
built from this page.
