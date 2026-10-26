---
issue: 177
title: Absolute area tolerance as an early stop, and sub-cell exclusion, for regions of a few cells (counties)
description: area_tol_cells is an early-stopping option, not an accuracy option: users who accept a small absolute size for small regions let the convergence test pass earlier. On the county ladder the finest level ends CONVERGED from 4 finest-grid cells, after 15 iterations and with a less accurate result than the stalled run (mean 1.28 % against 0.94 %, 103 counties above 10 % against 46); at 1 to 2 cells it only reports (34 and 59 counties unresolved). Excluding regions with a target below k cells does not converge the finest level up to 8 cells. Districts and states are unchanged. The option is off by default.
kind: exploration
topic: flow
status: led-to
related: exploration-stall-after-validity, exploration-stall-lagging-regions, exploration-county-error-relation, unresolved-regions-pr
date: 2026-10-26 20:00
before: main @ 6921aca
after: feat/unresolved-regions (area_tol_cells)
inputs: 3,108 bundled counties (population), max_segment_length 1000, morph_multiresolution with min_resolution and levels auto (grids 512, 1024, 2048), area_scale 1e-6, n_iter 1000, validity="repair-crossings", default tolerances (mean_tol 5 %, max_tol 10 %). Controls: 432 congressional districts (max_segment_length 1000) and the 49 states, n_iter 300. Single runs. Errors are the relative errors of the returned geometries.
---

`measure.py <dir>` runs the ladders with `area_tol_cells` (the library branch), `analyze.py <dir>` computes what each rule excuses on the baseline levels and draws the figure. `measure_per_level.json` is the first measurement, in which k counted cells of the grid of each level.

figure: fig1_excused.png — Left: at the finest level (2048) of the baseline ladder, the counties above 10 % that an absolute tolerance of k cells excuses and that the exclusion of targets below k cells removes. Right: time of the ladder per `area_tol_cells`.

## 1. What each rule excuses (offline, baseline levels, k in cells of the level's own grid)

Counties above 10 % in the baseline: 762 (grid 512), 413 (1024), 46 (2048).

| k | grid 2048: abs. excused / still above | grid 2048: targets below k cells / of those above 10 % / still above after exclusion | grid 512: abs. excused / still above |
|---|---|---|---|
| 0.5 | 28 / 18 | 2 / 2 / 44 | 683 / 79 |
| 1 | 34 / 12 | 20 / 12 / 34 | 746 / 16 |
| 2 | 38 / 8 | 58 / 20 / 26 | 762 / 0 |
| 4 | 44 / 2 | 171 / 35 / 11 | 762 / 0 |
| 8 | 46 / 0 | 383 / 38 / 8 | 762 / 0 |

At the finest level the absolute tolerance needs 8 cells to excuse all 46 counties above 10 %, the exclusion of sub-cell targets never converges the level up to 8 cells (8 to 44 regions remain above tolerance). At the coarsest level (512) a tolerance of 2 cells of that grid excuses all 762 counties and the ladder would stop on a grid that is too coarse; hence the tolerance is the same area at every level (cells of the finest grid).

## 2. Ladder runs with `area_tol_cells` = k cells of the finest grid

| k | time | level (grid: status, iterations) | n_unresolved at the end | mean error | above 10 % |
|---|---|---|---|---|---|
| 0 | 46 s | 512: stalled 500, 1024: stalled 80, 2048: stalled 200 | 0 | 0.94 % | 46 |
| 1 | 41 s | same, same iterations | 34 | 0.94 % | 46 |
| 2 | 44 s | 512: stalled 620, 1024: stalled 70, 2048: stalled 140 | 59 | 1.20 % | 62 |
| 4 | 40 s | 512: stalled 580, 1024: stalled 130, 2048: converged 15 | 103 | 1.28 % | 103 |
| 8 | 23 s | 512: stalled 470, 1024: converged 63 | 228 | 3.11 % | 229 |
| 16 | 17 s | 512: stalled 350, 1024: converged 20 | 436 | 5.86 % | 436 |

Controls (area_tol_cells 4): districts converge after 135 iterations with a mean of 0.4625 % and a max of 8.26 %, states after 65 with 1.19 % and 5.65 %, both identical to the runs without the tolerance.

## Reading

- With k counted in the cells of each level (the first measurement), the coarse level 512 converged at k 2 or 4 with a mean of 15 to 17 % and ended the ladder; the districts ended earlier with a worse error (mean 0.46 to 1.16 %, max 8 to 24 % at k 1). The tolerance therefore counts cells of the finest grid in a ladder, which leaves districts and states unchanged at k 4.
- At 1 cell the tolerance changes nothing in the run and reports the 34 counties that are as close as one cell. From 2 cells the runs differ (trajectories are chaotic; the iteration counts change), and at 4 cells the finest level converges after 15 iterations, with a worse result than the stalled run: 103 counties above 10 % against 46, because the previous level ended in a poorer state and the tolerance stops the refinement as soon as the remaining regions are within 4 cells.
- `area_tol_cells` is an early-stopping option: it ends the run once small regions are within k cells of their target, whatever their relative error, and the result is less accurate than the run that continues. It is not a fix for stalls; the continuation of a stalled run (`stall_patience=None`) gave the better counties (mean 0.68 %, 8 above 10 %) at 2.3 times the ladder time. The measurement shows the price of the early stop at each k, so the default stays off; `n_unresolved` reports the excused regions at any k.
