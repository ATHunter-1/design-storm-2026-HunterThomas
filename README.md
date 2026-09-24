# Design Storm 2026: Denver Water materials

Sent by Jake Slawson (Data Scientist, Denver Water Water Quality & Treatment) on 2026-08-25, following the Aug 24 call with Cassidi Rosenkrance and Paul. Updated 2026-09-04 (`ExploreDDD_Materials_Update.zip`): data through 2026-08-19 to match the real-time profiling sonde deployed in Strontia Reservoir, bug fixes in the notebooks, a replacement SNOTEL station, and shorter TOC lags. The Strontia sonde data itself arrived 2026-09-02 (`data/Strontia 0407_0819.xlsx`, byte-identical to the copy in the update zip).

## Disclaimers (Denver Water, must travel with the data)

Both notices below travel together. Cassidi Rosenkrance sent the second one on 2026-09-23 as Denver Water's standard public data terms, to be included in addition to the first.

> The water quality data is provided "as is." Water quality data provided to the user is provisional and subject to change, and the user should not assume that the data has undergone any quality assurance or quality control review. Denver Water makes no warranty of any kind, express or implied, concerning the data, including accuracy, reliability, completeness, timeliness, or usefulness.
> Copyright 2026, Denver Water. https://www.denverwater.org/about-us/how-we-operate/public-records

> COPYRIGHT AND DISCLAIMER: The data and metadata contained herein were prepared by Denver Water for its internal purposes only. Denver Water provides data and metadata as a public service with no claim as to the completeness, usefulness, timeliness or accuracy of its content, positional or otherwise. Denver Water and its employees make no warranty, express or implied, and assume no legal liability or responsibility for the ability of users to fulfill their intended purposes in accessing or using data or metadata or for omissions in content regarding such. The information provided is presented "as is," without warranty of any kind, including, but not limited to, the implied warranties of merchantability, fitness for a particular purpose, or non-infringement. Your use of this information is at your own risk. In providing this information or access to it, Denver Water assumes no obligation to assist the user in the use of such information or in the development, use, or maintenance of any applications applied to or associated with the data or metadata. Any sale, reproduction or distribution of this information, or products derived therefrom, in any format is expressly prohibited.

## The problem

Predict **TOC** and **alkalinity** at the **Foothills Water Treatment Plant influent a few days ahead**, from upstream gage, streamflow, snowpack, and precipitation data. Both analytes affect treatability, so advance warning lets plant operators plan staffing and treatment when outlier water is coming down the South Platte.

The exact horizon is empirical and still moving, and Jake asks that it not be over-emphasized (email, 2026-09-04). The deck used 4 days; he recently got slightly better results with 2, and the September notebooks use 2 for TOC (alkalinity still uses 4). Physically, Denver Water's raw water group models water moving through this stretch in about 4 hours; the multi-day lag that predicts best for TOC and alkalinity is likely mixing and deposition, not transport. What operators need is any heads-up of a day or more.

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

`ExploreDDD_Materials/Data/` (CSV, series run 2022-04-01 to 2026-08-19 in the Sep 4 update)

| File | Columns | Rows |
|---|---|---|
| `FoothillsInfluent.csv` | DATE, TOC_mg_L, Alk_mg_L | 1116 |
| `HoosierPass.csv` | DATE, SWE (SNOTEL snow water equivalent) | 1602 |
| `SouthPlatteFlow.csv` | measDate, Flow_CFS (DWR) | 1603 |
| `SouthPlatteTelemetry.csv` | Date, Flow_CFS, GageHeight_ft, Precip | 1603 |
| `USC00058022.csv` | STATION, DATE, PRCP, SNOW, TMAX, TMIN (NOAA GHCN, ends 2026-08-18) | 1602 |
| `USGS_South_Platte.csv` | Date, site_no, dissolved oxygen, specific conductance, temp, turbidity, pH (max/mean/min) | 1028 |
| `Strontia 0407_0819.xlsx` | Profiling sonde in Strontia Reservoir: timestamp, depth (vertical position), temp, conductivity, pH, ORP, turbidity, chlorophyll, phycocyanin, DO; 16,093 readings over 104 days, 2026-04-07 to 08-19, many depths per cast | |

The Sep 4 update replaced Michigan Creek with a different SNOTEL station because of the erroneous spring 2026 readings (see exploration-notes 7.1). Naming discrepancy to resolve with Jake: the shipped CSV is Hoosier Pass data (station 531, verified against NRCS), but the updated notebooks fetch and read Buckskin Joe (station 938). The superseded `data/MichiganCreek.csv` is kept because the drought analyses (`experiments/snowpack`, `regime`, `analog`) were built on that station's record.

