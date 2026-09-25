# Scenario 2: Visualization Options Implementation Plan

Follows on from [scenario-2-planning.md](scenario-2-planning.md), line 103 (the team's
contribution is to continue the story through the reservoir to the plant) and line 105
(the deliverable "can be a static page, a notebook, or a Scenario 2 mode in the 3D map;
pick whichever the team can build fastest").

All three options share the same data prep (gage series, sonde depth bands, Foothills
TOC) and the same layout described in scenario-2-planning.md: flow-path timeline,
reservoir depth chart, past-storm comparison, and sensor map.

## Option A — Static page

**What it is:** A single self-contained HTML file (e.g., `storm-impact/index.html`)
with pre-rendered charts, no server logic beyond `serve.py`.

**How it looks:** A vertically stacked page — title/provisional-data banner, the
flow-path timeline (three stacked line charts sharing an x-axis: gage
turbidity/conductance, sonde turbidity-by-depth-band, plant TOC), the reservoir depth
chart as a heatmap (time x depth, color = turbidity), a small side-by-side comparison
of Aug 14-15 vs Jul 28, and a static sensor map (SVG or small Leaflet/Mapbox snippet,
non-interactive) with markers in flow order. Built with a lightweight chart library
(Chart.js/D3) reading a pre-generated JSON (like `system.json`'s pattern). No
animation required, but a scrubber/slider is easy to add.

**Effort:** Lowest — no map engine, no live tiles, works offline once the JSON is
built.

## Option B — Notebook

**What it is:** A Jupyter/Observable-style notebook (e.g.,
`storm-impact/notebook.ipynb`) doing data loading, alignment, and plotting inline with
narrative markdown cells.

**How it looks:** Cells alternate prose ("Domain primer," "What Denver Water told
us") and matplotlib/plotly charts: one cell builds the gage+sonde+TOC combined
timeline plot, one cell renders the depth-by-time heatmap, one cell tabulates the
Aug 14-15 vs Jul 28 comparison, one cell prints/plots sensor coordinates on a simple
map (folium or a static plot). Reads directly from `data/` and
`strontia-brief/series/` via pandas.

**Effort:** Lowest for the data wrangler role since exploration and presentation are
the same artifact; less polished as a demo, best for showing the underlying analysis
and assumptions transparently.

## Option C — Scenario 2 mode in the 3D map

**What it is:** A new mode alongside the existing "Replay the Aug 14-15 storm" button
in `design-storm-water-system-3d.html`, e.g., "Continue to the reservoir & plant."

**How it looks:** Reuses the existing replay UI (map flies to Strontia Springs, the
`replaybar` scrubber/play controls, the `spark` canvases) but extends `STORM.frames`
past the gage: after the river-turbidity spark, add a depth-band heatmap strip (a
small canvas or DOM grid, colored by the six depth bands 0-5/5-15/15-25/25-35/35-50)
that animates in sync with the timeline slider, then a TOC spark for Foothills. Map
markers for the reservoir, dam, intake, and plant (from `places.json`) highlight/pulse
as the slider passes their arrival time, continuing the "pulse moving down the page"
idea from the flow-path timeline but overlaid on the existing satellite map instead of
a separate page.

**Effort:** Highest (touches existing JS state machine `STORM`, adds new data loading
for sonde + TOC), but most cohesive with what's already built and what Denver Water
has seen.

## Recommendation

For a 4-hour build, start with Option A (or B if the data wrangler wants to work in
notebook form first, then port to a static page) — it's fastest and satisfies line
105's directive to "pick whichever the team can build fastest." Option C is the
strongest long-term fit but riskier under time pressure since it requires modifying
live JS state (`STORM`) rather than authoring a new file.
