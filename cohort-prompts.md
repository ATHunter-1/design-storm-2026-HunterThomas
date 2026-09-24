# Exploration prompts: Foothills soft-sensor problem

Prompts to paste into an AI coding assistant working in a folder that holds the Denver Water materials: the `Data/` CSVs, the `Scripts/` notebooks, the figures, the disclaimers, and the problem statement. Work through the stages in order, or start wherever you are.

## 0. Ground rules (paste first)

> You are helping a small team explore a water-quality dataset from Denver Water. The data is provisional and carries two Denver Water disclaimers; keep both with any output. Explain water and statistics terms the first time you use them, as if to a software developer who has never touched either. When you are stating general knowledge rather than something in these files, say so. Never invent numbers; compute them or say you cannot.

## 1. Understand the domain

> Read the problem statement and the slide deck. In plain language: what does the Foothills treatment plant care about, why does it want a few days of warning, and what happens at the plant when it gets one? Define TOC, alkalinity, turbidity, specific conductance, soft sensor, and influent as you go.

> Draw the physical system as a sequence: where the snow falls, where the river is measured, where the water is treated. Label each measurement in the data with where on that path it is taken and who takes it.

> List every threshold or magic number in the deck and notebooks (for example 60 mg/L, 3 mg/L, four days). For each, say whether the materials explain where it comes from. Flag the ones they do not.

> Who decides what, based on this model's output? Name the roles you can find in the materials and what each would do differently with a warning versus without one.

## 2. Understand what was built

> Walk me through `TOC_SoftSensor.ipynb` cell by cell in plain language. For each data-handling step (join, shift, rolling window), say what it does physically, not just what pandas does.

> The notebooks shift the upstream data before joining it to the plant data. Explain why that shift is what makes this a forecast. Then check: is the shift the same in both notebooks and for every source? Report what you find.

> List every engineered feature, what raw columns it comes from, and the physical intuition behind it. Then group them: which features are different views of the same underlying signal?

> Summarise the reported model results in one table. Explain R^2, RMSE, MAPE, precision, and recall in one sentence each, then say what "R^2 of 0.59" means for an operator in practice.

## 3. Run it and check it

> Set up a Python environment and make `Alkalinity_Soft_Sensor.ipynb` run end to end from the CSVs in `Data/`. Replace any hardcoded paths. Do not change any modelling logic. Tell me what you had to change and why.

> Run both model notebooks. Compare the numbers and figures you get with the ones in the deck and the figures folder. Which match exactly, which differ, and what is the most likely reason for each difference?

> Is this pipeline deterministic? Find every source of randomness in the notebooks and say whether it is pinned. Then run the alkalinity model twice and confirm the outputs are identical.

> The API grabber notebooks pull from public services. Run one and diff its output against the CSV that was shipped. What changed, and what does that tell you about the data?

## 4. Experiment

> Change the shift from 4 days to 2, 3, 5, and 6 in the alkalinity notebook and rerun. Table the scores by lag. What does the shape of that table suggest about how long water takes to travel?

> Score the TOC model as an event detector instead of a regressor: find every run of days with TOC above 3, and for each run say whether the model predicted above 3 at any point before or during it, and with how many days of lead. Present that as a table of episodes.

> Split the test set by year and report the scores per year. Which years have any excursion days at all? What does R^2 mean in a year with none?

> Drop one feature at a time from the feature list, retrain, and table the change in R^2 and in excursion recall. Hold the set of rows constant across every run: drop rows with any missing value in the full feature set first, then remove columns. Which features carry the model, and which are free to remove?

> Fit a quantile model (CatBoost supports quantile loss) and produce, for each test day, a 10th to 90th percentile band rather than a point. Plot the band with the actual values. On what fraction of days does the actual fall inside the band?

> Compare the snowpack, river flow, and TOC by year. Which years had large TOC events and which did not? For a year with an unusually light or fast-melting snowpack, which of the model's inputs fall outside anything it saw in training, and what does that imply for its predictions?

## 5. Visualise

> Make one figure with stacked, date-aligned panels: snowpack, rain, river flow, upstream turbidity, and plant TOC. Pick one storm event and annotate the upstream spike and the plant arrival so the travel time is visible.

> Make a calendar heatmap of the alkalinity classifier's test days coloured by hit, miss, false alarm, and correct all-clear. Where do the misses cluster?

> Plot alkalinity by day of year, one line per year, on a circular (polar) axis. Explain why the month is encoded as sine and cosine in the notebooks, using this plot.

> For the single worst prediction in the TOC test set, produce a SHAP explanation and describe in plain words which inputs pushed the prediction the wrong way.

## 6. Model the domain

> From everything above, draft a ubiquitous-language glossary for this domain: terms, one-line definitions, and which role uses each term. Distinguish terms from the materials and terms you introduced.

> Propose candidate bounded contexts for a system that would put this model into daily use at the plant (for example watershed monitoring, forecasting, plant operations, compliance). For each pair that talks, say what crosses the boundary and in which direction.

> The model produces a number. Model the decision instead: what would an operator do at TOC 2.8 versus 3.1 versus 4.5, and what does a warning oblige anyone to do? Express that as commands, events, and policies.

> A USGS reading can be revised after the fact (the data is provisional). Model the lifecycle of a reading and of a forecast built on it. What happens to yesterday's warning when today's input is corrected?

> The alkalinity classifier asks "below 60, yes or no" and struggles near the line. Propose a different target that reflects what the plant actually decides on (a band, a distance, a joint TOC and alkalinity state) and sketch how the model and the operator's view would change.

## 7. Share findings

> Draft a one-page summary: the question we chose, one figure, what we found, what we would ask the plant operators, and what we would build next. No more than eight bullets.
