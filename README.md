# Design Storm 2026: Denver Water materials

Sent by Jake Slawson (Data Scientist, Denver Water Water Quality & Treatment) on 2026-08-25, following the Aug 24 call with Cassidi Rosenkrance and Paul.

## Disclaimer (Denver Water, must travel with the data)

> The water quality data is provided "as is." Water quality data provided to the user is provisional and subject to change, and the user should not assume that the data has undergone any quality assurance or quality control review. Denver Water makes no warranty of any kind, express or implied, concerning the data, including accuracy, reliability, completeness, timeliness, or usefulness.
> Copyright 2026, Denver Water. https://www.denverwater.org/about-us/how-we-operate/public-records

## The problem

Predict **TOC** and **alkalinity** at the **Foothills Water Treatment Plant influent four days ahead**, from upstream gage, streamflow, snowpack, and precipitation data. Both analytes affect treatability, so advance warning lets plant operators plan staffing and treatment when outlier water is coming down the South Platte.

The four-day horizon was chosen empirically (highest model accuracy) and lines up with transport time from the sampling area around Strontia Reservoir down to Foothills.

Jake's framing: the models are still under development, built as a case study for what is possible with current data. Not publication-ready.

## Contents

`ExploreDDD_Materials/Scripts/` (Jupyter notebooks)

| Notebook | What it does |
|---|---|
| `TOC_SoftSensor.ipynb` | TOC model development |
| `Alkalinity_Soft_Sensor.ipynb` | Alkalinity model development (regression and classification) |
| `USGS_gage_data_grabber.ipynb` | USGS water quality API pull |
| `DWR_gage_grabber.ipynb` | Colorado DWR streamflow API pull |
| `SNTL_grabber.ipynb` | NWCC / SNOTEL snowpack API pull |
| `GHCN_grabber.ipynb` | NOAA GHCN precipitation API pull |

`ExploreDDD_Materials/Data/` (CSV, all series start 2022-04-01)

| File | Columns | Rows |
|---|---|---|
| `FoothillsInfluent.csv` | DATE, TOC_mg_L, Alk_mg_L | 1120 |
| `MichiganCreek.csv` | DATE, SWE (SNOTEL snow water equivalent) | 1606 |
| `SouthPlatteFlow.csv` | measDate, Flow_CFS (DWR) | 1607 |
| `SouthPlatteTelemetry.csv` | Date, Flow_CFS, GageHeight_ft, Precip | 1607 |
| `USC00058022.csv` | STATION, DATE, PRCP, SNOW, TMAX, TMIN (NOAA GHCN) | 1604 |
| `USGS_South_Platte.csv` | Date, site_no, dissolved oxygen, specific conductance, temp, turbidity, pH (max/mean/min) | 1033 |

`ExploreDDD_Materials/Data/Figures/` holds the model output plots: correlation matrices, feature and permutation importance, and prediction comparisons for TOC, alkalinity, and turbidity, including CatBoost variants.

`Foothills_INF_ML_NoConclusions.pptx` is the intro to the deck Jake presented to Denver Water leadership around July 2026. Conclusions removed.

## Method, from the deck

- Random forest, trained on lagged features shifted 4 days relative to Foothills influent
- Month converted to radians so the model treats January and December as close
- Rolling 7-day averages for flow and precipitation, rolling 3-day for turbidity
- Flow times turbidity as a "loading" parameter
- Spearman correlation matrix used to pick candidate predictors, then combinations tried until best result

Reported results (deck, ~July 2026):
- TOC: R^2 0.59, RMSE 0.29 mg/L, MAPE 9.52%. Peak accuracy prioritized over raw R^2, since TOC is stable most of the year. Currently overestimates due to 2023 in the training data.
- Alkalinity regression: R^2 0.65, RMSE 5.89 mg/L, MAPE 8.34%.
- Alkalinity classification (above or below 60 mg/L): struggles with back-and-forth near the threshold. Jake: "not sold on precision."

**Newer than the deck:** Michigan Creek SNOTEL added as a predictor, and CatBoost tried as an additional model. Neither is described in the slides.

## Open offers from Jake

- Refresh the CSVs closer to the conference, for attendees who want ready-to-code data
- Walk through the material by email or Zoom

## Related

- Plain-language definitions of every water and statistics term used in this repo: [glossary.md](glossary.md)
- Visualizations: [design-storm-water-system-3d.html](design-storm-water-system-3d.html), a 3D map of the supply system from snowpack to treatment plants, and [design-storm-strontia-springs-brief.html](design-storm-strontia-springs-brief.html), a brief on a real turbidity spike at the Strontia gage on 15 Aug 2026, written before Jake's materials arrived. To view locally: `python3 serve.py 8765` from the repo root (or `python3 -m http.server`), then open `localhost:8765/design-storm-water-system-3d.html`. They load their data from `water-system-3d/` and `strontia-brief/`, so opening the files straight off disk shows an error; map tiles and live gage data also need an internet connection.
- The 3D map is also published as an online demo: **https://exploreddd.com/2026-design-storm-demo/#pw=snowmelt-2026** (this link skips the password prompt). The plain URL https://exploreddd.com/2026-design-storm-demo/ asks for the passphrase, snowmelt-2026. Unlisted; the Foothills influent data is served AES-encrypted and the brief is not published. The live copy is deployed from the Explore DDD website repo; edits here reach it when Paul re-runs the staging script and pushes.
- People: Jake Slawson (Data Scientist, Water Quality & Treatment) and Cassidi Rosenkrance (WQ&T Manager, Lab-Monitoring), Denver Water
- The four-cohort exercise structure is drafted in Explore DDD's planning docs, outside this repository
