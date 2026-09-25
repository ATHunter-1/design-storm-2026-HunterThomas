# Scenario 2 Plan: Storm Impact Visualization

## Decision

Take **Scenario 2** and build a **visualization**. It shows sensor data along the flow path so the user can judge when a storm's impact will reach the Foothills plant. The tool shows the evidence; the operator makes the timing call.

> We help Denver Water see a storm's impact move from the river, through Strontia Springs Reservoir, to the Foothills plant, so staff can judge when it will arrive.

Why this direction:

- Denver Water's biggest problem is visualization, not prediction ("Biggest problem we have is we don't have visualization").
- It directly answers Scenario 2's question of when the impact will arrive.
- Rain at the one weather station barely predicts river turbidity. The rank correlation between daily rain and the next two days' peak turbidity is 0.02 across 1,009 days. A rain-based forecast would need new data.
- Scenario 1 tends to turn into model tuning, and Scenario 3 risks becoming another map.

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
| Aug 14, 1:00 PM | Conductance reads 38 once, then back to about 300. Jake: probably a sensor glitch. Denver Water is still working out how to handle bad readings, probably by excluding outliers |
| Aug 14, 7:30 PM | First turbidity bump: 29.9 FNU |
| Aug 15, 12:30-1:45 AM | Main pulse, peaking at **329 FNU** at 1:45 AM |
| Aug 15, 6:00 PM | Back to about 5 FNU |

Upstream at Trumbull (gage 06701900), flow barely moved over the same window (139 to 147 cfs). One possibility is that the runoff entered below that gage; this is a hypothesis to confirm.

### Reservoir sonde (`data/Strontia 0407_0819.xlsx`)

Median turbidity (NTU) of all readings that day, by "Vertical Position" band (metres below the surface):

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

- "Vertical Position" has no unit in the file. Jake (Denver Water) confirmed it is metres below the surface, which replaces the "feet" we heard earlier in a working session. Metres also fits the bottom-contact depth of about 45-48 behind a 243 ft dam (`strontia-brief/places.json`).
- Jake says the sonde hangs in the middle of the reservoir, roughly 400 m from the intake, which is nearer the dam. It casts every 6 hours, matching the file.
- These are daily medians from one event, and some days have fewer readings.
- The data is provisional, so treat this as a case study, not proof.
- Out-of-range sonde readings happen when the sonde drops to the bottom of the reservoir and stirs up sediment (a team finding). In this file those are 11 casts between Apr 7 and May 5, 2026, with near-bottom spikes of 52 to 2,438 NTU. None fall in Aug 13-19, so the table above is unaffected. `storm-impact/build_data.py` leaves them out.

### Foothills plant (`data/FoothillsInfluent.csv`, daily lab samples)

TOC was 2.0 mg/L through Aug 15, then **2.5 on Aug 16-17**, 2.3 on Aug 18, and 2.2 on Aug 19.

### The whole path

| Stop | Peak signal | When |
| --- | --- | --- |
| River gage above Strontia | Turbidity 329 FNU | 1:45 AM, Aug 15 |
| Strontia reservoir, mid-depth | Turbidity 15.6 NTU (5-15 band, daily median) | Aug 16 |
| Strontia reservoir, at the intake pipe's depth (45 ft, 13.7 m) | Turbidity 32.7 NTU, up from a baseline of 1.64 (single cast) | 6:06 PM, Aug 15, about 16 h after the river peak |
| Foothills plant | TOC 2.0 to 2.5 mg/L | Aug 16 |

The impact reached the reservoir and the plant about a day after the river peak. At the depth of Foothills' primary intake pipe, the sonde saw turbidity jump within about 16 hours (between the 12:06 PM and 6:06 PM casts on Aug 15). The sonde is about 400 m from the intake, so this is the reservoir at the intake's depth, not a reading at the intake itself. The Jul 28 storm roughly agrees: river turbidity hit 151 FNU, and plant TOC was 2.4 that day (up from about 2.0) and 1.9 the next.

Timing at the plant is only accurate to the day, because the lab samples once a day. Two storms, from provisional data, show the pattern, not a proven rule.

**Water arrival vs. impact arrival.** Water travels from the gage to the plant intake in about 4 hours, per Denver Water's raw water group in `guide.md`; Jake confirmed that 4 hours is the travel time to use, not the multi-day model lags. The gage is only 1.76 km straight-line upstream of the dam (`strontia-brief/places.json`). Yet the water-quality impact showed up about a day later, so the delay is likely happening inside the reservoir. Operators care about the impact.

## What already exists and the gap

`design-storm-water-system-3d.html` already has **"Replay the Aug 14-15 storm"**: radar, Trumbull flow, and gage turbidity, with captions. Its story ends with "the water is already in the reservoir."

