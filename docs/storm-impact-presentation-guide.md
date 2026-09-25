# Presenting the Storm Impact page: a science-fair guide

This guide is for presenting `storm-impact/` at a booth where people walk up, watch
for a few minutes, ask questions, and move on. It assumes you are new to water
treatment. Every number here comes from the repo's files. General water knowledge
that is not in Denver Water's materials is marked as **general knowledge**.

All readings are **provisional**: USGS and Denver Water can still revise them.
Say this out loud at least once per visitor.

---

## 1. Before visitors arrive

- [ ] Start the page from the repository root with `python3 serve.py`, then open
      <http://localhost:8765/storm-impact/>. If the port is taken, run
      `python3 serve.py 8766` and use that port instead.
- [ ] Check the Wi-Fi. The map needs the internet for its background tiles. If
      the internet is down, the page shows a simpler offline map and everything
      else still works.
- [ ] Set **Storm** to **Aug 14-15, 2026**.
- [ ] Drag the splitter (the thin bar between the charts and the map) until the
      map is big enough to see from a few steps back.
- [ ] Drag the time slider back to the start so **Play** tells the story from the
      beginning.
- [ ] Have `docs/ddd-model.html` open in a second tab in case someone asks about
      the software design.
- [ ] Print or keep open the **Key numbers card** (section 5).

---

## 2. The one-sentence pitch

> Denver Water told us their biggest problem is that they don't have
> visualization. We built one page that follows a storm from the river, down
> through the reservoir layer by layer, to the treatment plant, so staff can
> see when its effects will arrive.

If they have 30 more seconds:

> For the August 14-15 storm, the muddy water hit the river gage at 1:45 in the
> morning on Aug 15. The water only takes about four hours to reach the plant's
> intake, but the effects showed up at the plant about a day later. The page
> shows why: the muddy water slid into the reservoir as a layer below the
> surface and took time to spread.

---

## 3. What beginners need to know

### The path the water takes

```text
Rain on the hills
  -> South Platte River
  -> River gage (a sensor station just above the reservoir, reads every 15 minutes)
  -> Strontia Springs Reservoir (a lake behind a dam; a sonde measures it by depth)
  -> Conduit 26 intake at the dam (where water leaves for the plant)
  -> Foothills Treatment Plant (cleans the water; its lab tests it once a day)
  -> Denver's taps
```

### Words you will say

| Word | What it means |
| --- | --- |
| **Storm impact** | The change in water quality a storm causes. It is different from the water itself arriving. |
| **Turbidity** | How cloudy the water is. Clear water reads about 1 to 5. A storm washes in mud and pushes it up. |
| **FNU / NTU** | Units of turbidity. The river gage reports FNU and the sonde reports NTU. **General knowledge:** the two come from slightly different instruments, so compare the shape of the change rather than the exact numbers. |
| **TOC (total organic carbon)** | Dissolved bits of dead plants and soil. It is not dangerous by itself, but the plant must deal with it before adding chlorine (`guide.md`). The plant lab measures it once a day, in mg/L. |
| **cfs** | Cubic feet per second: how much water passes a gage each second. |
| **Gage** | An automatic river monitoring station. USGS runs the ones here. |
| **Sonde** (say "sond," rhymes with "pond") | An instrument package lowered from the surface toward the bottom of the reservoir. Each trip down is a **cast**, and it takes one about every 6 hours. |
| **Depth band** | A slice of the reservoir by depth, such as 5-15 on the depth scale. The page summarises each cast by these slices. |
| **Stratification** | **General knowledge:** in summer, warm water floats on top of cold water, like oil on vinegar. River water slides in at the layer that matches its temperature and density. |
| **Provisional** | Published right away and possibly corrected later. Nothing here is final. |
| **Baseline** | What the reading looked like before the storm. It is the "normal" we compare against. |

### The big idea, in plain words

1. The storm made the river muddy fast: turbidity went from about 3 to 329.
2. That muddy water did **not** spread evenly through the reservoir. It slid in
   as a layer **in the 5-15 depth band, below the surface**. The surface stayed clear, and
   the bottom barely changed.
3. A day or so later, the plant's lab saw TOC rise from 2.0 to 2.5 mg/L.
4. So an operator watching the river has **about a day** of warning for this
   kind of storm, not just four hours.

---

## 4. The 3-minute walkthrough

