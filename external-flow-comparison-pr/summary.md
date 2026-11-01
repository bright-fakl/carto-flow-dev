---
pr: 203
title: "Reproducible comparison of carto-flow with other flow cartogram tools"
description: Docker-based harness that runs carto-flow, go-cart, R cartogram, cartogramR and Python cartogram on US states and congressional districts and plots measured accuracy against time.
kind: pr
topic: infra
project: carto-flow
url: https://github.com/bright-fakl/carto-flow/pull/203
branch: benchmarks-comparison-harness
base: main
related: benchmarks-voronoi-proportional-pr
date: 2026-10-31 21:30
before: main; no external comparison, flow benchmarks only for carto-flow
after: benchmarks-comparison-harness
inputs: US states (49 regions) and congressional districts (432 regions); full profile in Docker on a local workstation; time budgets 60 s (states) and 120 s (districts) per tool.
---
## Change

Part A of the comparison plan (carto-flow #75, #80, #113).

- `benchmarks/comparison/`: harness, R runner, Dockerfile and README. Each tool runs a ladder of iteration caps (go-cart: area-error tolerances) with an unreachable internal tolerance, so no tool decides when to stop. Accuracy is measured afterwards by the same code for every tool: maximum and mean relative deviation of each region's area share from its value share, and the number of invalid output polygons. Time is the median of repeats.
- carto-flow variants: default, `grid="auto"`, `dt=0.05`, `repair-crossings`, `repair-quadtree`.
- Docs: `docs/performance/comparison.ipynb` with error-versus-time curves, time-to-target tables and example cartograms per tool.

## Best maximum area error

| Dataset | Tool | Best max error | Time |
|---|---|---|---|
| States | carto-flow | 0.00008 % | 65 s |
| States | go-cart | 0.00005 % | 1.3 s |
| States | cartogramR gsm | 0.00000 % | 7.8 s |
| States | carto-flow (dt=0.05) | 0.0001 % | 54 s |
| Districts | carto-flow | 0.025 % | 4.8 s |
| Districts | carto-flow (repair-crossings) | 0.033 % | 6.3 s |
| Districts | go-cart | 0.00004 % | 27 s |

## Observations

- carto-flow is fastest to moderate targets (0.5 % on states in 0.37 s). With the iteration cap lifted it reaches 0.00008 %, so the earlier plateau came from the cap, not the grid.
- On districts the default carto-flow leaves 13 invalid regions; `repair-crossings` removes them at similar accuracy and cost.
- R cartogram and Python cartogram do not reach useful accuracy on districts within the budget.
- `repair-quadtree` is slow and inaccurate on districts (1.2 % after 95 s).
- On the states the carto-flow maximum error plateaus near 0.1 % while the best iterate improves slowly; at 640 iterations `dt=0.05` gives 0.0075 % against 0.071 %. Issue #202 tracks the cause.
- The example images are committed; the GeoPackages they are drawn from are not.
