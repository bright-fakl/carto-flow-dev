---
pr: 131
url: https://github.com/bright-fakl/carto-flow/pull/131
issue: 93
title: Multiresolution docs: grid="auto" instead of a fixed 128 / 4 recipe
description: The gallery examples, the multiresolution tutorial and the diagnose-convergence how-to use grid="auto" instead of min_resolution=128, levels=4; the tutorial gets a section on choosing the resolution. Documentation only; for states and districts "auto" picks 128, as the examples did.
kind: pr
topic: flow
branch: docs/multires-recipe
base: main
date: 2026-10-12 22:10
related: pr128-multires-auto-resolution, pr130-create-flow-cartogram
before: main @ 0416aa9
after: docs/multires-recipe @ 012f665
inputs: none; no code or figures change.
---

Pages changed: `docs/examples/flow_cartogram/plot_flow_population_evolution.py`, `plot_flow_covid_waves.py`, `docs/tutorials/multiresolution-flow-cartogram.ipynb` (two workflow cells, new section "Choosing the resolution"), `docs/how-to/diagnose-convergence.ipynb`, `docs/reference/flow_cartogram/index.md`. The documentation build in CI executes the notebooks and examples.
