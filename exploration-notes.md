# Design Storm exploration notes

Working notes from digging into Jake Slawson's Foothills soft-sensor materials, started 2026-08-25. Companion to `guide.md` (what Jake did) and `experiments/README.md` (how we reproduced it). This file is for what we noticed, what we want to chase, and what to ask Denver Water.

Claims marked **(general knowledge)** come from Della's background on water treatment, not from Jake's materials. Verify with Jake or Cassidi before relying on them.

## 1. Domain discoveries

### 1.1 Where the thresholds come from

Jake weights training days with TOC above 3 mg/L and alkalinity below 60 mg/L, and his classifier asks "below 60?". Neither number is explained in the notebooks or deck.

**(general knowledge)** The EPA Stage 1 Disinfectants and Disinfection Byproducts Rule sets required TOC removal by enhanced coagulation from a 3x3 matrix: source-water TOC bands (2 to 4, 4 to 8, over 8 mg/L) against source-water alkalinity bands (0 to 60, 60 to 120, over 120 mg/L as CaCO3). Crossing a band boundary changes the plant's compliance obligation.

If that holds for Foothills, the real domain object is the **joint (TOC, alkalinity) matrix cell**, not two independent numbers. The classifier's "coin flip near 58" problem becomes "how far are we from a regulatory step change", which is a different and better question. Predict the cell.

**Ask Jake:** is 60 the DBPR alkalinity band boundary, an operator rule of thumb, or something else? Same for TOC 3 (the DBPR band starts at 2, so 3 may be an operational trigger).

### 1.2 Upstream is partly Denver Water

**(general knowledge)** Flow at the gage above Strontia is not just weather. Denver Water controls releases from Cheesman Reservoir on the South Platte main stem, and Roberts Tunnel brings Dillon Reservoir water into the North Fork, which joins above Strontia. One of the strongest predictors (`Flow_CFS`, and through it `turb_flow`) is partly a lever the utility holds.

That turns a forecast into a control question: could the plant shape its influent by shaping releases? **Ask:** does the water-quantity side know about this model, and do the two sides talk about quality when planning releases? Cassidi said on Aug 13 that a separate team handles quantity.

### 1.3 Transport time is a domain concept, not a constant

The deck says "lagged by 4 days". The code uses 2 days for USGS in the TOC notebook, 4 in the alkalinity notebook, and 6 for precipitation in both. Jake ties four days to travel time from the sampling area around Strontia to Foothills.

Physically, transport time varies with flow (fast river, short lag), and Strontia Reservoir acts as a mixing buffer that smears upstream signals. **Experiment:** cross-correlate USGS turbidity against Foothills TOC at lags 0 through 10, split by flow tercile. If the best lag moves with flow, the model should carry a flow-dependent lag rather than a fixed shift.

### 1.4 Readings are provisional

Our fresh API pull on 2026-08-25 differed from Jake's CSVs by one revised USGS value plus one extra day. Denver Water's own disclaimer says the water quality data is provisional. A reading has a lifecycle (provisional, then approved), and a forecast built on it inherits that. What does an operator do when yesterday's warning changes because an input was revised? Event-sourcing territory.

### 1.5 Operators already have a manual early-warning habit

Deck, Goals slide: "Craig mentioned Ed and Tad subscribe to USGS WQ alerts from the gage above Strontia Reservoir." So plant staff already watch raw threshold alerts from the same sonde Jake models. His model is an attempt to make that habit smarter. Craig, Ed, and Tad are the people whose decision this is.

**Ask Cassidi:** can one of them (or a treatment plant operator) be among the floating SMEs, or at least be interviewed before the conference? What do they do when a USGS alert fires? That is the operator decision the domain model needs.

### 1.6 The plant's decision, not the number

Jake says "staffing and treatment" and "treatability". The room will want more. **(general knowledge)** High TOC means more organic carbon to strip before chlorination, or disinfection byproduct exceedances; low alkalinity means coagulation loses its buffer and operators add an alkaline chemical. The decision a four-day warning feeds is chemical dosing and shift staffing. Concretely: what changes at the plant when TOC is forecast at 3.1 rather than 2.8? That dose-response is the domain, and the prediction is one input to it.

## 2. What Jake's notes say

Todos and hints found in the notebooks, deck, and email (searched 2026-08-25):

- TOC notebook, last cell: "Next steps are to add in new sensor data (sonde?) and see if we can remove redundant features/simplify the model." The only explicit next-steps note.
- TOC notebook, data load: "may want to model turb later." Done since (six turbidity figures dated Aug 24), notebook not sent.
- Alkalinity notebook: "Try catboost before moving onto classification model." Done.
- Deck: "Can continue to tweak as more data becomes available!" and "Don't expect it to get much better without more data, only a handful of outlier data currently."
- Deck: "Model is not as useful for day-to-day operation." He positions it as a peak detector, not a daily forecast.
- Email: offered to refresh the CSVs closer to the conference, and a walkthrough by email or Zoom.

