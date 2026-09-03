# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

A private workspace for preparing the Explore DDD 2026 Design Storm exercises, built around Jake Slawson's (Denver Water) TOC and alkalinity soft-sensor models for the Foothills Water Treatment Plant. It holds Jake's original materials, a plain-language guide to them, reproducible re-runs of his notebooks, and a set of deterministic experiments layered on top. It is a preparation repo, not the repo that will be handed to conference cohorts.

Start with `README.md` (what Jake sent and why), `guide.md` (the domain and the models explained from zero), and `exploration-notes.md` (findings, open questions for Denver Water, glossary). Each experiment package has its own README with method and results.

## Ground rules

- **Jake's originals are read-only.** `scripts/`, `data/`, `figures/`, `Foothills_INF_ML_NoConclusions.pptx`, and the zip are the materials as sent (plus `data/` CSVs extracted from it). Never edit them; experiments work on copies. `ExploreDDD_Materials/` is gitignored; re-extract it from `ExploreDDD_Materials.zip` if needed.
- **The Denver Water disclaimer travels with the data.** It is at the top of `README.md`. Keep it with any derived dataset or shared output. The data is provisional; a fresh API pull can differ from the committed CSVs.
- **Determinism is a hard requirement for experiments.** Fixed seeds (`SEED = 42`) and pinned thread counts live in `experiments/ablation/scoring.py`. Every `run.py` must produce byte-identical result CSVs on a second run; verify before writing findings into a README or the notes.
- **Known data artifact:** `data/MichiganCreek.csv` (and the NRCS feed itself) shows SWE 9.0 on May 12 to 15, 2026 between zero readings. Treat those four days as suspect (see `exploration-notes.md` 7.1 and `experiments/analog/`).

## Environment and commands

All Python work happens in `experiments/` with a local venv:

```
cd experiments
uv venv --python 3.13 .venv
uv pip install --python .venv/bin/python -r requirements.txt
```

Run the full test suite (from `experiments/`):

```
.venv/bin/python -m pytest ablation/tests rolling/tests snowpack/tests novelty/tests regime/tests drivers/tests analog/tests -q
```

A single package: `.venv/bin/python -m pytest regime/tests -q`. A single test: `.venv/bin/python -m pytest regime/tests/test_split.py -q -k <name>`.

Run an experiment (each writes CSVs plus a `.meta.json` into its own `results/`):

```
.venv/bin/python -m ablation.run --target Alk        # or TOC; --check for the determinism check
.venv/bin/python -m rolling.run
.venv/bin/python -m snowpack.run
.venv/bin/python -m novelty.run
.venv/bin/python -m regime.run
.venv/bin/python -m drivers.run
.venv/bin/python -m analog.run                       # --fetch re-pulls the long NRCS/DWR records (network)
```

Re-execute Jake's notebooks (patched copies, originals untouched):

```
cd experiments
.venv/bin/python patch_notebooks.py
.venv/bin/jupyter nbconvert --to notebook --execute --ExecutePreprocessor.timeout=1800 TOC_SoftSensor.ipynb --output-dir runs
```

`experiments/README.md` documents what `patch_notebooks.py` changes and the reproduction status against Jake's figures.

## Architecture

Data flows one way: `data/` CSVs -> `ablation.frame.build_frame` (reproduces the notebooks' joins, lags, and engineered features exactly; per-target recipes, since TOC and alkalinity differ in lag and columns) -> `ablation.scoring.anchored_rows` (every feature set scored on identical days; without this, dropping a gappy column moves the train/test split) -> `ablation.scoring.FITTERS` (linear / grid-searched random forest / CatBoost, Jake's hyperparameters and sample weights).

Everything else composes on top of `ablation` without modifying it:

- `rolling/` folds by test year (train on all earlier years).
- `snowpack/` water-year summaries of SWE and the wet/dry labelling rule (`DRY_BELOW_FRACTION` of a reference median; the measure and sources are `exploration-notes.md` section 9). Foundation for `regime/` and `analog/`.
- `regime/` trains across the wet/dry boundary, reference median from `analog/data/MichiganCreek_full.csv`.
- `novelty/` counts per-day features outside the training range and relates that to error.
- `drivers/` groups TOC excursion days into episodes, labels the physical driver, scores recall per driver. Episodes live on the anchored index; driver labels read the unanchored frame (some columns are dropped by anchoring).
- `analog/` fetches the multi-decade SNOTEL and DWR records (`fetch.py` is the only networked module) and ranks past water years by similarity to 2026.

Conventions the packages share: pure logic modules with pytest tests (each package and its `tests/` has `__init__.py`; test basenames collide across packages without it), a `run.py` for orchestration and I/O, results as CSV plus a `.meta.json` recording input md5s, library versions, and git commit. New experiments follow the same shape and are built test-first.

Cross-package scores are comparable only because split, seeds, weights, and anchoring are identical everywhere; if you change one, change it in `ablation.scoring` and re-run everything, not in one package.

## Writing style in the docs

The markdown files are written for readers who are not data scientists or water engineers: terms get defined at first use (`guide.md` section 10 and the glossary in `exploration-notes.md` section 8), claims sourced from general knowledge rather than the materials are marked as such, and any quoted model score names the year it was measured on (a lesson from `experiments/rolling/`).