**The team's contribution is to continue the story through the reservoir to the plant.** Show the plume arriving at mid-depth, sinking, and fading, then the TOC rise at Foothills. That is what Scenario 2 asks about, and the repo does not show it yet.

## Deliverable: Storm Impact Visualization

It can be a static page, a notebook, or a Scenario 2 mode in the 3D map; pick whichever the team can build fastest.

### Layout

1. **Flow-path timeline** (the main view): one row per stop in flow order, on a shared time axis, so the pulse can be seen moving down the page.

   ```text
   River gage above Strontia   turbidity, conductance   ──▲──────────────
   Strontia, by depth band     turbidity                ─────▲───────────
   Foothills plant             TOC (daily lab)          ─────▲───────────
                               Aug 14    Aug 15    Aug 16    Aug 17
   ```

2. **Reservoir depth chart**: time across, depth down, colored by turbidity. It is the only view that shows the mid-depth plume and how it sinks.
3. **Past-storm comparison**: for example, "Aug 14-15: river peak to plant TOC rise, about 1 day; Jul 28: same day." This gives the user a reference for judging timing.
4. **Sensor map**: a small 2D map beside the timeline with the sensors drawn in flow order. Each one highlights when the pulse reaches it on the timeline. The existing 3D map already plots these points and can serve as a fuller view.

### Sensor coordinates

| Stop | Sensor | Lat, lon | Source |
| --- | --- | --- | --- |
| Upstream flow | USGS 06701900 (Trumbull) | 39.2600, -105.2214 | `strontia-brief/places.json` |
| River above the reservoir | USGS 06707525 (turbidity, conductance, and more) | 39.4164, -105.15106 | `places.json` |
| Reservoir | Strontia Springs Reservoir (center point) | 39.42453, -105.13845 | `places.json` |
| Dam | Strontia Springs Dam | 39.43276, -105.12591 | `places.json` |
| Intake | Conduit 26 intake (Strontia Springs Denver intake) | 39.431939, -105.126546 | `places.json` |
| Plant | Foothills Water Treatment Facility | 39.46637, -105.06154 | `places.json` |
| Snowpack (context) | Hoosier Pass SNOTEL 531 | 39.36092, -106.05999 | `water-system-3d/system.json` |

Not in the repo:

- **The sonde's exact position** (ask Denver Water).
- **NOAA weather station USC00058022** and **DWR flow gage PLASPLCO**. Both are available from the public NOAA and Colorado DWR station records if needed.

Always show a notice that readings are provisional and data terms apply.

### How it answers Scenario 2

| Scenario 2 question | What the user sees |
| --- | --- |
| How does the storm affect source-water quality? | Gage turbidity rose from about 3 to 329 FNU; plant TOC rose from 2.0 to 2.5 mg/L |
| When does the impact arrive? | River peak at 1:45 AM Aug 15; reservoir and plant response on Aug 16; past storms for comparison |
| What conditions at different depths? | Plume at mid-depth, right at the primary intake pipe's depth (45 ft, 13.7 m), then deeper; surface and bottom largely unchanged |

**It solves:** Denver Water's stated need to see sensor data together, and the operator's timing question, backed by the evidence.

**It does not solve:** automated prediction, generalized storm modeling, causal proof, validated travel times, or treatment recommendations. Say so in the demo:

> Denver Water told us their biggest problem is visualization. We built a view that lines up the sensors along the flow path, from the river through the reservoir by depth to the plant. It shows one storm's impact arriving about a day after the river peak, so staff can judge the next one.

## What Denver Water told us

- Sensors are "everywhere."
- Their biggest problem is that they don't have visualization.

Notes are in [domain-expert-debrief.md](domain-expert-debrief.md).

## Open questions for Denver Water

1. Is there a real-time sensor at the Foothills intake or in the plant? It would sharpen timing from about a day to hours, and let the tool check itself.
2. ~~What depth does Foothills draw water from?~~ Answered (Cassidi): the primary intake pipe is 45 ft (13.7 m) below the surface, inside the 5-15 m band where the plume travelled. Follow-up answers: there are other intake levels, and 45 ft is the default. The depth below the surface doesn't change, because Denver Water tries to keep the reservoir level the same. Still open: the depths of the other levels, and when operators switch to them.
3. Which of the "everywhere" sensors can we get data from, and which do they look at first after a storm?
4. ~~Where exactly is the sonde in the reservoir?~~ Answered (Jake): the middle of the reservoir, roughly 400 m from the intake, which is nearer the dam; it casts every 6 hours.
5. ~~Is "Vertical Position" in feet or metres?~~ Answered (Jake): metres below the surface.
6. What turbidity or TOC at the intake makes operators change treatment?
7. ~~Is the conductance reading of 38 on Aug 14 a known sensor glitch?~~ Answered (Jake): probably a glitch. Handling of bad readings is still being worked out, probably by excluding outliers.
8. The sonde shows turbidity rising at 5-15 m on Aug 14, from the 12:06 PM cast, before the river gage's first bump at 7:30 PM. What time zone is the sonde's clock in, and could runoff have entered the reservoir without passing the gage?