Do this for each new group. Each step has an action and a script.

### Step 1: set the scene (about 20 seconds)

**Do:** point at the title and the yellow **Provisional data** banner.

**Say:** "This is a real storm from August 14-15, 2026, using Denver Water and USGS
sensor data. The data is provisional, so it could still be corrected. The page
doesn't predict anything. It puts the evidence side by side so an operator can
make the call."

### Step 2: the map (about 30 seconds)

**Do:** point at the map on the right, following the river downstream.

**Say:** "These dots are the stops in flow order: an upstream flow gage at
Trumbull, the river gage just above the reservoir, the reservoir, the dam, the
intake, and the Foothills plant. Colour and size show how far each reading is
from normal: blue and small is normal, shifting through green to orange and big
at the storm's peak. The
dam and the intake are hollow because they have no water-quality sensor."

### Step 3: press Play (about 60 seconds)

**Do:** press **Play** and let the cursor sweep. Keep your finger on the timeline
(section 1) as it moves.

**Say, as it happens:**

- "Here's the river gage. Turbidity jumps in the early hours of Aug 15 and peaks
  at 329 at 1:45 AM. That dashed line marks the river peak."
- "Watch the reservoir row and the reservoir dot. Nothing happens right away. The
  response builds over the next day."
- "The bottom row is the plant lab. TOC steps up from 2.0 to 2.5 on Aug 16."
- "On the map, a dark ring means that stop's peak has passed. You can see the
  rings appear one after another as the storm moves downstream."

### Step 4: the depth chart, which is the "aha" moment (about 45 seconds)

**Do:** point at section 2, **Reservoir by depth**. Hover over the bright band.

**Say:** "This is the part nobody could see before. Time runs left to right and
depth runs top to bottom. Each column is one trip of the sonde. See
this bright stripe? It's the muddy storm water, in the 5-15 depth band. The top stays
clear. Over the next few days, the stripe moves deeper, to the 15-25 band, and
fades."

**Optional:** switch **Color by** to **Temperature**. "Warm on top, cold below.
That layering is why the muddy water travels as a sheet instead of mixing in."

### Step 5: compare storms and land the point (about 25 seconds)

**Do:** point at section 3, **Past-storm comparison**.

**Say:** "We checked a second storm, July 28. The plant saw its TOC bump the same
day there, and about a day later for August. Two storms show a pattern, not a
rule. That's why the page gives the operator evidence instead of an automatic
forecast."

**Close:** "Denver Water said they have sensors everywhere but no way to see them
together. This is one view of the whole path."

---

## 5. Key numbers card

Aug 14-15, 2026 storm (provisional)

| Stop | Normal before | Peak | When |
| --- | --- | --- | --- |
| River gage above Strontia (turbidity) | about 2.5 FNU | **329 FNU** | 1:45 AM, Aug 15 |
| Reservoir, 5-15 band (turbidity, one sonde cast) | about 1.5 NTU | **18.9 NTU** | 12:06 PM, Aug 16, about 34 h after the river peak |
| Reservoir, 5-15 band (daily median) | 1.5 NTU (Aug 13) | **15.6 NTU** | Aug 16 |
| Foothills plant (TOC, daily lab) | 2.0 mg/L | **2.5 mg/L** | Aug 16-17, about 1 day after the river peak |

Jul 28, 2026 storm (provisional)

| Stop | Peak | When |
| --- | --- | --- |
| River gage (daily max turbidity; no exact time) | 151 FNU | Jul 28 |
| Reservoir, 15-25 band | 4.9 NTU | Jul 30, about 36 h after the river peak (river peak assumed at noon) |
| Foothills plant TOC | 2.4 mg/L | Jul 28, the same day |

Other useful facts:

- Water moves from the river gage to the plant intake in **about 4 hours**,
  according to Denver Water's raw water group, as reported in `guide.md`.
- The river gage is only **1.76 km** straight-line upstream of the dam.
- Upstream at Trumbull, flow barely moved during the storm (139 to 147 cfs).
- For operators, an unusual TOC day is one **above 3 mg/L** (`glossary.md`). This
  storm's 2.5 was a noticeable rise but stayed under that line.

**Why two reservoir numbers?** The page's 18.9 is the single highest sonde cast.
The planning doc's 15.6 is the median of all readings that day. Both are correct;
they summarise the data differently. Quote the one that matches what's on
screen.