The Strontia sonde is the "new sensor data (sonde?)" from Jake's next-steps note: a real-time reservoir profiling sonde deployed in Strontia, arrival-side data between the USGS river gage and the plant. Jake (Sep 2): it does not need to be pulled into the activity; it is available if there is interest.

`ExploreDDD_Materials/Data/Figures/` holds the model output plots: correlation matrices, feature and permutation importance, and prediction comparisons for TOC, alkalinity, and turbidity, including CatBoost variants.

`Foothills_INF_ML_NoConclusions.pptx` is the intro to the deck Jake presented to Denver Water leadership around July 2026. Conclusions removed.

`reference/` holds the background material Cassidi Rosenkrance sent on 2026-09-14 for attendees, in response to Paul's Sep 11 ask for what plant staff actually do when alkalinity is out of range. Both carry Denver Water's note that they are introductory training material, not official regulatory or controlled documents.

| File | What it is |
|---|---|
| `reference/TOC_and_Alkalinity_Summary.pdf` | Two-page primer: what TOC and alkalinity are, why they matter for treatment (TOC reacts with disinfectants to form regulated disinfection byproducts; alkalinity sets how much chemical it takes to reach the slightly acidic pH where coagulation removes TOC best), and the 60 mg/L alkalinity threshold that moves the required TOC removal between 35% and 25%. Denver Water typically sees source-water TOC of 1.5 to 4.0 mg/L. Ends with links: a YouTube explainer on how treatment works, Denver Water's treatment-process walkthrough (denverwater.org/your-water/treatment-process), CDPHE's quick guide to the DBP Precursors rule (Regulation 11), and CDPHE's disinfection byproducts fact sheet. |
| `reference/DBP-PRE and DBP Rule Training Slides_DDD conference.pdf` | Eight slides summarizing Colorado Regulation 11.24 (DBP precursors: monthly paired TOC and source alkalinity samples, removal ratio or SUVA, running annual average) and 11.25 (TTHM and HAA5 sampling and MCLs, what counts as a violation, 48-hour CDPHE notification). Notes Denver Water is a lower-risk system: chloramination and low raw-water organic carbon. |

## Method, from the deck

- Random forest, trained on lagged features shifted relative to Foothills influent (the deck says 4 days; the September notebooks shift 2 for TOC and 4 for alkalinity, rain 4 and 6)
- Month converted to radians so the model treats January and December as close
- Rolling 7-day averages for flow and precipitation, rolling 3-day for turbidity
- Flow times turbidity as a "loading" parameter
- Spearman correlation matrix used to pick candidate predictors, then combinations tried until best result

Reported results (deck, ~July 2026):
- TOC: R^2 0.59, RMSE 0.29 mg/L, MAPE 9.52%. Peak accuracy prioritized over raw R^2, since TOC is stable most of the year. Currently overestimates due to 2023 in the training data.
- Alkalinity regression: R^2 0.65, RMSE 5.89 mg/L, MAPE 8.34%.
- Alkalinity classification (above or below 60 mg/L): struggles with back-and-forth near the threshold. Jake: "not sold on precision."

**Newer than the deck:** SNOTEL snowpack added as a predictor (Michigan Creek, replaced in the Sep 4 update), and CatBoost tried as an additional model. Neither is described in the slides.

## Open offers from Jake

- Refresh the CSVs closer to the conference, for attendees who want ready-to-code data (first refresh delivered 2026-09-04)
- Walk through the material by email or Zoom

## Related

- Plain-language definitions of every water and statistics term used in this repo: [glossary.md](glossary.md)
- Visualizations: [design-storm-water-system-3d.html](design-storm-water-system-3d.html), a 3D map of the supply system from snowpack to treatment plants, and [design-storm-strontia-springs-brief.html](design-storm-strontia-springs-brief.html), a brief on a real turbidity spike at the Strontia gage on 15 Aug 2026, written before Jake's materials arrived. To view locally: `python3 serve.py 8765` from the repo root (or `python3 -m http.server`), then open `localhost:8765/design-storm-water-system-3d.html`. They load their data from `water-system-3d/` and `strontia-brief/`, so opening the files straight off disk shows an error; map tiles and live gage data also need an internet connection.
- The 3D map is also published as an online demo: **https://exploreddd.com/2026-design-storm-demo/#pw=snowmelt-2026** (this link skips the password prompt). The plain URL https://exploreddd.com/2026-design-storm-demo/ asks for the passphrase, snowmelt-2026. Unlisted; the Foothills influent data is served AES-encrypted and the brief is not published. The live copy is deployed from the Explore DDD website repo; edits here reach it when Paul re-runs the staging script and pushes.
- People: Jake Slawson (Data Scientist, Water Quality & Treatment) and Cassidi Rosenkrance (WQ&T Manager, Lab-Monitoring), Denver Water
- The four-cohort exercise structure is drafted in Explore DDD's planning docs, outside this repository
