---
issue: 93, 116
title: Starting resolution and refinement of the multiresolution morph
description: What the start grid, the finest grid and the tolerance of the coarse levels do to a multiresolution flow cartogram on states, districts and counties, for population and for other value distributions. The share of regions with a target below one cell predicts the failures; the smallest region in cells is a better start rule than that share (districts converge from 128, 2.7 cells, and fail from 96, 1.5 cells). A start at the finest grid diverges on fine grids (1024 and 2048) where the ladder reaches them, and coarse levels at four times the tolerance let the ladder refine to the finest grid in 1 to 16 iterations per level. Counties converge in no variant.
kind: exploration
topic: flow
status: open
related: exploration-counties-subcell, flow-convergence-synthesis, adaptive-step-control
date: 2026-10-12 02:25
before: main @ b5a37be
after: the same checkout; start grid, finest grid, tolerance per level and values varied
inputs: 49 states and 432 congressional districts (bundled), 3,108 counties (prepared set, ESRI:102008, total_votes, area_scale 1e-6, not bundled). MorphOptions defaults except mean_tol / max_tol (5 % / 10 % default, 1 % / 3 % tight, 0.5 % / 1 % very tight, 10 % / 30 % loose); grids from build_multilevel_grids (margin 0.5, square); NUMBA_NUM_THREADS=8. True error is the output area against the target share of the total output area.
---

`start_resolution.py` and `relaxed_coarse.py` run the cases and write JSON to `data/`; `make_tables.py` turns it into `data/tables.md` (every table below). Counties are not bundled; `start_resolution.py` reads the prepared set from `COUNTIES_PARQUET`. `relaxed_coarse.py` uses its own level loop: `morph_multiresolution` ends at the first converged level, so with relaxed coarse levels it would never refine.

## Findings

- **Sub-cell share.** Regions with a target area below one grid cell predict the failures. Counties have 89 %, 67 %, 27 %, 5 %, 0.3 % and 0.03 % of such regions at grids 128, 256, 512, 1024, 2048 and 4096; states and districts have none from 128 up. Smallest county: 0.001 cells at 128 and 0.72 at 4096.
- **Start rule.** The share under one cell does not separate the districts cases: 128 (smallest region 2.7 cells) converges at every tolerance from 0.5 % / 1 % to 10 % / 30 %, and 96 (1.5 cells, also 0 % under one cell) stalls at every level except at 10 % / 30 %. The start 64 (76 % under one cell) stalls at 64 and converges after one refinement. The tolerance does not move this boundary in the range tested.
- **Fine start.** Starting at the finest grid fails on fine grids: districts 1024 and 2048 reach 500 iterations at a mean error of 2.4 % and 57 %; states at 2048 stall at 166 % mean error after 90 iterations; counties at 1024 and 2048 stall after 50 iterations at about 800 % mean. The ladder reaches the same grids. The cause is not identified.
- **Strict ladder.** With the same tolerance at every level the run ends at the first level that meets it, so refinement never runs on states and districts.
- **Relaxed ladder.** With coarse levels at four times the tolerance, every level converges and the finer levels need 1 to 16 iterations. At the same tolerance the final error is as low or lower than the strict ladder's (districts, population, finest 1024: mean 0.04 % and max 0.9 % against 0.21 % and 2.9 %). Invalid output polygons do not fall (46 against 44). The time saving is small where one grid already converges.
- **Other values.** Values that are smooth over the map behave like population (smooth1). Smooth2 stalls on districts in every scheme (mean 4 to 5 %). Random lognormal values do not converge on districts at σ=1 and σ=2 in any scheme (stall or 500 iterations), with 20 % and 62 % of the districts under one cell at grid 128 and 0.2 % and 13 % at 512; the random values are far more extreme than real data and are a stress test.
- **Counties.** No start or finest grid up to 4096 converges. The mean error falls with the finest grid when the start is 512 (6.5 %, 2.9 %, 1.6 % at 1024, 2048, 4096) while the maximum stays near 340 % and the invalid count stays near 300. Starts at 1024 and 2048 stall after 50 iterations at about 800 % mean error. A grid of 8192 is not tested: its solver arrays alone are about 2.7 GB on a machine with 4 GB available.
- **Stall rule.** Refinement levels stall after about 50 iterations when the previous level stalled, so damage from a coarse level that did not converge is not repaired by finer levels.