### 2.1 Reading "new sensor data (sonde?)"

A sonde is a multi-parameter in-situ probe (turbidity, conductivity, pH, temperature, DO). The USGS gage above Strontia is itself a sonde, so the question mark suggests he means a new instrument. Two plausible readings:

1. A Denver Water-owned sonde nearer the plant (Strontia outlet or Foothills intake). Would give continuous arrival-side data instead of one daily lab sample, validate the lag directly, and turn the model into forecast plus confirmation.
2. **(general knowledge)** A sonde with an optical organic-matter channel (fDOM), a near-direct TOC proxy, which would make most of the indirect features (turb_flow, rain, snowpack) unnecessary.

Either way "remove redundant features / simplify" follows: a better signal makes half the engineered features noise. He also has a redundancy problem today: about twenty features chosen by eyeballing a correlation table, several nearly collinear (flow and 7-day flow, turbidity and turb_flow, snowpack and the month encoding). Trees tolerate that, but importance gets smeared across correlated columns, and a ten-feature model is harder to hand to operators than a three-feature one.

The simplify half needs no new sensor. See section 4.

## 3. Exploration ideas

Grouped by what they're for. Numbers are for reference, not priority; the two I'd start with are 1.1 (predict the matrix cell) and 3.1 (score as an event detector).

### Making the model more useful

- **3.1 Score it as an event detector.** Build a catalogue of TOC excursions (episodes above 3) and ask per episode: did the model warn, with how many days of lead? Operators live in episodes. Also likely explains the gap between test R^2 0.56 and cross-validation mean -0.79: the instability probably lives in the peaks.
- **3.2 Lead time vs accuracy.** Run the pipeline at horizons 1 through 7 days and plot the curve. A rough 6-day heads-up refined by a sharp 2-day one may beat a single 4-day number.
- **3.3 Prediction intervals.** CatBoost supports quantile loss. "3.1 mg/L" becomes "80% likely between 2.7 and 3.6, 30% chance above 3." The decision rule then sits on a probability the operator can tune.
- **3.4 Read the outlier year.** Jake says TOC overestimates "due to 2023 in training data". Isolate 2023 (big snowpack) and see what a model trained without it does to 2024 through 2026.
- **3.5 Fix the loose ends and see what moves.** Uniform lag; the January-to-March filter (`month >= 4` under a comment saying "trim to April 2022"); day-of-year computed from the wrong frame. See `experiments/README.md`, "Things noticed in the code".

### Seeing it differently

- **3.6 The lag, drawn.** Stacked aligned timelines (SWE, rain, flow, turbidity, TOC, alkalinity) for one storm event, with the upstream spike and the plant arrival connected. Nobody has an intuition for "four days" until they see it.
- **3.7 Calendar heatmap of hit / miss / false-alarm days.** Makes the three-week run in late July 2026 where the classifier kept saying "low" jump out, and asks what the river was doing then.
- **3.8 Radial seasonal plot.** Month on the circle, as the sin/cos encoding sees it, one ring per year. Shows why the encoding matters and where 2023 sits.
- **3.9 SHAP for one bad day.** Pick the biggest miss and explain which inputs pushed it wrong.

### DDD framing

