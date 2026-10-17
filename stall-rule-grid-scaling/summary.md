---
pr: 171
url: https://github.com/bright-fakl/carto-flow/pull/171
issue: 166
title: Stall rule requires a smaller improvement per cycle on fine grids
description: A step moves the fastest point dt cells, so progress per iteration falls with the cell size and the fixed 2 % required improvement ended runs on fine grids that were converging. Above 256 cells the required improvement is scaled by 256 over the number of cells. Counties at grid 1024 go from stalled at the start (929 % mean error) to 4.2 %; Arizona's counties converge at 512 and 1024; runs at 256 cells and below are identical.
kind: pr
topic: flow
base: main
branch: feat/stall-grid-scaling
date: 2026-10-19 03:00
before: main @ cf7d1bb
after: feat/stall-grid-scaling @ c2fe797
related: exploration-county-hierarchical-prototype, square-grid-spacing
inputs: bundled states and congressional districts (population), 3,108 counties and the 15 Arizona and 254 Texas counties from the bundled ACS 2020 snapshot of the county-level PR (population), MorphOptions area_scale 1e-6, square grid with margin 0.5 (the grid code of main, before the square-grid fix of PR 170), n_iter 3000. NUMBA_NUM_THREADS=8.
---

## Figures

figure: fig_counties.png — Counties by population on a single grid of 1024 with default options, before (stalled after 50 iterations at 929 % mean error) and after (stalled after 700 iterations at 4.2 %). Color is log2(area/target); red is too large.

## Rule

`stall_min_improvement` (2 %) is the improvement of the window minimum of the error ratio that counts as progress. The windows are 10 iterations. The required improvement is now `stall_min_improvement * min(1, 256 / cells)`, with `cells` the number of cells along the longer side of the grid, so it is 2 % at 256 cells and below, 1 % at 512, 0.5 % at 1024 and 0.25 % at 2048.

## Single grids: default rule, scaled rule, no rule

`stall166.py` runs every case (the data are in `data_stall166.log`).

| input | grid | default rule | scaled rule (this change) | no stall rule (3,000 iterations at most) |
|---|---|---|---|---|
| AZ counties | 256 | converged, 206 it, mean 2.2 %, max 6 % | converged, 206 it, mean 2.2 %, max 6 % | converged, 206 it, mean 2.2 %, max 6 % |
| AZ counties | 512 | stalled, 50 it, mean 393.73 %, max 1137.2 % | converged, 383 it, mean 1.27 %, max 5 % | converged, 383 it, mean 1.27 %, max 5 % |
| AZ counties | 1024 | stalled, 50 it, mean 414.13 %, max 1194.8 % | converged, 755 it, mean 1.92 %, max 9.9 % | converged, 755 it, mean 1.92 %, max 9.9 % |
| TX counties | 512 | stalled, 50 it, mean 1939.49 %, max 56196.4 % | stalled, 480 it, mean 11.64 %, max 410.6 % | completed, 3000 it, mean 6 %, max 355.6 % |
| TX counties | 1024 | stalled, 50 it, mean 2054.93 %, max 59399.6 % | stalled, 960 it, mean 1.72 %, max 47.8 % | completed, 3000 it, mean 1.72 %, max 47.8 % |
| states pop | 256 | converged, 111 it, mean 0.5 %, max 5.9 % | converged, 111 it, mean 0.5 %, max 5.9 % | converged, 111 it, mean 0.5 %, max 5.9 % |
| states pop | 512 | converged, 213 it, mean 0.59 %, max 7.8 % | converged, 213 it, mean 0.59 %, max 7.8 % | converged, 213 it, mean 0.59 %, max 7.8 % |
| states pop | 1024 | converged, 420 it, mean 0.74 %, max 9.3 % | converged, 420 it, mean 0.74 %, max 9.3 % | converged, 420 it, mean 0.74 %, max 9.3 % |
| states pop | 2048 | stalled, 80 it, mean 168.19 %, max 1540.2 % | converged, 832 it, mean 0.96 %, max 9.7 % | converged, 832 it, mean 0.96 %, max 9.7 % |
| districts pop | 256 | converged, 149 it, mean 0.47 %, max 7.2 % | converged, 149 it, mean 0.47 %, max 7.2 % | converged, 149 it, mean 0.47 %, max 7.2 % |
| districts pop | 512 | converged, 261 it, mean 0.41 %, max 6.2 % | converged, 261 it, mean 0.41 %, max 6.2 % | converged, 261 it, mean 0.41 %, max 6.2 % |
| districts pop | 1024 | converged, 510 it, mean 0.54 %, max 8.5 % | converged, 510 it, mean 0.54 %, max 8.5 % | converged, 510 it, mean 0.54 %, max 8.5 % |
| districts pop | 2048 | converged, 1006 it, mean 0.64 %, max 9.8 % | converged, 1006 it, mean 0.64 %, max 9.8 % | converged, 1006 it, mean 0.64 %, max 9.8 % |
| counties pop | 1024 | stalled, 50 it, mean 929.39 %, max 57754.3 % | stalled, 700 it, mean 4.17 %, max 622.9 % | completed, 3000 it, mean 2.27 %, max 610.4 % |
| counties pop | 2048 | stalled, 50 it, mean 968.37 %, max 60180 % | stalled, 1100 it, mean 3.09 %, max 477 % | completed, 3000 it, mean 0.94 %, max 385.5 % |

