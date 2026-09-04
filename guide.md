# What Jake is doing, from the ground up

A plain-language walkthrough of the Denver Water materials for someone who writes software but has never touched water treatment, statistics, pandas, or Jupyter. Written 2026-08-25 from Jake's notebooks, deck, and email, plus our local runs in `experiments/`; revised 2026-09-05 for his Sep 4 update (data through Aug 19, shorter TOC lags, replacement SNOTEL station, bug fixes). Where this fills in water chemistry Jake never spelled out, it says so. Terms used across the rest of the repo (snowpack, water year, MAE, recall, and the like) are collected in [glossary.md](glossary.md).

## 1. The physical system

Snow falls in the Rockies. It melts in spring and runs into the South Platte River. The river flows down to **Strontia Springs Reservoir** southwest of Denver, and from there the water goes to the **Foothills Water Treatment Plant**, which cleans it and sends it to Denver taps.

Water takes time to move through that, and the "how long" turns out to be subtle. Denver Water's raw water group models water moving from the measurement point (a sensor just above Strontia) to the plant intake in about four hours. Yet the models predict best with the upstream readings lagged by days, not hours: the deck used 4 days, Jake recently got slightly better results with 2, and he thinks the multi-day scale is about mixing and deposition in the reservoir rather than raw travel time. The exact number is still moving and he asks that it not be leaned on. The premise survives in a looser form: what the river looked like a couple of days ago tells you something about what the plant receives today, and any heads-up of a day or more is useful to operators.

## 2. What the plant cares about

The water arriving at a plant is not the same every day. Treatment is a chemistry problem and the recipe changes with what is in the water. Two of the quantities that change the recipe are the ones Jake predicts.

