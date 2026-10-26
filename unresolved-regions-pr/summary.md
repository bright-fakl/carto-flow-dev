---
pr: 185
url: https://github.com/bright-fakl/carto-flow/pull/185
issue: 177
title: area_tol_cells (early stop), n_unresolved and a stall warning that names the continuation
description: MorphOptions.area_tol_cells (default off) stops a morph early when small regions are within k cells of their target, whatever their relative error; Cartogram.n_unresolved counts the excused regions above max_tol; a stalled morph warns and names workflow.morph(stall_patience=None, n_iter=N). It is not an accuracy option. On the county ladder the finest level converges from 4 cells with a less accurate result than the stalled run; districts and states are unchanged.
kind: pr
topic: flow
base: main
branch: feat/unresolved-regions
related: exploration-unresolved-regions, exploration-stall-after-validity
date: 2026-10-26 21:00
before: main @ 6921aca
after: feat/unresolved-regions @ 7ba2271
inputs: 3,108 bundled counties (1 km input, auto ladder, validity="repair-crossings", n_iter 1000), 432 districts and the states as controls; see exploration-unresolved-regions.
---

The measurement and its figure are in `exploration-unresolved-regions`; this page lists the change.

## Behavior

- `area_tol_cells` (>= 0, default 0), an early-stopping option for users who accept a small absolute size for small regions: a region with `|area - target| <= area_tol_cells * dx * dy` counts as on target in the convergence test, the stall rule and the best-iterate score. The reported errors (`mean_error_pct`, `max_error_pct`, history, snapshots) are the relative errors. In a ladder every level uses the same area: the cells of the finest grid.
- `Cartogram.n_unresolved`: excused regions whose relative error is not below `max_tol` (0 when off). It is not stored by `save_cartogram`.
- `CartogramWorkflow.morph` and `morph_multiresolution` warn when the last pass is stalled; the message names `workflow.morph(stall_patience=None, n_iter=N)`, which continues from the best iterate with the stall rule off. The quality report of `metrics` names it too.
- Not in this PR: a stall component that follows the count of regions above `max_tol`.

## Results

| k (finest cells) | finest level | n_unresolved | mean / above 10 % (true) |
|---|---|---|---|
| 0 | stalled, 200 | 0 | 0.94 % / 46 |
| 1 | stalled, 200 (same run) | 34 | 0.94 % / 46 |
| 4 | converged, 15 | 103 | 1.28 % / 103 |

Districts and states with k = 4: identical status, iterations and errors to k = 0.