## Start grid (finest 512 on districts, 1024 on others), default and tight tolerance

| input | tolerance | start | regions < 1 cell at start | status | iterations | true mean / max % | invalid | levels (grid status iterations) |
|---|---|---|---|---|---|---|---|---|
| states | default | 64 | 8.2 % | converged | 74 | 2.86 / 7.3 | 5 | 64 conv 74 |
| states | default | 128 | 0.0 % | converged | 63 | 1.61 / 9.2 | 0 | 128 conv 63 |
| states | default | 256 | 0.0 % | converged | 111 | 0.50 / 5.9 | 0 | 256 conv 111 |
| states | default | 512 | 0.0 % | converged | 215 | 0.40 / 6.0 | 0 | 512 conv 215 |
| states | default | 1024 | 0.0 % | converged | 420 | 0.74 / 9.3 | 0 | 1024 conv 420 |
| counties | default | 64 | 97.4 % | stalled | 640 | 45.32 / 4733.5 | 2455 | 64 stal 90, 128 stal 100, 256 stal 80, 512 stal 140, 1024 stal 230 |
| counties | default | 128 | 88.9 % | stalled | 490 | 22.14 / 3593.7 | 1577 | 128 stal 120, 256 stal 120, 512 stal 140, 1024 stal 110 |
| counties | default | 256 | 67.4 % | stalled | 490 | 8.45 / 787.2 | 612 | 256 stal 200, 512 stal 180, 1024 stal 110 |
| counties | default | 512 | 27.3 % | stalled | 490 | 6.46 / 496.4 | 277 | 512 stal 410, 1024 stal 80 |
| counties | default | 1024 | 5.3 % | stalled | 50 | 853.60 / 49422.1 | 2 | 1024 stal 50 |
| counties | tight | 64 | 97.4 % | stalled | 640 | 45.32 / 4733.5 | 2455 | 64 stal 90, 128 stal 100, 256 stal 80, 512 stal 140, 1024 stal 230 |
| counties | tight | 128 | 88.9 % | stalled | 490 | 22.14 / 3593.7 | 1577 | 128 stal 120, 256 stal 120, 512 stal 140, 1024 stal 110 |
| counties | tight | 256 | 67.4 % | stalled | 540 | 8.45 / 787.2 | 612 | 256 stal 200, 512 stal 180, 1024 stal 160 |
| counties | tight | 512 | 27.3 % | stalled | 600 | 3.26 / 475.1 | 346 | 512 stal 410, 1024 stal 190 |
| counties | tight | 1024 | 5.3 % | stalled | 50 | 853.60 / 49422.1 | 2 | 1024 stal 50 |
| districts | default | 64 | 75.9 % | converged | 208 | 1.12 / 9.6 | 109 | 64 stal 110, 128 conv 98 |
| districts | default | 128 | 0.0 % | converged | 123 | 0.76 / 8.3 | 48 | 128 conv 123 |
| districts | default | 256 | 0.0 % | converged | 149 | 0.47 / 7.2 | 20 | 256 conv 149 |
| districts | default | 512 | 0.0 % | converged | 266 | 0.53 / 8.7 | 14 | 512 conv 266 |
| districts | default | 1024 | 0.0 % | completed | 500 | 2.36 / 36.1 | 13 | 1024 comp 500 |
| districts | tight | 64 | 75.9 % | converged | 229 | 0.18 / 2.6 | 109 | 64 stal 110, 128 conv 119 |
| districts | tight | 128 | 0.0 % | converged | 150 | 0.21 / 2.9 | 44 | 128 conv 150 |
| districts | tight | 256 | 0.0 % | converged | 153 | 0.28 / 2.9 | 20 | 256 conv 153 |
| districts | tight | 512 | 0.0 % | converged | 270 | 0.19 / 1.8 | 16 | 512 conv 270 |
| districts | tight | 1024 | 0.0 % | completed | 500 | 2.36 / 36.1 | 13 | 1024 comp 500 |
| states | tight | 64 | 8.2 % | converged | 95 | 0.66 / 1.4 | 7 | 64 conv 95 |
| states | tight | 128 | 0.0 % | converged | 66 | 0.21 / 1.3 | 0 | 128 conv 66 |
| states | tight | 256 | 0.0 % | converged | 115 | 0.42 / 1.5 | 0 | 256 conv 115 |
| states | tight | 512 | 0.0 % | converged | 216 | 0.28 / 1.7 | 0 | 512 conv 216 |
| states | tight | 1024 | 0.0 % | converged | 422 | 0.17 / 2.3 | 0 | 1024 conv 422 |
| districts | loose | 64 | 75.9 % | converged | 188 | 3.45 / 29.9 | 106 | 64 stal 110, 128 conv 78 |
| districts | loose | 96 | 0.0 % | converged | 189 | 2.09 / 23.9 | 197 | 96 conv 189 |
| districts | loose | 128 | 0.0 % | converged | 109 | 2.59 / 23.7 | 41 | 128 conv 109 |
| districts | default | 64 | 75.9 % | converged | 208 | 1.12 / 9.6 | 109 | 64 stal 110, 128 conv 98 |
| districts | default | 96 | 0.0 % | stalled | 360 | 1.09 / 13.7 | 208 | 96 stal 260, 192 stal 50, 384 stal 50 |
| districts | default | 128 | 0.0 % | converged | 123 | 0.76 / 8.3 | 48 | 128 conv 123 |
| districts | tight | 64 | 75.9 % | converged | 229 | 0.18 / 2.6 | 109 | 64 stal 110, 128 conv 119 |
| districts | tight | 96 | 0.0 % | stalled | 360 | 1.14 / 19.8 | 209 | 96 stal 260, 192 stal 50, 384 stal 50 |
| districts | tight | 128 | 0.0 % | converged | 150 | 0.21 / 2.9 | 44 | 128 conv 150 |
| districts | vtight | 64 | 75.9 % | converged | 296 | 0.27 / 1.0 | 113 | 64 stal 110, 128 conv 186 |
| districts | vtight | 96 | 0.0 % | stalled | 380 | 0.92 / 16.5 | 215 | 96 stal 270, 192 stal 60, 384 stal 50 |
| districts | vtight | 128 | 0.0 % | converged | 157 | 0.07 / 0.7 | 50 | 128 conv 157 |

