# Scenario 2 Plan: Storm Impact Investigation

## Decision

With four hours, take **Scenario 2** and scope it narrowly: one storm (Aug. 14-15, 2026), investigated end to end. Build an investigation workflow, not a prediction model.

> We help Denver Water see how a storm signal moves from the river into Strontia Springs Reservoir: when it arrives and which depths it reaches.

Scenario 1 tends to turn into model tuning, and Scenario 3 risks becoming another map. Scenario 2 fits Event Storming naturally, splits into tasks agents can do, and makes a strong demo.

## Domain primer

### The system

```text
Rain / snowmelt -> South Platte River -> USGS gage 06707525 (just above the reservoir, every 15 min)
  -> Strontia Springs Reservoir (profiling sonde) -> Foothills Treatment Plant -> Denver taps
```

- **Gage**: an automatic river monitoring station.
- **Sonde** (pronounced "sond", rhymes with "pond"): an instrument package lowered through the reservoir. One trip from surface to bottom is a **cast**; its readings form a **depth profile**.
- **Provisional**: USGS publishes readings right away and revises them later. No reading here is final.

### Measurements

| Measurement | Meaning |
| --- | --- |
| Flow (cfs) | How much water is moving; storms raise it |
| Turbidity (FNU/NTU) | Cloudiness. Clear water reads about 1-5. Muddy water is harder to treat and usually carries organic matter |
| Specific conductance | Dissolved minerals; rainwater can dilute it |
| Temperature by depth | Shows whether the reservoir is layered |
| Dissolved oxygen, pH, chlorophyll | Background water health; chlorophyll tracks algae |

### Why depth matters (general limnology, not from Denver Water's materials; confirm with them)

- In summer the warm surface water floats on colder water below it. This layering is **stratification**.
- Incoming river water sinks to the layer that matches its density, so a storm plume can travel at mid-depth while the surface stays clear.
- In autumn the layers mix (**turnover**), which can suddenly change the water the plant draws.
- What matters is whether the affected layer reaches the plant's intake.

## The Aug. 14-15 storm in the data

### River gage (`strontia-brief/series/`)

| Time (MDT) | Observation |
| --- | --- |
| Aug 14, noon | Baseline: turbidity about 3-5 FNU, conductance about 296 |
| Aug 14, 1:00 PM | Conductance reads 38 once, then back to about 300. Likely a sensor glitch, which is why readings stay provisional |
| Aug 14, 7:30 PM | First turbidity bump: 29.9 FNU |
| Aug 15, 12:30-1:45 AM | Main pulse, peaking at **329 FNU** at 1:45 AM |
| Aug 15, 6:00 PM | Back to about 5 FNU |

Upstream at Trumbull (gage 06701900), flow barely moved over the same window (139 to 147 cfs). One possibility is that the runoff entered below that gage; this is a hypothesis to confirm.

### Reservoir sonde (`data/Strontia 0407_0819.xlsx`)

Median turbidity (NTU) of all readings that day, by "Vertical Position" band:

| Date | 0-5 | 5-15 | 15-25 | 25-35 | 35-50 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Aug 13 | 1.1 | 1.5 | 1.7 | 1.8 | 1.9 |
| Aug 15 | 1.2 | 5.5 | 1.8 | 1.8 | 2.0 |
| Aug 16 | 1.3 | **15.6** | 2.5 | 1.9 | 2.0 |
| Aug 17 | 1.6 | 10.2 | 4.9 | 2.1 | 2.0 |
| Aug 18 | 1.4 | 4.0 | **7.0** | 1.8 | 1.8 |
| Aug 19 | 1.4 | 2.8 | 6.0 | 1.8 | 1.8 |

What the table shows: the surface stayed clear. The plume peaked in the 5-15 band on Aug 16, about a day after the river peak. By Aug 18-19 the highest turbidity was in the 15-25 band, which suggests the plume sank or spread; confirm with Denver Water. The deepest band barely changed.

Caveats:

- "Vertical Position" has no unit. The warmest readings are at low values, so it is probably depth below the surface, likely in meters.
- These are daily medians from one event, and some days have fewer readings.
- The data is provisional, so treat this as a case study, not proof.

## What already exists and the gap

`design-storm-water-system-3d.html` already has **"Replay the Aug 14-15 storm"**: radar, Trumbull flow, and gage turbidity, with captions. Its story ends with "the water is already in the reservoir."

**The team's contribution is to continue the story into the reservoir**: show the plume arriving at mid-depth, sinking, and fading. That is what Scenario 2 asks about, and the repo does not show it yet.

