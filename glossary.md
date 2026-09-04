# Glossary for the non-water reader

Plain-language definitions used across this repository. Items marked **(general knowledge)** come from general knowledge, not Jake's materials; verify with Denver Water before relying on them.

See also `guide.md` sections 1 to 3 for TOC, alkalinity, soft sensor, turbidity, and specific conductance, and section 10 for R^2, RMSE, MAPE, and MAE.

## Water terms

- **Snowpack.** Snow lying on the mountains through winter. In the Colorado Front Range most of the year's water arrives as snowmelt, so the snowpack is the real reservoir.
- **SWE, snow water equivalent.** If this snow melted right now, how deep a layer of water would it make? Depth of snow is useless (powder vs packed), so SWE is the measurement. A peak of 9.0 means nine inches of water sitting on the hillside as snow.
- **SNOTEL.** The federal network of automated mountain snow stations ("snow telemetry"). Jake used Michigan Creek (station 937) until the Sep 4 update replaced it over bad spring 2026 readings; the shipped replacement CSV matches Hoosier Pass (531) while the notebooks name Buckskin Joe (938). One point in a large watershed: a proxy for the basin, not the basin.
- **Peak and melt-out.** SWE climbs all winter, reaches a maximum (peak), then falls to zero (melt-out). The shape of that curve is the year's water story: high, late, slow means a long strong river; low and gone in two weeks means a short pulse and a thin summer.
- **April 1 SWE.** The traditional comparison date, usually near peak. "How was the snowpack this year" means "April 1 SWE vs average."
- **Water year.** October 1 to September 30. Snow that falls in November melts the following May, so calendar years split one winter in half. Group snow data by water year, never calendar year (see `exploration-notes.md` section 7.1 for what the calendar grouping got wrong).
- **cfs, cubic feet per second.** River flow. 620 cfs means 620 cubic feet of water pass the gage each second.
- **Flush.** The rising melt river scours banks, forest floor, and stream bed and carries a season's accumulated dead plant material downstream in a few weeks. That is the spring TOC spike. "First flush" is the same idea for any storm after a dry spell.
- **Baseflow.** What the river is when it is neither raining nor melting: groundwater seeping from rock. Groundwater has been in contact with minerals, so it carries more of what makes alkalinity. Less melt means less dilution, so a dry year runs higher alkalinity, exactly as 2026 shows.
- **Convective storms, monsoon.** Summer afternoon thunderstorms. In July and August, moist air from the south (the North American monsoon) produces short, intense downpours over small areas. Little annual water, but an inch on one hillside in an hour flushes sediment and organic matter fast.
- **Burn scar (general knowledge).** Land where wildfire removed vegetation; rain runs straight off carrying ash, soil, and organic carbon. Denver Water's watershed has several (Buffalo Creek 1996, Hayman 2002). Ask Jake whether it matters at Strontia.
- **Regime.** A stretch of time where one mechanism dominates. A snow-flush year and a drought-plus-thunderstorm year are two regimes: same river, different physics producing the TOC.
- **Excursion.** A day beyond the operational threshold: TOC above 3 mg/L or alkalinity below 60 mg/L, the days Jake's sample weights emphasise and operators care about.

## Modeling and statistics terms

- **Extrapolation.** Answering for inputs outside anything seen in training. Straight-line models try (badly); tree models cannot, and instead return the nearest remembered answer with full confidence.
- **Novelty score.** For one day, how many of its inputs sit outside the training range. A cheap way to flag days where the model is extrapolating. See `experiments/novelty/`.
- **MAE, mean absolute error.** The typical size of a miss in the target's units, as a plain average: each day's miss with the sign dropped, averaged. Unlike RMSE it does not square the misses, so one bad day cannot dominate a group. Used when comparing groups of days (novelty bins, regimes).
- **Median.** The middle value when you sort a list. Half the values are above it, half below. Less sensitive to one extreme value than the mean, which is why the wet/dry reference is a median.
- **Percentile, 5th and 95th.** The value below which 5% (or 95%) of the training days fall. A test day "beyond the 5th or 95th percentile" on some input is in a corner the model saw on fewer than one training day in twenty. Softer than "outside the minimum and maximum", which means never seen at all.
- **Fold.** One train/test split. Rolling-origin folds (`experiments/rolling/`) train on every year before N and test on year N; regime folds (`experiments/regime/`) train on wet years and test on dry, or the reverse.
- **Anchored rows.** The rule that every feature set is scored on the same days: keep only days where all of Jake's full feature set is present, then remove columns. Without it, dropping a column with gaps changes which days survive, and the comparison is partly a different test set (`experiments/ablation/`).
- **Spearman correlation.** A number from -1 to 1 saying how consistently two things rise together, based on rank order rather than exact values. 0.4 means "more novelty tends to mean more error, loosely"; 1 would mean perfectly in step.
- **Standardised (z-score).** Each column rescaled so its mean is 0 and its spread is 1, so that inches of snow and days of melt can be compared on one footing before measuring distance between years (`experiments/analog/`).
- **Monotonically.** Only ever moving one way. "MAE rises monotonically with novelty count" means each step up in novelty brought a higher error, with no dips.
- **Recall, precision, false alarm, base rate.** Recall: of the days that really were excursions, what share the model flagged. Precision: of the days the model flagged, what share were real. A false alarm is a flagged day that was not real. The base rate is what precision would be if the model flagged every day (59% for alkalinity below 60, since that is how often it happens); precision near the base rate means the flags carry little information. Full explanation in `guide.md` section 11.
- **Lead (days).** For an episode, the gap between the first day the model flagged it and the day it actually began. Negative means the warning came before the episode; positive means the model noticed after it had started.