## Counties, finest grid 2048 and 4096

| start | levels | true mean / max % | invalid |
|---|---|---|---|
| 256 | 256 stal 200, 512 stal 180, 1024 stal 110, 2048 stal 50 | 7.8 / 720 | 623 |
| 512 | 512 stal 410, 1024 stal 80, 2048 stal 60 | 2.9 / 371 | 299 |
| 1024 | 1024 stal 50, 2048 stal 50 | 812.4 / 47026 | 5 |
| 2048 | 2048 stal 50, 4096 stal 50 | 870.6 / 50426 | 2 |

## Single grid, strict ladder, relaxed ladder (tolerance 1 % / 3 %; relaxed: coarse levels at 4 times)

| input | values | finest | scheme | status | iterations | seconds | true mean / max % | invalid | levels |
|---|---|---|---|---|---|---|---|---|---|
| districts | population | 512 | single | converged | 270 | 1.9 | 0.19 / 1.8 | 16 | 512 conv 270 |
| districts | population | 512 | strict | converged | 150 | 1.0 | 0.21 / 2.9 | 44 | 128 conv 150 |
| districts | population | 512 | relaxed | converged | 133 | 1.1 | 0.17 / 2.7 | 48 | 128 conv 123, 256 conv 1, 512 conv 9 |
| districts | lognormal1 | 512 | single | completed | 500 | 1.9 | 0.96 / 68.5 | 69 | 512 comp 500 |
| districts | lognormal1 | 512 | strict | stalled | 520 | 2.6 | 7.20 / 485.7 | 237 | 128 stal 310, 256 stal 120, 512 stal 90 |
| districts | lognormal1 | 512 | relaxed | stalled | 520 | 2.4 | 7.20 / 485.7 | 237 | 128 stal 310, 256 stal 120, 512 stal 90 |
| districts | lognormal2 | 512 | single | stalled | 420 | 1.8 | 227.11 / 53652.4 | 270 | 512 stal 420 |
| districts | lognormal2 | 512 | strict | stalled | 410 | 1.6 | 678.03 / 169998.0 | 375 | 128 stal 200, 256 stal 100, 512 stal 110 |
| districts | lognormal2 | 512 | relaxed | stalled | 410 | 1.6 | 678.03 / 169998.0 | 375 | 128 stal 200, 256 stal 100, 512 stal 110 |
| districts | area_like | 512 | single | stalled | 100 | 0.9 | 3.50 / 35.7 | 0 | 512 stal 100 |
| districts | area_like | 512 | strict | stalled | 340 | 2.6 | 4.73 / 53.9 | 0 | 128 stal 130, 256 stal 140, 512 stal 70 |
| districts | area_like | 512 | relaxed | stalled | 250 | 1.9 | 4.30 / 56.4 | 1 | 128 stal 110, 256 stal 50, 512 stal 90 |
| districts | inverse_area | 512 | single | completed | 500 | 2.3 | 3.86 / 134.6 | 112 | 512 comp 500 |
| districts | inverse_area | 512 | strict | stalled | 490 | 1.9 | 18.67 / 330.6 | 289 | 128 stal 230, 256 stal 140, 512 stal 120 |
| districts | inverse_area | 512 | relaxed | stalled | 490 | 1.9 | 18.67 / 330.6 | 289 | 128 stal 230, 256 stal 140, 512 stal 120 |
| states | population | 256 | single | converged | 115 | 0.5 | 0.42 / 1.5 | 0 | 256 conv 115 |
| states | population | 256 | strict | converged | 95 | 0.2 | 0.66 / 1.4 | 7 | 64 conv 95 |
| states | population | 256 | relaxed | converged | 87 | 0.6 | 0.15 / 2.3 | 5 | 64 conv 74, 128 conv 1, 256 conv 12 |
| states | lognormal1 | 256 | single | converged | 113 | 0.2 | 0.43 / 1.9 | 1 | 256 conv 113 |
| states | lognormal1 | 256 | strict | converged | 88 | 0.2 | 0.35 / 2.8 | 12 | 64 conv 88 |
| states | lognormal1 | 256 | relaxed | converged | 67 | 0.3 | 0.25 / 2.8 | 11 | 64 conv 62, 128 conv 1, 256 conv 4 |
| states | lognormal2 | 256 | single | completed | 500 | 0.7 | 1.14 / 10.9 | 11 | 256 comp 500 |
| states | lognormal2 | 256 | strict | stalled | 270 | 0.9 | 15.25 / 106.5 | 36 | 64 stal 160, 128 stal 50, 256 stal 60 |
| states | lognormal2 | 256 | relaxed | stalled | 270 | 0.9 | 17.61 / 118.2 | 33 | 64 stal 150, 128 stal 60, 256 stal 60 |
| states | area_like | 256 | single | converged | 156 | 0.3 | 0.45 / 2.8 | 0 | 256 conv 156 |
| states | area_like | 256 | strict | converged | 193 | 0.5 | 0.86 / 2.7 | 6 | 64 stal 110, 128 stal 50, 256 conv 33 |
| states | area_like | 256 | relaxed | converged | 244 | 0.6 | 0.29 / 2.9 | 3 | 64 stal 100, 128 stal 50, 256 conv 94 |
| states | inverse_area | 256 | single | stalled | 270 | 0.4 | 2.64 / 42.1 | 4 | 256 stal 270 |
| states | inverse_area | 256 | strict | stalled | 240 | 0.6 | 3.47 / 19.7 | 13 | 64 stal 140, 128 stal 50, 256 stal 50 |
| states | inverse_area | 256 | relaxed | stalled | 240 | 0.5 | 3.09 / 18.6 | 12 | 64 stal 140, 128 stal 50, 256 stal 50 |
| states | smooth1 | 256 | single | converged | 87 | 1.3 | 0.16 / 1.5 | 1 | 256 conv 87 |
| states | smooth1 | 256 | strict | converged | 64 | 0.3 | 0.41 / 2.7 | 5 | 64 conv 64 |
| states | smooth1 | 256 | relaxed | converged | 38 | 0.5 | 0.19 / 1.6 | 4 | 64 conv 34, 128 conv 1, 256 conv 3 |
| states | smooth2 | 256 | single | converged | 236 | 0.5 | 0.95 / 2.9 | 3 | 256 conv 236 |
| states | smooth2 | 256 | strict | converged | 378 | 0.7 | 0.58 / 2.7 | 20 | 64 stal 170, 128 stal 130, 256 conv 78 |
| states | smooth2 | 256 | relaxed | converged | 304 | 0.8 | 0.35 / 2.8 | 25 | 64 stal 160, 128 stal 70, 256 conv 74 |
| states | density | 256 | single | converged | 115 | 0.2 | 0.42 / 1.5 | 0 | 256 conv 115 |
| states | density | 256 | strict | converged | 95 | 0.2 | 0.66 / 1.4 | 7 | 64 conv 95 |
| states | density | 256 | relaxed | converged | 87 | 0.3 | 0.15 / 2.3 | 5 | 64 conv 74, 128 conv 1, 256 conv 12 |
| districts | smooth1 | 512 | single | stalled | 330 | 2.7 | 0.18 / 4.2 | 0 | 512 stal 330 |
| districts | smooth1 | 512 | strict | stalled | 440 | 3.4 | 0.14 / 3.2 | 6 | 128 stal 150, 256 stal 80, 512 stal 210 |
| districts | smooth1 | 512 | relaxed | stalled | 350 | 2.4 | 0.51 / 6.5 | 12 | 128 stal 130, 256 stal 120, 512 stal 100 |
| districts | smooth2 | 512 | single | stalled | 400 | 1.5 | 5.34 / 151.4 | 46 | 512 stal 400 |
| districts | smooth2 | 512 | strict | stalled | 570 | 2.2 | 4.26 / 44.8 | 121 | 128 stal 170, 256 stal 100, 512 stal 300 |
| districts | smooth2 | 512 | relaxed | stalled | 620 | 2.3 | 4.31 / 51.4 | 119 | 128 stal 170, 256 stal 100, 512 stal 350 |
| districts | density | 512 | single | converged | 270 | 1.1 | 0.19 / 1.8 | 16 | 512 conv 270 |
| districts | density | 512 | strict | converged | 150 | 0.7 | 0.21 / 2.9 | 44 | 128 conv 150 |
| districts | density | 512 | relaxed | converged | 133 | 0.8 | 0.17 / 2.7 | 48 | 128 conv 123, 256 conv 1, 512 conv 9 |
| states | population | 1024 | single | converged | 422 | 5.2 | 0.17 / 2.3 | 0 | 1024 conv 422 |
| states | population | 1024 | strict | converged | 66 | 0.4 | 0.21 / 1.3 | 0 | 128 conv 66 |
| states | population | 1024 | relaxed | converged | 77 | 1.6 | 0.35 / 2.1 | 0 | 128 conv 63, 256 conv 1, 512 conv 1, 1024 conv 12 |
| states | smooth1 | 1024 | single | converged | 326 | 2.1 | 0.20 / 1.5 | 0 | 1024 conv 326 |
| states | smooth1 | 1024 | strict | converged | 98 | 0.2 | 0.92 / 2.8 | 2 | 128 conv 98 |
| states | smooth1 | 1024 | relaxed | converged | 58 | 0.5 | 0.28 / 2.9 | 2 | 128 conv 45, 256 conv 1, 512 conv 1, 1024 conv 11 |
| states | lognormal1 | 1024 | single | converged | 417 | 2.9 | 0.14 / 0.5 | 0 | 1024 conv 417 |
| states | lognormal1 | 1024 | strict | converged | 87 | 0.2 | 0.50 / 1.7 | 5 | 128 conv 87 |
| states | lognormal1 | 1024 | relaxed | converged | 86 | 0.7 | 0.27 / 2.9 | 4 | 128 conv 68, 256 conv 1, 512 conv 1, 1024 conv 16 |
| districts | population | 1024 | single | completed | 500 | 4.2 | 2.36 / 36.1 | 13 | 1024 comp 500 |
| districts | population | 1024 | strict | converged | 150 | 0.6 | 0.21 / 2.9 | 44 | 128 conv 150 |
| districts | population | 1024 | relaxed | converged | 136 | 1.2 | 0.04 / 0.9 | 46 | 128 conv 123, 256 conv 1, 512 conv 1, 1024 conv 11 |
| districts | smooth1 | 1024 | single | converged | 343 | 3.3 | 0.12 / 2.9 | 0 | 1024 conv 343 |
| districts | smooth1 | 1024 | strict | converged | 443 | 2.9 | 0.11 / 3.0 | 6 | 128 stal 150, 256 stal 80, 512 stal 210, 1024 conv 3 |
| districts | smooth1 | 1024 | relaxed | stalled | 347 | 3.0 | 0.22 / 6.6 | 9 | 128 stal 130, 256 stal 120, 512 conv 47, 1024 stal 50 |
| districts | lognormal1 | 1024 | single | completed | 500 | 4.3 | 29.00 / 3735.1 | 25 | 1024 comp 500 |
| districts | lognormal1 | 1024 | strict | stalled | 600 | 4.3 | 7.11 / 502.8 | 237 | 128 stal 310, 256 stal 120, 512 stal 90, 1024 stal 80 |
| districts | lognormal1 | 1024 | relaxed | stalled | 570 | 4.1 | 7.11 / 502.8 | 237 | 128 stal 310, 256 stal 120, 512 stal 60, 1024 stal 80 |
| states | population | 2048 | single | stalled | 90 | 13.0 | 165.87 / 1518.9 | 0 | 2048 stal 90 |
| states | population | 2048 | strict | converged | 115 | 0.7 | 0.42 / 1.5 | 0 | 256 conv 115 |
| states | population | 2048 | relaxed | converged | 123 | 2.4 | 0.24 / 2.8 | 0 | 256 conv 111, 512 conv 1, 1024 conv 1, 2048 conv 10 |
| states | smooth1 | 2048 | single | stalled | 50 | 1.4 | 147.86 / 846.6 | 0 | 2048 stal 50 |
| states | smooth1 | 2048 | strict | converged | 87 | 0.2 | 0.16 / 1.5 | 1 | 256 conv 87 |
| states | smooth1 | 2048 | relaxed | converged | 100 | 1.0 | 0.24 / 1.9 | 1 | 256 conv 84, 512 conv 1, 1024 conv 1, 2048 conv 14 |
| districts | population | 2048 | single | completed | 500 | 14.0 | 57.33 / 885.0 | 11 | 2048 comp 500 |
| districts | population | 2048 | strict | converged | 153 | 0.5 | 0.28 / 2.9 | 20 | 256 conv 153 |
| districts | population | 2048 | relaxed | converged | 162 | 1.7 | 0.17 / 2.6 | 20 | 256 conv 145, 512 conv 1, 1024 conv 1, 2048 conv 15 |
| districts | smooth1 | 2048 | single | stalled | 50 | 1.6 | 162.78 / 965.9 | 0 | 2048 stal 50 |
| districts | smooth1 | 2048 | strict | converged | 289 | 2.4 | 0.40 / 2.8 | 1 | 256 stal 160, 512 stal 100, 1024 conv 29 |
| districts | smooth1 | 2048 | relaxed | stalled | 316 | 13.2 | 0.06 / 3.9 | 5 | 256 stal 150, 512 conv 25, 1024 conv 1, 2048 stal 140 |