---

## 6. Questions visitors may ask

**"So can it predict when the next storm will hit the plant?"**
No, and that's on purpose. It lines up the evidence and shows past storms for
comparison, and the operator makes the call. Two storms aren't enough to build
a trustworthy prediction.

**"If the water takes four hours, why does the impact take a day?"**
The water moving and the mud moving aren't the same thing. The depth chart
suggests the muddy water entered as a layer and spread slowly through the
reservoir. That's our reading of the data, not a proven cause. Denver Water's
experts would confirm it.

**"Why does the surface stay clear?"**
**General knowledge:** in summer the reservoir is layered, warm on top and cold
below. Cooler, muddier river water sinks to the layer that matches its density.
You can see the layers when you switch the depth chart to Temperature.

**"What unit is the depth in?"**
The sonde file doesn't say. We're confirming with Denver Water whether it's feet
or metres, so the page shows no unit. The pattern is the same either way: muddy
water in a middle layer, a clear surface, and a bottom that barely changes.

**"Does it matter that the mud is in the 5-15 band?"**
It depends on how deep the plant's intake draws water. That's one of our open
questions for Denver Water.

**"Why is July 28 the same day but August is a day later?"**
We don't know yet. The July river data is only a daily summary, so we don't
know what time the river peaked, and the plant lab samples only once a day.
Timing at the plant is accurate only to the day.

**"Were there any bad readings?"**
Yes. In April and May, the sonde sometimes hit the reservoir bottom at the dam
and stirred up sediment, which gave false readings as high as 2,438 NTU. The
page detects those 11 casts and leaves them out. None of them happened during
these storms. We also saw one conductance reading of 38 at 1 PM on Aug 14,
between readings of about 300. We think it's a sensor glitch, but that's
unconfirmed.

**"Is 2.5 mg/L of TOC dangerous?"**
TOC isn't dangerous by itself. It matters because it reacts with the chlorine
used to disinfect the water (`guide.md`). The operational line in these
materials is 3 mg/L, and this storm stayed under it.

**"Where does the data come from?"**
USGS river gages, Denver Water's reservoir sonde, and the Foothills plant's
daily lab samples, all in this repo. A small script, `storm-impact/build_data.py`,
turns them into the page's data file.

**"How did you use DDD / AI agents?"**
Open `docs/ddd-model.html`. It has the Event Storming timeline, the storm's
events in the past tense (such as `TurbiditySpikeDetected` and
`DepthChangeObserved`), and the bounded contexts. The key language rule is that
"water arrival" and "impact arrival" are different things.

**"What would you build next?"**
Real-time sensors at the intake or in the plant would sharpen timing from a day
to hours. We'd also add more past storms and the actual intake depth.

If you don't know an answer, say so: "Good question. That's on our list for
Denver Water."

---

## 7. What to avoid saying

- Don't say it **predicts** or **forecasts**. Say it **shows** the evidence.
- Don't say the storm **caused** the TOC rise as a fact. Say the rise
  **followed** the storm.
- Don't say "it always takes a day." Say it took **about a day for this storm**.
- Don't present numbers as final. Say they're **provisional**.
- Don't give the depth a unit (feet or metres) until Denver Water confirms it.
- Don't give treatment advice.
- Don't hand out copies of the data or the page. Denver Water's terms restrict
  redistribution (`data/TERMS.md`, and at the bottom of the page).

---

## 8. Booth roles for a team

| Role | Job |
| --- | --- |
| Driver | Runs the laptop: Play, hover, switching storms. |
| Narrator | Gives the walkthrough in section 4. |
| Greeter / Q&A | Brings people over, gives the pitch in section 2, and handles questions from section 6. |

Rotate every half hour so nobody's voice gives out.

---

## 9. If something goes wrong

| Problem | Fix |
| --- | --- |
| "Address already in use" | Run `python3 serve.py 8766` and open port 8766. |
| Blank page or data error | You opened the file directly. Use the `http://localhost` address instead. |
| Map is a plain drawing with no streets | The internet is down, so the offline map is showing. Carry on; the story still works. |
| Map is squashed | Widen the window (the map column hides below 1100 px wide) or drag the splitter. |
| A stop is off-screen on the map | Reload the page. It fits all stops until you pan or zoom. |
| Splitter width is odd | Double-click the splitter to reset it. |