## DDD model

Visual version: [ddd-model.html](ddd-model.html) (big-picture EventStorm boards, the storm's Event Storming timeline, context map, context contents, and shared vocabulary). Open it directly in a browser.

**Domain events** (past tense): `StormEventIdentified`, `GageResponseObserved`, `TurbiditySpikeDetected`, `ReservoirProfileCollected`, `DepthChangeObserved`, `PlantResponseObserved`, `ImpactArrivalEstimated`, `ReadingRevised`.

**Entities**: `StormEvent`, `MonitoringStation` (gage, sonde, or plant lab), `ReservoirCast`, `ImpactArrivalEstimate`.

**Value objects**: `Measurement`, `DepthReading`, `DepthProfile`, `ArrivalWindow(earliest, likely, latest)`, `ProvisionalReading`, `FlowPathPosition` (the station's order along the path).

**Language rules**:

- Build on the repo's `glossary.md` and `guide.md`. [ddd-model.html](ddd-model.html) maps every glossary water term to its place in the model.
- `StormEvent` is the real-world storm. Past-tense names such as `StormEventIdentified` are domain events in the software.
- "Water arrival" (hours) and "impact arrival" (about a day for Aug 14-15) are different things. The tool is about impact arrival.
- The operator makes the `ImpactArrivalEstimate`. The system supplies the evidence and past storms for comparison.

| Bounded context | Owns |
| --- | --- |
| Watershed Observation | Gage and weather readings, provisional status, and the translation of external feeds into our model |
| Storm Event Catalog (core) | What counts as a storm, each storm's timeline, and past storms for comparison |
| Reservoir Profiling (core) | Casts, depth profiles, layers, and plume position |
| Plant Influent | Daily lab TOC and alkalinity at Foothills |
| Impact Visualization (core) | The flow-path timeline, the depth chart, and the operator's arrival estimate |

## Four-hour plan

| Time | Work |
| --- | --- |
| 0:00-0:30 | Agree on the framing; run a short Event Storming session using the events above |
| 0:30-1:30 | Load the gage series, the sonde file (grouped into depth bands), and the Foothills TOC data onto one time axis; pull sensor coordinates from `places.json` |
| 1:30-2:30 | Build the flow-path timeline, the reservoir depth chart, and the past-storm comparison (Aug 14-15 and Jul 28) |
| 2:30-3:15 | Write up the contexts, assumptions, limitations, and next steps |
| 3:15-4:00 | Polish the demo: the problem Denver Water named, the storm moving down the timeline, the arrival call, the domain model, how agents helped, what comes next |

## Team split

| Role | Owns | Output |
| --- | --- | --- |
| DDD facilitator | Context map, events, language | `docs/scenario-2-brief.md` |
| Data wrangler | Loading and aligning the gage, sonde, and plant data | `storm-impact/` data prep script or notebook |
| Visualization/demo | Timeline, depth chart, storm comparison | `storm-impact/` page or the 3D map mode |
| Agent coordinator/narrator | Prompts, README, limitations | `storm-impact/README.md` |

This fork is the team workspace, so no `teams/<name>/` folder is needed.

## Guardrails

- Don't edit `data/`, `scripts/`, `figures/`, or `reference/`.
- Never invent numbers. Label general hydrology knowledge as general knowledge.
- Treat all readings as provisional.
- Keep Denver Water's data terms (`data/TERMS.md`) with any shared output.
- Out of scope: automated prediction, all storms, new external data, and a from-scratch web app.

## Demo summary

```text
Storm Impact - Aug. 14-15, 2026 (provisional data)
River:     turbidity ~3 -> 329 FNU at 1:45 AM Aug 15; back to ~5 by 6 PM
Reservoir: surface clear; at the intake pipe's depth (45 ft / 13.7 m) turbidity
           1.6 -> 32.7 NTU by 6 PM Aug 15 (~16 h after the river peak);
           plume peaks at mid-depth (5-15 m) on Aug 16,
           moves deeper (15-25) by Aug 18-19; bottom largely unchanged
Plant:     TOC 2.0 -> 2.5 mg/L on Aug 16-17
Impact arrival: about one day after the river peak (Jul 28: same day)
Open:      intake sensor, depths of other intake levels and when to switch, operator thresholds, sonde clock
```