- Candidate bounded contexts: Watershed Monitoring (USGS, DWR, SNOTEL, NOAA feeds, provisional data), Forecasting (Jake's models), Plant Operations (dosing, staffing, the USGS alert habit), Compliance (the DBPR matrix). The interesting seams are Forecasting to Operations (what a prediction obliges anyone to do) and Operations to Compliance (which cell are we in).
- Ubiquitous language already visible in the code: soft sensor, influent, headworks, loading (`turb_flow`), lag, excursion, provisional. Worth a glossary.

## 4. Ablation study (done 2026-08-25)

Answers Jake's "remove redundant features / simplify" without a new sensor. Code, method, and full tables: `experiments/ablation/README.md`. Deterministic: same rows for every feature set, fixed seeds and threads, `--check` fits twice and compares.

What it found:

- **Alkalinity:** conductance and pH are load-bearing (drop either, R^2 falls from 0.68 to 0.42 or lower). One of `turb_flow`, `turb_3day`, or dissolved oxygen can go for free. Below six features, trees do worse than a one-variable line on conductance (0.50), because trees cannot extrapolate into a test half whose conductance range differs from training.
- **TOC:** the five turbidity columns are one signal; any one can go without losing peak recall (0.82 nearly everywhere). Snowpack is the surprise: dropping it takes the forest from 0.56 to 0.70 and CatBoost from 0.65 to 0.55. Two reasonable models flipping sign on the same feature means the single test half is too small to settle it.
- **A methodological trap worth remembering for the conference:** the first run, without anchoring rows, showed a 3-feature TOC model beating Jake's 10-feature one. It was an artefact of `dropna` keeping 21 more days once a gappy column was removed, which moved the train/test boundary. Every ablation needs the same days.

Next experiment: rolling-origin evaluation (train through year N, test year N+1) so the snowpack question becomes "which years" rather than "which model". Ties to idea 3.4 (the 2023 outlier year).

### 4.1 Rolling-origin evaluation (done 2026-08-25)

Code and full tables: `experiments/rolling/README.md`. Built test-first on top of the ablation package without changing it.

- **The dataset has one and a half informative TOC years.** 2023 had 65 excursion days, 2024 had 60, 2025 had 3, 2026 (to August) had 0. Models trained on 2022 alone missed 2023 almost entirely (recall 0.11 to 0.23). 2024 is the only year where a trained model does real work (R^2 0.46 to 0.69). In 2025 and 2026, R^2 is noise around a flat line and RMSE (0.25 to 0.33 mg/L) is the honest number.
- **Snowpack cannot be settled on this data.** In 2024, the one year that can judge, dropping `swe_7day` moves the forest up 23 points and CatBoost down 11. Jake's "don't expect it to get much better without more data" is right, and the data it needs is another big year.
- **Alkalinity swings -0.5 to +0.8 by year.** 2025 good for every configuration, 2026 bad for every configuration (32 low days, precision under 0.5). Recall stays 0.63 to 0.93 throughout; what moves is precision, and it moves with how much of the year sits near 60. That is the argument for predicting distance to 60 or the compliance cell (section 1.1) rather than the binary.
- **Keep `turb_flow` for alkalinity.** The single-split gain of 1.5 points reverses to an 8 to 13 point loss on the cross-year mean. Ablation deltas of a few points on one split are noise here.
- **For the conference:** any quoted R^2 should carry the year it was measured on. "0.65 on 2024 to 2026, of which only 2024 had excursions" is the true statement.

## 5. Questions for Denver Water

For Jake:
- The turbidity notebook (six figures arrived without it).
- The two lab exports the notebooks actually read (`PL-FTH-INF_cleaned.csv`, `PL-FTH-HW_cleaned.csv`); `FoothillsInfluent.csv` is presumably their daily-median blend.
- Why 60 mg/L and 3 mg/L (section 1.1).
- Why the TOC notebook shifts USGS by 2 days under a comment saying 4.
- What he means by "sonde" (section 2.1).
- Whether the water-quantity side knows about the model (section 1.2).

For Cassidi:
- An operator voice (Craig, Ed, Tad, or a plant operator) among the floating SMEs, or a pre-conference conversation.
- What happens at the plant when a USGS alert fires today.

## 6. Status

- 2026-08-25: notebooks reproduced locally, guide written, this file started.
- 2026-08-26: ablation and rolling-origin done (sections 4, 4.1). Drought-year analysis and glossary added (sections 7, 8).
- 2026-08-28: wet/dry measure defined with sources (section 9). All four drought explorations built test-first and run (sections 7.4 to 7.7; packages `experiments/snowpack`, `novelty`, `regime`, `drivers`, `analog`; 101 tests). The May 12 to 15 2026 SNOTEL readings are an artifact still present in the NRCS feed (7.1, 7.7); question for Jake.

## 7. The 2026 drought year and what it means for the model

Paul's question (2026-08-26): the snowpack was very light this year; how might that affect the model over the next year, and how could we explore it?

### 7.1 What the data says, by year

Snowpack is grouped by **water year** (October 1 to September 30, see section 8), computed by `experiments/snowpack/run.py` from `data/MichiganCreek.csv` (2026-08-28). Peak date is the first day the maximum is reached; melt-out is the first zero reading after the peak. The earlier calendar-year table was built from the newest-first file, so its peak dates were the last day of each plateau rather than the first.

| Water year | Peak SWE (in) | Peak date | April 1 SWE (in) | Melt-out | Days peak to melt-out | Days with data |
|---|---|---|---|---|---|---|
| 2022 (from Apr 2) | 8.4 | Apr 18 | none | May 28 | 40 | 182 |
| 2023 | 9.6 | Apr 24 | 9.1 | May 28 | 34 | 365 |
| 2024 | 13.1 | May 12 | 12.0 | Jun 4 | 23 | 366 |
| 2025 | 10.0 | Apr 5 | 9.3 | May 31 | 56 | 364 |
| 2026 (to Aug 23) | 9.0 | May 12 | 0.8 | May 16 | 4 | 327 |

Flow, TOC, and alkalinity stay by **calendar** year (they do not straddle a winter, and the sonde has no January to March readings anyway):

| Calendar year | Max flow (cfs) | Mean flow | TOC max | Days TOC above 3 | Alk mean | Days Alk below 60 |
|---|---|---|---|---|---|---|
| 2022 (from Apr) | 970 | 494 | 3.39 | 11 | 58.3 | 118 |
| 2023 | 1090 | 396 | 7.30 | 70 | 54.4 | 241 |
| 2024 | 1390 | 473 | 6.40 | 109 | 56.6 | 140 |
| 2025 | 734 | 386 | 3.10 | 3 | 60.7 | 112 |
| 2026 (to Aug) | 620 | 332 | 2.70 | 0 | 63.6 | 35 |

The 2026 snow row needs a caveat. Its "peak" is four readings of 9.0 on May 12 to 15, with 0.0 on May 10 and 11 and 0.0 again from May 16 onward. A nine-inch snowpack does not appear on bare ground and vanish within four days in May; those rows look like a sensor or transmission artifact, and the earlier "9.0, May 15, gone by May 29" line (with the "latest peak, fastest melt-out" reading built on it) came from them. With those four days masked, water year 2026 peaks at 4.9 in on March 16 and reaches zero on April 12 (27 days). The functions report the file as it is; whether to drop those rows is a question for Jake (section 5), and the analog-years exploration, which fetches the same station's full record from NRCS, can check whether the QC'd data still shows them.

Reading: by the real snow curve, 2026 at Michigan Creek was the lightest year in this window by a wide margin (peak 4.9 in against 8.4 to 13.1; April 1 SWE 0.8 in against 9.1 to 12.0) and the earliest to melt out. Downstream it is the quietest water in the record: lowest flow, zero TOC excursions, highest alkalinity. Michigan Creek is one station; Paul's "very light" holds at this site and may hold basin-wide. Wet/dry labels from `snowpack/run.py` with the in-kit median (9.2 in, the section 9 fallback): 2023, 2024, and 2025 wet; 2026 dry at 9% of median; 2022 unlabelled (no April 1 reading).

### 7.2 Two ways a drought year hurts the model

**Mechanical: unseen feature space.** Zero SWE in June, flow below any training day, and month encodings that used to co-occur with a melt pulse. Tree models cannot extrapolate: an unfamiliar day is routed to whichever leaf looks closest and gets that leaf's answer with full confidence. Likely why 2026 alkalinity precision fell under 0.5 (section 4.1).

**Physical: the wrong physics.** In a snow year, TOC arrives as the spring flush and the loading term (`turb_flow`) carries the signal. In a dry year the flush is small and TOC events come from summer convective storms (the 6-day rain lag doing the work) and, **(general knowledge)**, from burn-scar runoff. The model was trained on 2023 and 2024, both snow-flush years, so the rules it learned may be the wrong rules for a thunderstorm-driven year. A model can be numerically fine on days it has seen and structurally wrong about the days that matter next.

**Carry-over (hypothesis, not fact).** A dry year leaves unflushed organic material in the watershed, so the next wet year's first flush carries two years' worth and is bigger than snowpack alone predicts. If true, 2027's TOC peak could surprise a model that thinks "peak TOC scales with peak SWE." One question to a plant operator confirms or dismisses this.

### 7.3 Explorations, in order

1. **Novelty score per day.** For each 2026 day, count how many features fall outside the training range (or beyond the 5th/95th percentile). Plot prediction error against it. If error climbs with novelty, the errors are extrapolation, quantified, with the specific out-of-range inputs named. Small addition on top of `experiments/rolling/`.
2. **Regime-split evaluation.** Label years wet or dry by April 1 SWE (water-year grouping). Train on wet, test on dry, and the reverse. Answers "does a snow-year model transfer to a drought year" directly.
3. **Driver attribution.** Label each TOC excursion day snowmelt-driven (SWE falling, flow rising) or rain-driven (rain spike, flow flat). Score recall per driver. "Catches 80% of melt peaks, 20% of rain peaks" is a sentence an operator can act on.
4. **Analog years.** SNOTEL 937 and the DWR gage go back decades; the USGS sonde only to 2022. Find prior years whose snow curve resembles 2026 (2002, 2012, 2018 are the usual Colorado suspects; verify from the SNOTEL record) and see what the river did that year and the next. No TOC labels, but it shows whether "light, late, fast" has precedent.

Start with 1 and 3: pure functions over data we have, buildable test-first like `rolling/`, and each produces a picture Jake could put in front of plant staff.

Questions this adds for Denver Water: is burn-scar runoff a factor at Strontia; do operators see a bigger first flush after a dry year; how did 2026 operations differ (releases, source blending) from a normal year.

### 7.4 Novelty score (done 2026-08-28)

Item 1 of 7.3. `experiments/novelty/`: for each test day in each rolling-origin fold, the number of Jake's inputs outside the training min/max (and, softer, beyond the training 5th/95th percentile), against that day's absolute error. Same rows, folds, fitters, and seeds as `rolling/`. README has the tables; `figures/<target>-error-vs-novelty.png` the pictures.

**2026 has no min/max novelty.** Every 2026 test day scores 0 for both targets (135 TOC days, 133 alkalinity days, every feature inside the training box). The "mechanical" story in 7.2 does not hold for the model's actual inputs: `swe_7day` is 0 every summer in training, so 0 in June 2026 is familiar, and 2026's lowest `flow_7day_avg` (188 cfs) is above the training minimum (175 cfs). 2026 is a quiet year inside the envelope. MAE at count 0: TOC 0.23 (forest) and 0.19 (CatBoost) mg/L; alkalinity 4.37 and 4.28 mg/L.

**The softer count finds the alkalinity problem.** Binning 2026 on the 5th/95th count: alkalinity days with no input in a tail have MAE 3.0 to 3.1; days with two inputs in the tails (14 days) have 9.0 to 9.1, for both models (Spearman 0.40 to 0.41). The tail inputs are `pH_Median` above the training 95th percentile on 35 days and `flow_7day_avg` below the 5th on 26, with `turb_flow` below on 19. High pH with low flow is the combination the models saw on under 5% of training days, and it is where they miss. For TOC the same binning is flat (0.2 to 0.3 mg/L at every count; `turb_flow` low on 25 days is the main tail); there is nothing to explain in a year with no excursions.

**Where extrapolation really shows: TOC 2023.** Trained on 2022 alone, MAE climbs monotonically with min/max count, 0.53 mg/L on the 107 days at 0 to about 4.0 on the 5 days at 6 (both models within 0.05 of each other at every count). The most-outside inputs were `turb_flow` (33 of 191 days), `month_cos` (27), `turb_3day` (25), `turb/cond` (22). That is the 2023 flush, which 2022 could not teach. In 2024 only `swe_7day` went outside (52 days, the big snow year) with a modest MAE rise; 2025 had no outside days. Alkalinity 2023 and 2024 had outside days on turbidity, flow, and DO inputs and MAE did not rise with them, matching the ablation's finding that those inputs carry little.

What this changes: the 7.2 "physical" explanation (a dry-year regime the models did not learn) is the one left standing for 2026 alkalinity, and the regime split (7.3, item 2) is the test for it. The 7.2 first paragraph's "zero SWE in June, flow below any training day" should be read as a description of the year, not of the model's inputs.

### 7.5 Regime split (done 2026-08-28)

Item 2 of 7.3. `experiments/regime/`: each in-kit water year labelled by the section 9 rule (April 1 SWE at Michigan Creek below 75% of the period-of-record median, 10.05 inches over 28 years from the `analog/` fetch, is dry), then Jake's full feature set trained on one regime and scored on the other with the ablation fitters. Labels: 2023 (9.1 in, 91%), 2024 (12.0, 119%), and 2025 (9.3, 93%) wet; 2026 (0.8, 8%) dry; 2022 unlabelled (no April 1 reading) and its 171 to 173 rows excluded. The suspect May 2026 readings do not touch April 1, so they do not touch the labels. README has the tables and `results/labels.csv` the fractions, so the 75% line can be second-guessed from the file.

**One dry year.** The dry side is water year 2026 alone (October 2025 to August 23, 2026; 187 anchored rows) in both directions, so wet to dry is a single-year test and dry to wet a single-year training set, and both are indicative only.

**Wet to dry (train 2023 to 2025).** TOC: RMSE 0.30 (forest) and 0.27 mg/L (CatBoost) on a year with no day above 3 mg/L; the forest raised two false alarms, CatBoost none. R^2 is -3.5 and -2.7 because the year is flat (range 1.2 to 2.7), so the error is the number to read, and it matches the rolling 2026 fold. Alkalinity: R^2 0.08 and -0.70, RMSE 4.2 and 5.7 mg/L, recall on the 55 low days 0.62 and 0.35, precision 0.54 and 0.61.

**Dry to wet (train 2026 only).** TOC: recall 0 on 128 excursion days for both models (predicted range 1.7 to 2.4 against actual to 7.3), RMSE 1.2. Alkalinity: R^2 -0.04 and 0.12, RMSE 10.9 and 10.0, recall 0.42 and 0.63 with precision 0.92 to 0.94 on a test set that is 68% excursion days. A model that saw only 51 to 75.5 mg/L cannot reach 39 or 92.

**Answer.** A wet-trained model holds up on the dry year for TOC in the only sense available (it reports a quiet year as quiet, with almost no false alarms, but there was no dry-year flush to catch) and does not hold up for alkalinity (R^2 at or below zero, 4 to 6 mg/L error, half its low-day alarms wrong). Taken with 7.4, which found 2026's inputs inside the training box, this is the 7.2 "wrong physics" story showing up in the target rather than the inputs: the same conductance and pH read differently in a baseflow year. The reverse direction is an extrapolation failure by construction and is what a refit on 2026 alone would do. The TOC side of the drought question still needs a dry year with rain-driven excursions, which 2026 did not supply.

### 7.6 Driver attribution (done 2026-08-28)

Item 3 of 7.3. `experiments/drivers/`: consecutive TOC days above 3 mg/L on the anchored index (the days the models were scored on, 2023 to 2026) grouped into episodes; each episode labelled from the full frame over its days plus the week before (snowmelt if `swe_7day` fell and flow at the peak was at or above the median; rain if `precip_7day` hit the 90th percentile and flow was below); each model's rolling-origin predictions checked for any day above 3 from four days before the start to the end. README has the tables.

**Five episodes.** Three snowmelt (2023 May 14 to Jul 17, 65 days, peak 7.3; 2024 Apr 15 to Jun 7, 54 days, peak 6.4; 2025 Jun 11, one day), one rain (2025 May 16 to 17, two days), one unclear (2024 Aug 28 to Sep 2, six days, peak 3.3: a rain spike with no snow, on a river still above median flow, so the rule declined to name it).

**Both models catch 3 of 3 melt episodes and 1 of 1 rain episode, and miss the unclear one.** So "recall 0.82" becomes "every melt episode, late": the forest first crossed 3 mg/L two days into the 2023 episode and thirteen days into 2024's; CatBoost five and four days in. The two short 2025 episodes were called one and four days early. Day-level recall in 4.1 (0.23 and 0.11 for 2023) and episode recall answer different questions: the episode number is the operator's sentence ("it will tell you the flush has started"), the day number is how much of the flush it tracks.

**For the drought question**, the one late-summer, no-snow episode in the record is the one both models missed, all six days. One episode is not a rate, but it is the shape a dry-year excursion would take, and models trained on melt-shaped years did not see it. The useful next data is the rain-driven episodes of a dry year, captured as they happen.

**Coverage caveat.** 54 raw excursion days (from `FoothillsInfluent.csv`) fall outside the anchored index: 5 in 2023 (Aug 5 to 9) and 49 in 2024 (Jun 8 to Aug 27), the latter because the USGS sonde columns are absent, so the 2024 episode's "end" on Jun 7 is where the sonde record stops, not where TOC fell. 2024 was most likely one long episode into September. Definition note: with flow as the tiebreaker, `mixed` cannot occur; the 2025 May episode (SWE falling and a rain spike on a low river) is the case that would have wanted it.

### 7.7 Analog years (done 2026-08-28)

Item 4 of 7.3. `experiments/analog/`: the whole Michigan Creek SNOTEL record (NRCS, 28 water years, 1999 to 2026) and the whole PLASPLCO gage record (DWR, 127 water years from 1900) fetched once and committed; each water year summarised by snowpack shape (peak SWE, day of the water year it peaked, days from peak to melt-out) and flow (max, day of max, mean); past years ranked by standardised distance from 2026 on the three shape numbers. README has the tables and the fetch details.

**The four suspect May 2026 readings are in the NRCS record too** (0, 0, 9, 9, 9, 9, 0 for May 10 to 16), so the service has not corrected them as of the fetch date. Ranked on the file as fetched, 2026 (peak 9.0 on May 12, gone in 4 days) is closest to 2004, 2015, 2010, 2024, and 2005: ordinary-to-good snow years that peaked late and melted fast, none dry, each followed by a near-normal or wet year. That is the shape of the artifact, not of the year. With those four days masked, 2026 is peak 4.9 on March 16, April 1 SWE 0.8, bare by April 12, and its nearest years are 2002 (distance 1.74; peak 6.8 on March 27, 45 days to melt-out, April 1 6.6; flow max 748, mean 399), 2022 (2.53; 8.4, April 18, 40 days; 970, 422), 2018 (2.56; 9.1, April 21, 26 days, April 1 6.3; 751, 382), then 2023 and 2017. 2012 is eighth, kept out by its 64-day melt tail.

**Precedent in kind, not in degree.** The known Colorado dry years are the neighbours, so the regime is familiar to this station. The size is not: 2026's masked peak is 1.9 inches below the lightest year on record, its April 1 reading 5.1 inches below the lowest, and its melt-out 22 days earlier than the earliest (2012, May 4). Downstream, 2026's 620 cfs maximum (July 18) is the lowest since 1999 and the third lowest in 127 water years, after 1963 (530) and 1902 (593); mean flow 323 cfs through August 27 is the lowest since 1999.

**What followed.** Snow returned to median or above the next year for 2002 (2003: 13.6), 2018 (2019: 14.6), 2022 (2023: 9.6), and 2023 (2024: 13.1); 2017 was followed by dry 2018 (9.1). The river did not always follow: after 2002, water year 2003 peaked at only 750 cfs with the third-lowest mean since 1999 despite the snow **(general knowledge, hypothesis: upstream reservoirs refilling; section 1.2)**; after 2018 the gage reached 1540; after 2022 it reached 1090 in the biggest TOC year the sonde has seen (7.1). The one dry-to-wet transition with TOC labels is the big-flush case, which is consistent with the 7.2 carry-over hypothesis without proving it. In 2002, 2003, 2018, 2022, and 2026 the annual flow maximum came outside the melt window (June 1, then September 8, 16, September 2, July 18), the flow-side signature of 7.2's rain-or-release regime. No TOC or alkalinity claim is made about any analog year.

Side result for section 9: the period-of-record median April 1 SWE at Michigan Creek (1999 to 2026) is 10.05 inches, so the 75% line is 7.5 inches; below it are 2012, 2018, 2002, 2004, 2013, and 2026, with 2022 just above at 7.6.

## 8. Glossary for the non-water reader

Plain-language definitions used in this file and the analysis. Items marked **(general knowledge)** are Della's background, not Jake's materials.

- **Snowpack.** Snow lying on the mountains through winter. In the Colorado Front Range most of the year's water arrives as snowmelt, so the snowpack is the real reservoir.
- **SWE, snow water equivalent.** If this snow melted right now, how deep a layer of water would it make? Depth of snow is useless (powder vs packed), so SWE is the measurement. Michigan Creek's 2026 peak of 9.0 means nine inches of water sitting on the hillside as snow.
- **SNOTEL.** The federal network of automated mountain snow stations ("snow telemetry"). Michigan Creek is station 937. One point in a large watershed: a proxy for the basin, not the basin.
- **Peak and melt-out.** SWE climbs all winter, reaches a maximum (peak), then falls to zero (melt-out). The shape of that curve is the year's water story: high, late, slow means a long strong river; low and gone in two weeks means a short pulse and a thin summer.
- **April 1 SWE.** The traditional comparison date, usually near peak. "How was the snowpack this year" means "April 1 SWE vs average."
- **Water year.** October 1 to September 30. Snow that falls in November melts the following May, so calendar years split one winter in half. The table in 7.1 grouped by calendar year, which is why earlier years show snow still present on December 31: that is the next winter's first snow. Regroup by water year before analysis.
- **cfs, cubic feet per second.** River flow. 620 cfs means 620 cubic feet of water pass the gage each second.
- **Flush.** The rising melt river scours banks, forest floor, and stream bed and carries a season's accumulated dead plant material downstream in a few weeks. That is the spring TOC spike. "First flush" is the same idea for any storm after a dry spell.
- **Baseflow.** What the river is when it is neither raining nor melting: groundwater seeping from rock. Groundwater has been in contact with minerals, so it carries more of what makes alkalinity. Less melt means less dilution, so a dry year runs higher alkalinity, exactly as 2026 shows.
- **Convective storms, monsoon.** Summer afternoon thunderstorms. In July and August, moist air from the south (the North American monsoon) produces short, intense downpours over small areas. Little annual water, but an inch on one hillside in an hour flushes sediment and organic matter fast.
- **Burn scar (general knowledge).** Land where wildfire removed vegetation; rain runs straight off carrying ash, soil, and organic carbon. Denver Water's watershed has several (Buffalo Creek 1996, Hayman 2002). Ask Jake whether it matters at Strontia.
- **Regime.** A stretch of time where one mechanism dominates. A snow-flush year and a drought-plus-thunderstorm year are two regimes: same river, different physics producing the TOC.
- **Extrapolation.** Answering for inputs outside anything seen in training. Straight-line models try (badly); tree models cannot, and instead return the nearest remembered answer with full confidence.
- **Novelty score.** For one day, how many of its inputs sit outside the training range. A cheap way to flag days where the model is extrapolating.
- **Excursion.** A day beyond the operational threshold: TOC above 3 mg/L or alkalinity below 60 mg/L, the days Jake's sample weights emphasise and operators care about.

See also `guide.md` sections 1 to 3 for TOC, alkalinity, soft sensor, turbidity, and specific conductance, and section 10 for R^2, RMSE, MAPE, and MAE.

### Statistics terms used in sections 4 to 7

- **MAE, mean absolute error.** The typical size of a miss in the target's units, as a plain average: each day's miss with the sign dropped, averaged. Unlike RMSE it does not square the misses, so one bad day cannot dominate a group. Used when comparing groups of days (novelty bins, regimes).
- **Median.** The middle value when you sort a list. Half the values are above it, half below. Less sensitive to one extreme value than the mean, which is why the wet/dry reference is a median.
- **Percentile, 5th and 95th.** The value below which 5% (or 95%) of the training days fall. A test day "beyond the 5th or 95th percentile" on some input is in a corner the model saw on fewer than one training day in twenty. Softer than "outside the minimum and maximum", which means never seen at all.
- **Fold.** One train/test split. Rolling-origin folds (section 4.1) train on every year before N and test on year N; regime folds (7.5) train on wet years and test on dry, or the reverse.
- **Anchored rows.** The rule that every feature set is scored on the same days: keep only days where all of Jake's full feature set is present, then remove columns. Without it, dropping a column with gaps changes which days survive, and the comparison is partly a different test set (section 4).
- **Spearman correlation.** A number from -1 to 1 saying how consistently two things rise together, based on rank order rather than exact values. 0.4 means "more novelty tends to mean more error, loosely"; 1 would mean perfectly in step.
- **Standardised (z-score).** Each column rescaled so its mean is 0 and its spread is 1, so that inches of snow and days of melt can be compared on one footing before measuring distance between years (7.7).
- **Monotonically.** Only ever moving one way. "MAE rises monotonically with novelty count" means each step up in novelty brought a higher error, with no dips.
- **Recall, precision, false alarm, base rate.** Recall: of the days that really were excursions, what share the model flagged. Precision: of the days the model flagged, what share were real. A false alarm is a flagged day that was not real. The base rate is what precision would be if the model flagged every day (59% for alkalinity below 60, since that is how often it happens); precision near the base rate means the flags carry little information. Full explanation in `guide.md` section 11.
- **Lead (days).** For an episode, the gap between the first day the model flagged it and the day it actually began. Negative means the warning came before the episode; positive means the model noticed after it had started.

## 9. Wet and dry years: the measure

Decided 2026-08-28 with Paul, for the regime-split exploration (section 7.3, item 2).

### The rule

A water year is **dry** if its April 1 snow water equivalent (SWE) at the Michigan Creek SNOTEL station is below 75% of the period-of-record median April 1 SWE at that station; otherwise **wet** (near normal or above). The 75% cutoff is a project choice and lives in one named constant (`DRY_BELOW_FRACTION` in `experiments/snowpack/wateryear.py`); change it there and every downstream result changes with it.

### Why each piece

- **April 1.** The conventional snowpack comparison date in western US water management, close to the seasonal peak at most stations. NRCS's water supply forecasts key on it. Source: NRCS Snow Survey and Water Supply Forecasting program, https://www.nrcs.usda.gov/programs-initiatives/sswsf-snow-survey-and-water-supply-forecasting-program (checked 2026-08-28).
- **Percent of median, not an absolute number.** NRCS reports basin and station snowpack as a percentage of the long-term median, so "far below normal" is a comparison to the station's own history, not to a fixed inch count. Same source.
- **Period of record, not the in-kit years.** Jake's kit holds 2022 to 2026 only. The four years with an April 1 reading are 9.1, 12.0, 9.3, and 0.8 inches. Three of those sit within 0.2 inches of each other, so a median cut through them is "2026 versus the rest" and drops 2023 (the biggest TOC and second-biggest flow year) on the dry side by 0.1 inch. That is the wrong picture. The long record comes from the same station via the NRCS AWDB REST API that Jake's `SNTL_grabber.ipynb` already uses (https://wcc.sc.egov.usda.gov/awdbRestApi/swagger-ui/index.html, station triplet `937:CO:SNTL`, element WTEQ). Station page: https://wcc.sc.egov.usda.gov/nwcc/site?sitenum=937.
- **One station.** Michigan Creek is the station Jake chose as a predictor. It is one point in a large basin, so the label is "the snowpack the model saw", not a basin-wide index. A basin index would be a better regime label and is a follow-up.
- **75%.** Chosen, not sourced. It is meant to separate "far below normal" from everything else with the few years available. If the long record shows several years in the 75 to 90% band, reconsider. Record the fraction of median for every year in `labels.csv` so the cutoff can be second-guessed from the table.

### Fallback

If the long record cannot be fetched or has fewer than 20 water years with an April 1 reading, the regime split uses the median of the in-kit years and says so in its README and `labels.csv`, with the 2023 caveat above.

### Alternatives considered, not used

1. **Peak SWE with melt-out timing.** Captures the shape of the season (when it peaked, how fast it went) rather than one number, but has no standard reference to compare against. Note that the "late peak May 15, gone by May 29" reading of 2026 that first motivated this option came from four artifact rows in the kit file (section 7.1); by the real curve, 2026 peaked at 4.9 inches on March 16 and was gone by April 12, so its distinctive feature is simply how little snow there was and how early it went.
2. **Flow-based.** Max or mean flow at the DWR gage above Strontia (`PLASPLCO`, https://dwr.state.co.us/Tools/Stations/PLASPLCO; API help https://dwr.state.co.us/Rest/GET/Help). Separates 2023 and 2024 (1090, 1390 cfs) from 2025 and 2026 (734, 620) cleanly, but it is downstream of the question: flow is partly Denver Water's own releases (section 1.2), and it is what the model predicts from, so labelling by it risks circularity.
3. **In-kit median April 1 SWE.** Rejected as the primary measure for the reason above; kept as the fallback.

### Data used

- `data/MichiganCreek.csv` (Jake's kit): April 1 SWE 2023 9.1, 2024 12.0, 2025 9.3, 2026 0.8; no April 1 2022 reading (file starts 4/2/2022). Grouping by calendar year in section 7.1 is being replaced by water-year grouping (section 8, "Water year").
- `data/SouthPlatteFlow.csv` (Jake's kit): flow maxima by calendar year, section 7.1.
- Period-of-record Michigan Creek SWE: to be fetched by the analog-years exploration into `experiments/analog/data/MichiganCreek_full.csv`.