**TOC, total organic carbon.** Dissolved dead plant material: leaves, soil, forest litter washed in by rain and snowmelt. Not dangerous in itself. The problem is that the plant adds chlorine to kill pathogens, and chlorine reacts with organic carbon to form **disinfection byproducts**, which are regulated for health reasons. High TOC means more work stripping carbon before chlorination, or a failed compliance test. (Jake's other project folder is named `DBP_Python2026`, disinfection byproducts. This is my general knowledge, not his words.)

**Alkalinity.** The water's ability to resist changes in acidity, mostly from dissolved minerals picked up from rock. The main cleaning step, **coagulation**, doses the water with acidic chemicals that make fine particles clump so they can be filtered out. Low alkalinity means not enough buffering, the acidity swings, and coagulation stops working properly, so operators have to add something alkaline to compensate. (Again general knowledge; Jake only says "treatability".)

Why a few days of warning helps, in his words: staffing and treatment. Get the right people on shift and the right chemicals dosed before the unusual water arrives, rather than after someone notices.

## 3. The trick: a soft sensor

TOC and alkalinity need a lab. Somebody takes a sample, runs a test, and the number comes back later. You cannot get them continuously and you cannot get them for the future.

But there is an instrument sitting in the river above Strontia, run by the US Geological Survey, taking readings every 15 minutes with no human involved. It measures cheap things:

- **Turbidity**: cloudiness. Muddy water usually means runoff, which usually brings organic matter.
- **Specific conductance**: how well the water conducts electricity, which tracks dissolved minerals. Closely tied to alkalinity because both come from dissolved rock.
- **pH**, **temperature**, **dissolved oxygen**.

A **soft sensor** is a model that predicts the expensive measurement from the cheap ones. That is the entire idea. The machine learning is the tool, not the point.

Jake adds three more cheap, public feeds for context: **river flow** from the state (trickle or flood), **snowpack** from a mountain station (how much melt is still coming), and **rainfall** from a weather station (did it rain, which drives runoff).

## 4. What the data looks like

Every file is one row per day. There is one **target** table (the thing to predict) and five **predictor** tables (the things to predict it from).

Target, `FoothillsInfluent.csv`, from Denver Water's own lab:

```
DATE,      TOC_mg_L, Alk_mg_L
6/26/2025, 2.3,      42
```

Predictors, one row each:

```
USGS river sensor (site 06707525, above Strontia)
Date,       Dissolved_Oxygen_Mean, Specific_Cond_Mean, Temp_C_Mean, Turbidity_Median, pH_Median ...
2024-10-07, 9.3,                   301.0,              11.9,        1.6,              8.6

Colorado DWR gage (station PLASPLCO)
Date,       Flow_CFS, GageHeight_ft, Precip
2024-06-07, 1060.0,   4.058437,      -100.53875

SNOTEL snowpack (HoosierPass.csv since the Sep 4 update; Michigan Creek before)
DATE,       SWE
2023-04-01, 12.6

NOAA weather station (USC00058022)
STATION,     DATE,       PRCP, SNOW, TMAX, TMIN
USC00058022, 2024-06-07, 0.0,  0.0,  86.0, 44
```

Units: mg/L is milligrams per litre. CFS is cubic feet per second of river flow. SWE is snow water equivalent, the depth of water you would get if the snowpack melted. Temperatures in the NOAA file are Fahrenheit, the USGS ones Celsius.

Two quirks. The DWR `Precip` column is a running total that occasionally resets, which is why it can be negative and why Jake takes its day-to-day difference (his Sep 4 comment adds: don't use it as a predictor, the data is dirty, NOAA preferred). And the Foothills file has no January to March at all, because the river sensor has almost no winter readings (probably pulled out before the river freezes). Jake's code used to also filter those months out with a `month >= 4` mask; the Sep 4 update replaced that with a proper date cutoff, fixing the "bug in waiting" from section 14.

About 1,100 rows in the target, spread over four and a half summers, ending 2026-08-19 to match the new reservoir sonde deployment.

## 5. What a Jupyter notebook is

A Python script chopped into **cells**, run one at a time from the top, in a browser. Variables persist between cells, so it is a REPL session that has been saved to a file. Plots and tables appear inline under the cell that produced them. The `.ipynb` file is JSON holding each cell's code and, optionally, its last output. Jake stripped the outputs before sending; our executed copies in `experiments/runs/` have them.

To open one: `cd experiments && .venv/bin/jupyter notebook`, then click a file in `runs/`. Shift+Enter runs a cell.

## 6. What pandas is, and the five operations Jake uses

pandas is Python's table library. A `DataFrame` is a table in memory with named columns and an index; here the index is always the date. Jake's whole data pipeline is five operations.

**`read_csv`**: load a file into a table.

**`set_index('DATE')`**: make the date column the row key, so rows from different tables can be matched up by day.

**`join`**: a SQL left join on the date index. Start with the target table, bolt the predictor columns onto each day's row. After four joins, each day has the lab result plus every sensor reading for that day, all in one wide row.

**`shift(2, freq='D')`**: slide every row in a table two days later. This is the move that makes it a forecast. After shifting, the row dated June 10 actually contains the river readings from June 8. So when you join it to the June 10 lab result, the model is learning "readings from two days ago" against "lab result today". Without the shift it would be a same-day model, which is useless for warning anyone. The shift is 2 days in the TOC notebook and 4 in the alkalinity one (rain gets 4 and 6; NOAA publishes about two days behind, so its lag carries an operational allowance on top).

**`rolling(7).mean()`**: a moving average over the last seven rows. Smooths noise and captures "the river has been high all week" as opposed to "the river spiked today". `diff()` is the sibling: today's value minus yesterday's, so rising or falling.

That's it. Everything else in the load section is renaming and cleaning.

## 7. Feature engineering

"Features" are the input columns the model sees. Raw sensor columns are a start; the craft is in the derived ones. Jake's:

- **Rolling averages**: 7-day flow, 3-day turbidity, 7-day rain, 7-day snowpack.
- **`turb_flow`** = turbidity times flow. Muddy water in a big river carries far more material than muddy water in a trickle. This "loading" term turns out to be the single strongest TOC predictor.
- **Month as sine and cosine.** If you feed month as 1 to 12, the model thinks December (12) and January (1) are far apart. Map month onto a circle with `sin` and `cos` and they become neighbours. Two columns encode the season.
- **Flow delta**: rising or falling river.

He makes about twenty of these and picks ten for TOC and eight for alkalinity, guided by a correlation table (which columns move together with the target).

## 8. Train on the past, grade on the future

You cannot grade a model on the data it learned from; it would just memorise. So the rows are split. Jake trains on the first half of the timeline and tests on the second half. Crucially, no shuffling: the test rows are all later in time than the training rows, so the model never sees the future while learning. Anything else would cheat, because neighbouring days are nearly identical and a shuffled split leaks answers.

He also uses **sample weights**: when training, days with TOC above 3 (or alkalinity below 60) count 1.5 times as much. It tells the model "care more about the unusual days", because those are the ones operators need warning about.

## 9. The models

**Linear regression.** The simplest thing: `TOC = a * turb_flow + b`, a straight line through one variable. Jake fits it first as a baseline, so the fancier models have something to beat.

**Random forest.** A decision tree is a flowchart of yes/no questions on the features ("is turbidity over 5? is it summer? is flow rising?") ending in a predicted number. One tree is crude and overfits. A random forest grows a few hundred trees, each on a random sample of rows and a random subset of features, and averages their answers. The randomness makes the trees disagree in different ways and the average cancels the noise. It is the default "usually works" model for tabular data.

**CatBoost.** Also trees, but grown in sequence rather than in parallel: each new tree is fitted to the errors the previous trees left behind, so the ensemble corrects itself step by step. This family is called gradient boosting. It often edges out random forests, and it does here.

**Grid search.** Every model has knobs (how many trees, how deep, how many rows before a branch is allowed). `GridSearchCV` tries every combination on a list and keeps the one that scores best on held-out slices of the training data.

None of this is exotic. Every line is textbook scikit-learn.

## 10. Reading the scores

Three numbers appear everywhere.

**R²** (R squared). What fraction of the target's variation the model explains. 1.0 is perfect. **0 means the model is exactly as good as always guessing the average.** Negative means worse than guessing the average, which happens more than you would think.

**RMSE**, root mean squared error. The typical size of a miss, in the same units as the target. An RMSE of 5 mg/L for alkalinity on values that average 58 means predictions are typically off by around 5, or roughly 9%.

**MAPE**, mean absolute percentage error. The typical miss as a percentage. Easier to read than RMSE, but unfair to the model when the true value is small.

**MAE**, mean absolute error. Also the typical size of a miss in the target's units, but a plain average: take each day's miss, drop the sign, average. RMSE squares the misses first, so a few big misses dominate it; MAE counts one 3 mg/L miss as exactly ten 0.3 mg/L misses. The later experiments (`experiments/novelty/`) use MAE when comparing groups of days, because one outlier day should not swamp a group average.

Jake's numbers as we reproduced them (test half of the data, re-run 2026-09-04 on the updated materials; the baseline R² is scored on the ablation package's matched rows):

| | Baseline line | Random forest | CatBoost |
|---|---|---|---|
| TOC, R² | 0.06 | 0.66 | 0.74 |
| TOC, RMSE (mg/L) | 0.63 | 0.38 | 0.33 |
| Alkalinity, R² | 0.51 | 0.61 | 0.68 |
| Alkalinity, RMSE (mg/L) | 6.30 | 5.76 | 5.20 |

How to read that:

- For alkalinity, one variable and a straight line already explains half the variation (0.51). Conductance really is a good proxy for alkalinity, which matches the chemistry. The forest lifts it to 0.61, so the extra machinery is worth about 10 points. Real, not dramatic.
- For TOC, the straight line is barely better than guessing the average. The forest gets to 0.66. So the relationship is genuinely nonlinear and the trees are earning their keep. (Both TOC models scored higher than on the August materials; the 2-day lags and the replacement snow station are the difference.)
- Jake's own summary is honest: "pretty good, don't expect it to get much better without more data." He deliberately traded some R² for catching peaks, because a model that nails the boring days and misses the storm is worthless to an operator.

One warning sign in the output. Cross-validation (testing on several different time slices of the training data) gave a mean R² of -0.66 for the TOC forest. That means the model's quality swings wildly depending on which stretch of time you test it on. The single 0.66 number is a good result on one particular half; it is not a stable property of the model.

## 11. The yes/no version

For alkalinity Jake also asks a simpler question: **will it be below 60 mg/L, yes or no?** That is **classification**. Two ways to be wrong, and they matter differently:

- Predict low, actually high: a **false alarm**. Operators prepare for nothing.
- Predict high, actually low: a **miss**. Operators get no warning.

The two scores:

- **Precision**: when the model says "low", how often is it right? 82%.
- **Recall**: of the days that really were low, how many did it flag? 61%.

Out of 377 test days: 92 lows caught, 60 lows missed, 20 false alarms, 205 correct all-clears. In the 2026 season plot there is a three-week run in late July and August where it kept predicting low while the water was high.

Why it struggles: the average alkalinity in this data is 58.3 and 58% of days are below 60. The threshold runs straight through the middle of normal. The question "above or below 60" on water that hovers at 58 is close to a coin flip, and Jake says so ("not sold on precision", "lots of back and forth"). Whether 60 is the number operators actually act on, or just a round one, is worth asking.

## 12. Which inputs the model leans on

**Feature importance** ranks the inputs by how much the model uses them. For alkalinity: conductance 33%, pH 29%. For TOC: turbidity times flow 34%, snowpack 17%, conductance 15%. Both match the physical story: dissolved minerals for alkalinity, muddy high water for organic carbon. That agreement is reassuring, because a model that leaned on something physically meaningless would be memorising coincidences.

**SHAP** plots do the same per prediction: for this particular day, which inputs pushed the estimate up or down.

## 13. The honest one-paragraph summary

Jake has a small, clean, public dataset; a physically motivated question; a sensible pipeline; and models that are clearly better than nothing and clearly not finished. The alkalinity regression is useful today. The TOC model catches the big spring peaks and is unstable elsewhere. The below-60 classifier is not yet something an operator should trust. He knows all of this and says so.

## 14. Loose ends found in the code

Two of the four originals were fixed by Jake's Sep 4 update; strikethrough kept for the story.

- ~~The TOC notebook shifts the river readings by 2 days, not 4, under a comment saying 4.~~ Resolved Sep 4: the TOC notebook now shifts everything upstream by 2 days consistently (rain 4), and Jake's email explains the thinking (2 recently scored better; the number is expected to keep moving). Alkalinity still uses 4 (rain 6).
- ~~The "trim to April 2022" filter removes January to March of every year.~~ Fixed Sep 4: now a real date cutoff (`index >= '2022-04-01'`).
- Six turbidity figures came in the package with no turbidity notebook. There is a third model.
- The two Foothills lab exports the notebooks actually read were not shared; `FoothillsInfluent.csv` is their combined output.
- New in the Sep 4 update: the notebooks fetch and read Buckskin Joe SNOTEL (station 938), but the shipped CSV is `HoosierPass.csv` and its values match Hoosier Pass (station 531) on the NRCS feed. One of the two is stale; question for Jake.

## 15. Poking at it yourself

```
cd eddd/design-storm/experiments
.venv/bin/jupyter notebook
```

Open `runs/Alkalinity_Soft_Sensor.ipynb`. Read cells top to bottom; every one has its output underneath. Change a number (the lag in `shift(4, freq='D')`, the 60 threshold, the feature list), then Kernel > Restart & Run All and watch the scores move. That is the fastest way to build intuition, and it is roughly what a cohort would do on the day.
