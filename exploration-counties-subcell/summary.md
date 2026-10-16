---
issue: 93, 109
title: Why the counties do not converge: targets below the grid resolution
description: At grid 256, 67 % of the 3,108 counties have a target area below one grid cell (27 % at 512, 5 % at 1024). Finer grids and multiresolution lower the mean error to about 20 % but every run stalls or plateaus; the worst regions are all sub-cell and are held at 0.1 to 1 cell, while the regions with a target of at least one cell have a median error of 2.6 %. The ring orientation fix does not change this.
kind: exploration
topic: flow
status: led-to
related: exact-ring-orientation, flow-convergence-synthesis, exploration-hierarchical-morph
date: 2026-10-11 23:36
before: main @ 2a03f40
after: the same checkout; grid, multiresolution and stall rule varied
inputs: 3,108 counties (prepared set, ESRI:102008, total_votes, area_scale 1e-6, not bundled); MorphOptions defaults (adaptive_dt on, exact rasterization, error floor 1e-3) except where stated; n_iter 300; NUMBA_NUM_THREADS=8. True error is the output area against the vote share of the total output area.
---

`counties_check.py` regenerates `data/tables.md` (every table below). The counties are not bundled; the script reads the prepared set from `COUNTIES_PARQUET`.

The counties never converged in the earlier flow work (stalled at 210 iterations at grid 256, true mean error about 50 %). This page checks whether the ring orientation fix (#124) or the resolution is the cause.

## Targets below one grid cell

Votes range from 66 to 4263443 (median 12528); the target area of a county is its share of the total area.

| grid | counties with a target area below one cell | below 0.1 cell |
|---|---|---|
| 256 | 2093 (67 %) | 296 |
| 512 | 852 (27 %) | 30 |
| 1024 | 164 (5 %) | 1 |
| 2048 | 8 (0 %) | 0 |

## Single-level runs (stall rule on, 300 iterations)

| grid | status, iterations | true mean / max error % | regions with target < 1 cell: count, median error % | other regions: median error %, max error % | regions off by > 10 % (of which target < 1 cell) | invalid output regions |
|---|---|---|---|---|---|---|
| 256 | stalled, 210 | 66.7 / 5738 | 2093, 43 | 12.1, 206 | 2366 (1802) | 7 |
| 512 | completed, 300 | 20.6 / 1273 | 852, 28 | 2.6, 162 | 1143 (654) | 51 |
| 1024 | stalled, 50 | 853.4 / 49408 | 164, 5338 | 118.7, 20920 | 2994 (164) | 2 |

## Multiresolution (128 to 1024, 4 levels)

Levels: stalled 120, stalled 120, stalled 140, stalled 110; true mean 22.1 %, max 3594 %, 1066 regions off by more than 10 % (11 s).

## Stall rule off, grid 512 (reported mean / max error % at iteration)

| 1 | 50 | 100 | 200 | 300 | 500 | 800 | 1200 | 1500 |
|---|---|---|---|---|---|---|---|---|
| 370.6 / 53342 | 294.6 / 45089 | 230.3 / 34919 | 111.5 / 13776 | 15.8 / 2001 | 11.7 / 963 | 9.3 / 5351 | 9.2 / 5351 | 10.5 / 7078 |

## Worst regions, grid 512 (stall rule on)

| county | error % | target (cells) | area (cells) |
|---|---|---|---|
| 48261 | 1273 | 0.033 | 0.45 |
| 31007 | 788 | 0.070 | 0.62 |
| 48301 | 734 | 0.011 | 0.09 |
| 48033 | 722 | 0.071 | 0.58 |
| 48269 | 667 | 0.027 | 0.21 |
| 48173 | 497 | 0.111 | 0.66 |
| 31165 | 484 | 0.125 | 0.73 |
| 48137 | 456 | 0.182 | 1.01 |

Sub-cell regions: target 458 cells in total, actual 557 cells; all other regions: target 26412, actual 26313. Regions with a target of at least one cell and an error above 10 %: 489 of 2256 (median error of that group 2.6 %).

## Reading

- **The ring orientation fix does not change it.** With the fix the grid-256 run still stalls at 210 iterations (true mean 66.7 %; before the fix 49.6 %, the best iterate differs between the two).
- **Resolution is the limit.** Most counties have a target below one cell at grid 256 (67 %), so the flow cannot shrink them to their targets: at grid 512 the worst regions have targets of 0.01 to 0.2 cells and stay at 0.1 to 1.1 cells. Together the sub-cell regions hold 458 cells of target and 557 cells of area, 0.4 % of the map, so the bulk is well resolved: of the 2,256 regions with a target of at least one cell, 489 are off by more than 10 % and their median error is 2.6 %.
- **Finer grids and multiresolution help only in the mean.** The mean error falls from 66.7 % (256) to 20.6 % (512) and about 22 % with multiresolution to 1024, but every level stalls. A single level at 1024 stalls after 50 iterations because it starts too far from the target. With the stall rule off at grid 512 the mean error plateaus at 9 to 12 % from iteration 500 and the maximum error swings between about 1,000 % and 7,000 % late in the run.
- **The tolerances apply to every region,** so a run with sub-cell regions cannot meet them and the stall rule stops it correctly. A warning for regions below one cell and a multiresolution trigger that accounts for them are the subject of #93; whether a cell-aware error criterion is wanted is open.
