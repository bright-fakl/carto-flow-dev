---
pr: 171
url: https://github.com/bright-fakl/carto-flow/pull/171
issue: 166
title: Stall rule requires an improvement proportional to the distance moved
description: The stall rule required a fixed 2 % improvement per window, which ended runs on fine grids that were converging, because a step moves the fastest point dt cells and progress per iteration falls with the cell size. A window now has to improve by stall_min_efficiency (0.05) times the distance the boundaries moved divided by the area-weighted region size. Arizona's counties converge at grids 512 and 1024, the states at 2048, all counties at 1024 go from stalled at the start (930 % mean error) to 7.6 %; runs on the default grid are unchanged.
kind: pr
topic: flow
base: main
branch: feat/stall-grid-scaling
date: 2026-10-19 12:00
before: main @ 0491b5b
after: feat/stall-grid-scaling @ 239299d
related: exploration-county-hierarchical-prototype, square-grid-spacing
inputs: bundled states and congressional districts (population), 3,108 counties and the 15 Arizona and 254 Texas counties from the bundled ACS 2020 snapshot (population), districts and states with lognormal values (seed 0). MorphOptions area_scale 1e-6, square grid with margin 0.5, n_iter 3000 (single grids) or 1000 per level (ladders). NUMBA_NUM_THREADS=8.
---

## Figures

figure: fig_counties.png — Counties by population on a single grid of 1024 with default options, main (stalled after 50 iterations, 929.6 % mean error) and this PR (stalled after 600 iterations, 7.6 %). Color is log2(area/target); red is too large.

## Rule

A step moves the fastest point `dt` times the adaptive step fraction times the cell size. A region of linear size `L` changes its area, and with it its error, by a fraction of order `distance / L`. A window of 10 iterations therefore has to lower a violated component's minimum below its best earlier minimum by at least `stall_min_efficiency * (sum of the distances of the window) / L`, with `L = sqrt(sum(T^2) / sum(T))` over the target areas `T`. The option replaces `stall_min_improvement`, which was never released (it appeared after 2.0.0 in the stall rule of PR 110). At the default grid and `dt` the requirement is about 1 to 2 % for typical inputs, as before.

## Single grids: main and this PR

Stall detection on in both (the previous column is main, which already has the square-grid fix).

| input | grid | main | this PR |
|---|---|---|---|
| AZ | 256 | converged, 202 it, mean 1.08 % | converged, 202 it, mean 1.08 % |
| AZ | 512 | stalled, 50 it, mean 393.7 % | converged, 382 it, mean 1.13 % |
| AZ | 1024 | stalled, 50 it, mean 414.13 % | converged, 755 it, mean 1.61 % |
| TX | 512 | stalled, 50 it, mean 1939.46 % | stalled, 590 it, mean 5.45 % |
| TX | 1024 | stalled, 50 it, mean 2054.91 % | stalled, 1050 it, mean 0.48 % |
| states | 64 | converged, 82 it, mean 3.37 % | converged, 82 it, mean 3.37 % |
| states | 256 | converged, 111 it, mean 0.71 % | converged, 111 it, mean 0.71 % |
| states | 1024 | converged, 421 it, mean 0.56 % | converged, 421 it, mean 0.56 % |
| states | 2048 | stalled, 90 it, mean 165.85 % | converged, 833 it, mean 0.93 % |
| districts | 64 | stalled, 190 it, mean 32.04 % | stalled, 100 it, mean 92.9 % |
| districts | 256 | converged, 145 it, mean 1.44 % | converged, 145 it, mean 1.44 % |
| districts | 1024 | converged, 511 it, mean 0.63 % | converged, 511 it, mean 0.63 % |
| counties | 1024 | stalled, 50 it, mean 929.62 % | stalled, 600 it, mean 7.65 % |
| counties | 2048 | stalled, 50 it, mean 968.12 % | stalled, 1100 it, mean 3.15 % |
| districts lognormal1 | 256 | stalled, 490 it, mean 2.1 % | stalled, 490 it, mean 2.1 % |
| districts lognormal1 | 512 | converged, 625 it, mean 0.37 % | converged, 625 it, mean 0.37 % |
| districts lognormal2 | 256 | stalled, 350 it, mean 242.67 % | stalled, 390 it, mean 242.67 % |
| districts lognormal2 | 512 | stalled, 450 it, mean 148.46 % | stalled, 510 it, mean 149.68 % |
| states lognormal2 | 256 | converged, 478 it, mean 0.66 % | converged, 478 it, mean 0.66 % |

## Ladders: main and this PR

Default options, ladder from the first grid for the given number of levels.

| ladder | main | this PR |
|---|---|---|
| states 64x3 | converged, 82 it, mean 3.37 %, 0 invalid | converged, 82 it, mean 3.37 %, 0 invalid |
| states 32x5 | converged, 256 it, mean 1.96 %, 0 invalid | converged, 256 it, mean 1.96 %, 0 invalid |
| districts 128x3 | converged, 134 it, mean 0.88 %, 15 invalid | converged, 134 it, mean 0.88 %, 15 invalid |
| districts 64x4 | stalled, 420 it, mean 1.83 %, 196 invalid | converged, 200 it, mean 1.07 %, 24 invalid |
| districts 32x5 | stalled, 380 it, mean 3.53 %, 177 invalid | stalled, 360 it, mean 3.53 %, 177 invalid |
| counties 512x3 | stalled, 530 it, mean 3.4 %, 301 invalid | stalled, 550 it, mean 3.4 %, 301 invalid |
| counties 256x4 | stalled, 630 it, mean 4.19 %, 321 invalid | stalled, 700 it, mean 4.19 %, 321 invalid |
| counties 128x5 | stalled, 690 it, mean 15.18 %, 378 invalid | stalled, 690 it, mean 28.37 %, 406 invalid |
| counties 64x6 | stalled, 610 it, mean 7.78 %, 419 invalid | stalled, 850 it, mean 17.13 %, 641 invalid |

## Reading

- On the default grid and coarser, results are identical where runs converge (Arizona 256, states 64 to 1024, districts 256 and 1024). Runs with the stall rule at work on genuinely hard values (lognormal, sigma 1 and 2) are unchanged within 60 iterations.
- The runs that the old rule ended after 50 iterations at 512 cells and above (Arizona 512 and 1024, Texas, states at 2048, all counties at 1024 and 2048) now run until they converge or make no more progress.
- Districts on a grid of 64 cells (76 % of the districts below one cell) stall after 100 instead of 190 iterations with a worse best iterate (92.9 % against 32.0 % mean error); that start is not usable in either case.
- In ladders only the starts that are too coarse change: districts 64x4 converges (in 200 iterations, 24 invalid polygons) instead of stalling after 420 (196 invalid); counties from 64 and 128 cells end at 17.1 and 28.4 % mean error against 7.8 and 15.2 % on main. The sub-cell damage of coarse levels remains the subject of issue 167.
- The ladder from 256 or 512 cells on counties is identical to main (4.2 and 3.4 % mean error).

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

The experiment that led to the rule of this PR compared it with the earlier one-way scaling by `256 / cells` (`eta_try.py`, `eta_lad.py`; patch in `eta_rule_experiment.patch`), on the grid code before the square-grid fix. Outcomes (status, iterations, mean error) for `eta_min` from 0.03 to 0.1:

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
