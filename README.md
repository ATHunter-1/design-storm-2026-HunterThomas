# Design Storm 2026: Denver Water

The Design Storm is a hands-on collaborative challenge at
[Explore DDD 2026](https://exploreddd.com), run with Denver Water. Cohorts work in
small groups with real water utility data on something their Water Quality and
Treatment team actually needs: advance warning of what is coming down the South
Platte before it reaches a treatment plant.

This repository holds the materials Denver Water shared, the models their data
scientist built, and a 3D map of the collection system those numbers describe.

**New to water treatment, or to data science, or to both?** That is the expected
starting point, and nothing here assumes otherwise. [`guide.md`](guide.md) explains
the domain and the models from zero, for someone who writes software and has touched
neither. [`glossary.md`](glossary.md) defines every water and statistics term used
anywhere in the repository. You do not need either to get started, but they are the
fastest way out of any sentence that stops making sense.

Denver Water's data terms apply to everything here. They are at the bottom of this
file and in [`data/TERMS.md`](data/TERMS.md). Denver Water has confirmed the data is
public; please keep the terms with anything you build on it.

## Working as a cohort

The simplest way for a cohort to work together is for one person to **fork this
repository** and share the fork with the rest of the group. The fork becomes the
cohort's collaboration point: everyone else works against it, opens pull requests
into it, and it keeps one shared history of what the cohort tried.

Forking also keeps Denver Water's materials, the guide, and the glossary alongside
whatever you build, so the data terms travel with the work. If a cohort produces
something worth sharing more widely, a pull request back here is welcome.

## Start here

**[The challenge, as Denver Water framed it](reference/Explore%20DDD%202026%20Denver%20Water%20Design%20Storm%20Presentation.pdf)**
(PDF, 12 slides). Cassidi Rosenkrance, their Water Quality and Treatment Manager,
presented this to the room at the kickoff: who Denver Water is, what the water
sector is up against, and the three scenarios below.

**[Denver's Water, in 3D](https://exploreddd.com/2026-design-storm-demo/)** is the
system map on her slide 4, rebuilt as something you can fly through. Reservoirs,
gages, snow stations, treatment plants, and the tunnels that carry water under the
Continental Divide, on real terrain, with live readings behind each marker. It runs
in the browser; click anything. It doubles as a worked example of Scenario 3, and as
a starting point for the viewing application Scenario 1 asks for.

The page is `design-storm-water-system-3d.html` in this repository, if you want to
take it apart or build on it. It fetches JSON, so serve it rather than opening the
file directly:

```
python3 serve.py
open http://localhost:8765/design-storm-water-system-3d
```

## What you are predicting, and why it matters

Water reaches Denver Water's **Foothills treatment plant** after travelling down the
South Platte through Strontia Springs Reservoir. Two things about that water change
how hard it is to treat:

- **TOC** (total organic carbon) is dissolved plant and soil matter. It is harmless
  by itself, but it reacts with the chlorine used to disinfect drinking water and
  forms **disinfection byproducts**, which are regulated. More TOC arriving means
  more work to remove it first.
- **Alkalinity** is the water's resistance to changes in pH. Removing TOC works best
  at a slightly acidic pH, so alkalinity sets how much chemical the plant has to add
  to get there. A regulatory threshold sits at 60 mg/L: below it, the plant is
  required to remove a different proportion of the TOC.

Both are measured by hand from grab samples, which means the plant learns what
arrived after it arrived. Predicting them a few days out from upstream sensors, snow
and weather data would let operators plan staffing and chemical dosing before the
water gets there. That is the problem. Everything else here is in service of it.

## The three scenarios

Cassidi put three to the room. Each question below is hers, quoted from the deck;
the bullets under it are the ways in she suggested. Pick one, or take a scenario
somewhere she did not anticipate.

### 1. TOC and alkalinity predictive model

> Can watershed, hydrologic, and reservoir monitoring data provide enough advance
> warning to accurately predict TOC and alkalinity arriving at Foothills and give
> treatment staff actionable time to prepare?

- Using national datasets upstream of Strontia Springs Reservoir, predict TOC and
  alkalinity concentrations a few days ahead of them hitting the Foothills plant.
- Bring in the real-time Strontia profiling sonde. It sits much closer to the
  Foothills influent, which may improve accuracy but also shortens the lead time.
  Cassidi starred this one on the slide.
- Machine learning enthusiasts: try different models (support vector machines, say),
  different lag times, and feature engineering, and see if performance improves.
- Build a web application for viewing everything behind a prediction (streamflow,
  weather, USGS sonde water quality) alongside the projected TOC and alkalinity.

### 2. Storm and runoff events, and real-time data

> Given current watershed and reservoir conditions, how is an incoming storm or
> runoff event likely to affect source-water quality, when will that impact arrive,
> and what conditions might we expect at different depths within Strontia Springs
> Reservoir?

- Model how precipitation events hit the real-time water quality readings above
  Strontia Springs Reservoir.
- Adapt that model to the Strontia sonde data: how do water quality parameters
  change and distribute by depth in the reservoir, and how do storms and spring
  runoff change that picture?
- Look back through the historical data and model how major precipitation events
  have moved water quality through the system.

### 3. Snowpack and surface water system function

> Develop an interactive model that visualizes how water and water-quality
> conditions move from the watershed through the collection system to the treatment
> plants and evaluate how hydrologic and seasonal events influence that movement.

- Model or visualize how water enters the system and moves through it to the
  treatment plants.
- Focus on one aspect of it, for example historical snowpack and streamflow and how
  those shift year to year, drought against wet.
- Choose a parameter, or a few, and follow them through the system. See whether
  snowpack, rainstorms, or lake turnover change how they travel.

Her framing for all three, from the deck: *use your backgrounds and skillsets to
develop creative solutions.* The scenarios and datasets are ones Denver Water uses
every day to predict, model, and understand what is happening in their collection
system.

## What is in here

### From Denver Water

| Path | What it is |
|---|---|
| [`reference/`](reference/) | Everything Denver Water shared, exactly as sent: Cassidi's kickoff deck, Jake's model walkthrough, and two primers on the water chemistry and the regulations. Has [its own README](reference/README.md). |
| `data/` | The datasets, as CSV and one spreadsheet. Detailed below. |
| `scripts/` | Jake Slawson's six original Jupyter notebooks: two model notebooks and four API grabbers. Unmodified, including the hardcoded paths. |
| `figures/` | The plots those notebooks produce: correlation matrices, feature and permutation importance, prediction comparisons. |

### Added for the cohorts

| Path | What it is |
|---|---|
| `design-storm-water-system-3d.html` | The 3D map. Hand-maintained; no build step. |
| `water-system-3d/` | The generated JSON behind the map, and the scripts that build it. |
| `strontia-brief/` | Basin polygons, river lines, and two gage series the map draws. |
| [`guide.md`](guide.md) | The domain and the models explained from zero, for a developer who has touched neither water treatment nor time-series modelling. |
| [`glossary.md`](glossary.md) | Every water and statistics term used here, defined. |
| [`cohort-prompts.md`](cohort-prompts.md) | Prompts to paste into an AI coding assistant pointed at this folder, staged from first look to modelling. |
| `data-terms.html`, [`data/TERMS.md`](data/TERMS.md) | Denver Water's terms, in the two places they need to be reachable from. |
| `serve.py` | A small static server, because the map fetches JSON and will not run from a `file://` URL. |

## The data

Series run 2022-04-01 to 2026-08-19.

| File | Columns | Rows |
|---|---|---|
| `FoothillsInfluent.csv` | DATE, TOC_mg_L, Alk_mg_L | 1116 |
| `HoosierPass.csv` | DATE, SWE (SNOTEL snow water equivalent) | 1602 |
| `SouthPlatteFlow.csv` | measDate, Flow_CFS (Colorado DWR) | 1603 |
| `SouthPlatteTelemetry.csv` | Date, Flow_CFS, GageHeight_ft, Precip | 1603 |
| `USC00058022.csv` | STATION, DATE, PRCP, SNOW, TMAX, TMIN (NOAA GHCN, ends 2026-08-18) | 1602 |
| `USGS_South_Platte.csv` | Date, site_no, dissolved oxygen, specific conductance, temperature, turbidity, pH (max/mean/min) | 1028 |
| `Strontia 0407_0819.xlsx` | Profiling sonde in Strontia Springs Reservoir: timestamp, depth, temperature, conductivity, pH, ORP, turbidity, chlorophyll, phycocyanin, dissolved oxygen. 16,093 readings over 104 days, 2026-04-07 to 08-19, many depths per cast. | |

Two things worth knowing before you model:

**Readings are provisional.** USGS publishes immediately and revises later. A fresh
API pull can differ from the committed CSVs by a value or two. A forecast built on
a provisional reading inherits that, which is itself an interesting modelling
question: what happens to yesterday's warning when today's input is corrected?

**`MichiganCreek.csv` carries a known artifact.** It shows snow water equivalent of
9.0 on May 12 to 15, 2026 between zero readings, an error in the NRCS feed. Jake
replaced that station with Hoosier Pass in his September update; the file is kept
because it covers a longer record.

## Jake's models

`reference/Foothills_INF_ML_NoConclusions.pptx` is the walkthrough. The short
version: a random forest on lagged upstream features, predicting TOC and alkalinity
at the Foothills influent.

- Features shifted relative to the influent, by 2 days for TOC and 4 for alkalinity,
  and 4 to 6 days for precipitation
- Month converted to radians, so January and December sit next to each other
- Rolling 7-day averages for flow and precipitation, rolling 3-day for turbidity
- Flow times turbidity as a combined "loading" parameter
- Spearman correlation used to shortlist predictors, then combinations tried

Reported results: TOC at R^2 0.59, RMSE 0.29 mg/L; alkalinity regression at R^2 0.65,
RMSE 5.89 mg/L. A classifier asking "is alkalinity below 60 mg/L?" struggles when
the true value sits near the threshold. Later work added SNOTEL snowpack as a
predictor and tried CatBoost alongside the forest.

On the lag: Denver Water's raw water group models water moving through this stretch
in about four hours, so the multi-day lag that predicts best is likely mixing and
deposition in the reservoir rather than transport time. The exact horizon is
empirical and still moving. What operators need is any heads-up of a day or more.

Jake's own framing, and worth keeping in view: these models are under development,
built as a case study in what current data makes possible. Not publication-ready.

## Data terms

Denver Water provided this data under two notices. Both apply to everything in this
repository, and both travel with any dataset or output derived from it.

> The water quality data is provided "as is." Water quality data provided to the user is provisional and subject to change, and the user should not assume that the data has undergone any quality assurance or quality control review. Denver Water makes no warranty of any kind, express or implied, concerning the data, including accuracy, reliability, completeness, timeliness, or usefulness.
> Copyright 2026, Denver Water. https://www.denverwater.org/about-us/how-we-operate/public-records

> COPYRIGHT AND DISCLAIMER: The data and metadata contained herein were prepared by Denver Water for its internal purposes only. Denver Water provides data and metadata as a public service with no claim as to the completeness, usefulness, timeliness or accuracy of its content, positional or otherwise. Denver Water and its employees make no warranty, express or implied, and assume no legal liability or responsibility for the ability of users to fulfill their intended purposes in accessing or using data or metadata or for omissions in content regarding such. The information provided is presented "as is," without warranty of any kind, including, but not limited to, the implied warranties of merchantability, fitness for a particular purpose, or non-infringement. Your use of this information is at your own risk. In providing this information or access to it, Denver Water assumes no obligation to assist the user in the use of such information or in the development, use, or maintenance of any applications applied to or associated with the data or metadata. Any sale, reproduction or distribution of this information, or products derived therefrom, in any format is expressly prohibited.

Data from USGS, Colorado DWR, USDA NRCS, and NOAA is public domain. Map imagery is
Esri and contributors; terrain is Mapzen via AWS; pipeline geometry is
OpenStreetMap contributors; storm radar is the NEXRAD archive via Iowa State
Mesonet.

## Thanks

To **Cassidi Rosenkrance**, who brought Denver Water to the conference, framed the
challenge, recruited her colleagues, and answered every question put to her; to
**Jake Slawson**, who shared his working models and the data behind them; and to
**Jonathan Spitze** and the Water Quality and Treatment team at Denver Water for
backing it.