## Reading

- At 256 cells and below the three rules agree (same iteration count and error), so default runs on the default grid are unchanged.
- The default rule ends the runs that start far from the target at 512 cells and above after 50 iterations (Arizona and Texas at 512 and 1024, counties at 1024 and 2048, states at 2048), with the error close to the start error. The scaled rule reaches the no-rule result on Arizona (convergence), on the states at 2048 (convergence in 832 iterations) and gets within a factor of 2 to 3 of it on the counties, in a fifth to a third of the iterations.
- Counties and Texas still end as stalled, at 4.2 % and 1.7 % mean error at 1024: the remaining large errors are sub-cell counties, which no longer improve. The no-rule run uses all 3,000 iterations for the same or a slightly lower error.
- Districts and the states up to 1024 are unchanged.

## Why only above 256 cells

256 cells is the default grid and the grid at which `stall_min_improvement` was set; all tests and earlier explorations of the rule are at 256 or below, and the rule is unchanged there. The evidence supports relaxing the requirement on fine grids, where runs that make steady progress are ended; it does not support tightening it on coarse grids. `sym256.py` and `sym256b.py` compare three rules, with the required improvement multiplied by 1 (none), by `min(1, 256 / cells)` (this change) and by `256 / cells` at every grid (symmetric):

| case | none | this change | symmetric |
|---|---|---|---|
| states, single grid 32 | stalled, 590 it, 4.0 % mean | same | stalled, 80 it, 29.9 % mean |
| AZ counties, single grid 32 | converged, 177 it | same | stalled, 130 it, 6.9 % mean |
| districts, single grid 64 | stalled, 240 it, 34 % mean | same | stalled, 90 it, 92 % mean |
| states ladder 32 x 5 | converged, 256 it, 1.96 % | same | converged, 117 it, 0.93 % |
| districts ladder 64 x 4 | stalled, 196 invalid, 1.83 % | same | converged, 200 it, 1.07 %, 24 invalid |
| districts ladder 32 x 5 | stalled, 3.53 % | same | same |
| counties ladder 256 x 4 or 512 x 3 | 4.19 % or 3.40 % | same | same |
| counties ladder 128 x 5 | 15.2 % | same | 28.4 % |

The symmetric rule makes coarse levels of a ladder give up sooner, which helps the districts ladder from a start that is too coarse. It also ends single runs on coarse grids that were converging (states at 32 cells, Arizona at 32), and it is worse on the counties ladder from 128. Stopping an unresolvable coarse level early is a question about ladders, not about the grid size, so it is left to issue 167 as a per-level rule.