## Deliverable: Storm Impact Investigation Viewable

Add a Scenario 2 mode to the 3D map, or build a notebook or static page if that is faster. Either way it needs this analytical backbone:

```text
Storm event selected -> gage response observed -> Strontia depth profiles compared
  -> candidate arrival window described -> impact assessment generated
```

| Scenario 2 question | What we show |
| --- | --- |
| How does the storm affect source-water quality? | Gage turbidity rose from about 3 to 329 FNU; conductance changed |
| When does the impact arrive? | River peak at 1:45 AM Aug 15; mid-depth reservoir peak on Aug 16 |
| What conditions at different depths? | Plume at mid-depth, then deeper; surface and bottom largely unchanged |

**It solves:** a first slice of decision support. It aligns the upstream signal with the reservoir depth response, uses clear domain language, and can be extended toward forecasting.

**It does not solve:** real-time prediction, generalized storm modeling, causal proof, validated travel times, or treatment recommendations. Say so in the demo:

> We did not build a storm-impact prediction model in four hours. We built the first slice of a Scenario 2 decision-support workflow: it follows one storm from the river into the reservoir, depth by depth, and produces an initial impact assessment.

## Questions for Denver Water

1. What depth does Foothills draw water from? This decides whether a mid-depth plume matters.
2. Is "Vertical Position" depth below the surface, in meters?
3. What turbidity at the intake makes operators change treatment?
4. Is the conductance reading of 38 on Aug 14 a known sensor glitch?

## DDD model

**Domain events** (past tense): `PrecipitationObserved`, `StormEventIdentified`, `GageResponseObserved`, `TurbiditySpikeDetected`, `ReservoirProfileCollected`, `DepthChangeObserved`, `ImpactAssessmentIssued`, `ReadingRevised`.

**Entities**: `StormEvent`, `Gage`, `ReservoirCast`, `ImpactAssessment`.

**Value objects**: `Measurement`, `DepthReading`, `DepthProfile`, `ArrivalWindow(earliest, likely, latest)`, `ProvisionalReading`.

**Language rule**: `StormEvent` is the real-world storm. Past-tense names such as `StormEventIdentified` are domain events in the software.

| Bounded context | Owns |
| --- | --- |
| Watershed Observation | Gage and weather readings, provisional status, and the translation of external feeds into our model |
| Storm Event Catalog (core) | What counts as a storm, and each storm's timeline |
| Reservoir Profiling (core) | Casts, depth profiles, layers, and plume position |
| Impact Assessment (core) | Arrival windows, affected depths, confidence, and limitations |

## Four-hour plan

| Time | Work |
| --- | --- |
| 0:00-0:30 | Agree on the framing; run a short Event Storming session using the events above |
| 0:30-1:30 | Load the gage series and the sonde file; group sonde readings into casts and depth bands |
| 1:30-2:30 | Build the timeline and depth-profile views and the impact summary, using turbidity first and temperature as the layering context |
| 2:30-3:15 | Write up the contexts, assumptions, limitations, and next steps |
| 3:15-4:00 | Polish the demo: storm, river signal, reservoir response by depth, domain model, how agents helped, what comes next |

## Team split

| Role | Owns | Output |
| --- | --- | --- |
| DDD facilitator | Context map, events, language | `docs/scenario-2-brief.md` |
| Data wrangler | Sonde loading, casts, depth bands | `storm-impact/analyze_aug14.py` or a notebook |
| Visualization/demo | Timeline, depth view, 3D map mode | `storm-impact/output/` or the map |
| Agent coordinator/narrator | Prompts, README, limitations | `storm-impact/README.md` |

This fork is the team workspace, so no `teams/<name>/` folder is needed.

## Guardrails

- Don't edit `data/`, `scripts/`, `figures/`, or `reference/`.
- Never invent numbers. Label general hydrology knowledge as general knowledge.
- Treat all readings as provisional.
- Keep Denver Water's data terms (`data/TERMS.md`) with any shared output.
- Out of scope: a general prediction model, all storms, new external data, and a from-scratch web app.

## Demo summary

```text
Storm Impact Assessment - Aug. 14-15, 2026 (investigative, provisional data)
River:     turbidity ~3 -> 329 FNU at 1:45 AM Aug 15; back to ~5 by 6 PM
Reservoir: surface clear; plume peaks at mid-depth (5-15) on Aug 16,
           moves deeper (15-25) by Aug 18-19; bottom largely unchanged
Arrival:   about one day from river peak to mid-depth reservoir peak
Open:      intake depth, depth units, operator thresholds
```