## Expected against observed change

The scaling by `256 / cells` is a proxy. The expected progress of a window can be stated directly. In a window the fastest point moves `dt * fraction * cell` per iteration, so the boundaries move a distance `d` in total, and a region of linear size `L` changes its area, and with it its error, by a fraction of order `d / L` (perimeter times displacement over area). The efficiency of a window is

`eta = (relative decrease of the error ratio over the window) / (d / L)`,

with `d` the sum over the window of `dt * step fraction * cell size` and `L = sqrt(sum(T^2) / sum(T))`, the area-weighted size of the target regions (`expect.py`, `expect2.py`, `expect3.py`).

Observed `eta` of the first windows of runs with the stall rule off:

| input | grid 256 | grid 1024 |
|---|---|---|
| Arizona counties (L = 62 and 121 cells) | 0.76 to 1.4 | 0.38 to 0.42 |
| states (17 and 60 cells) | 1.0 to 2.9 | 0.9 to 1.4 |
| districts (4 and 26 cells) | 0.28 to 0.37 | 0.58 to 0.83 |
| all counties (11 cells at 1024) | | 0.06 to 0.07 |
| districts, lognormal values, sigma 1 | 0.31 to 0.42 | 0.48 to 0.62 |
| districts, lognormal values, sigma 2 | 0.33 to 0.40 | 0.22 to 0.32 |

For one input `eta` is the same on every grid (Arizona with the mean region size: 0.22, 0.22, 0.22, 0.28 at grids 128, 256, 512, 1024; the first-window decrease itself falls exactly as 1 / grid: 4.8 %, 2.5 %, 1.25 %, 0.63 %), so the `1 / grid` scaling is the grid part of this expression. The expression adds the dependence on `dt`, the adaptive step fraction and the region size, and `eta` of healthy runs lies between 0.2 and 3, a factor of ten above the sub-cell dominated counties (0.06).

A rule that requires an improvement of `eta_min * d / L` per window, with `eta_min` a constant, was run on the same cases (`eta_try.py`, `eta_lad.py`; patch in `eta_rule_experiment.patch`). Outcomes (status, iterations, mean error) for `eta_min` from 0.03 to 0.1:

| case | one-way scaling (this PR) | eta rule, eta_min 0.03 to 0.1 |
|---|---|---|
| Arizona 256, 512, 1024; states 64 to 2048; districts 256, 1024 | converged | identical |
| Texas counties 512, 1024; all counties 1024, 2048 | stalled after 480 to 1100 iterations, 1.7 to 11.6 % | identical (all counties 1024 at 0.1: 660 iterations, 4.6 %) |
| districts, lognormal sigma 1 and 2, grids 256 and 512 | stalled | identical within 10 iterations |
| districts 64 | stalled, 110 iterations | stalled, 100 to 80 iterations |
| ladders: states 64x3 and 32x5, districts 128x3 and 64x4, counties 512x3 and 256x4 | converged or stalled as before | identical (districts 64x4 in 188 instead of 208 iterations) |
| ladder districts 32x5 | stalled, 4.88 % | converged in 222 iterations, 1.51 %, 249 invalid |
| ladder counties 128x5 and 64x6 | 17.4 and 31.3 % | 16.9 and 30.8 % |

At `eta_min` 0.2 the all-counties runs stall at the start (929 %), so the usable range is about 0.03 to 0.1 and 0.05 is its middle. With the mean region size instead of the area-weighted one the counties stall at 0.04 already, because the many sub-cell counties make the mean size small; the area-weighted size is the one that matches.

So the rule needs no reference grid and no one-way scaling: the required improvement follows from what the step can do. It also reproduces the fixed 2 % rule on the default grid for typical inputs (`d / L` of about 0.3 gives 1.5 %).
