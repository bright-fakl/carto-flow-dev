---
issue: 93, 109
title: Stall parameters per level and an iteration budget for the multiresolution ladder
description: Treating the cartogram-cpp trigger (go to the next grid when the maximum error is not below 0.8 times its previous value) as a stall rule with short windows on the coarse levels lowers the cost by 20 to 60 % where the ladder already works and converges a skewed-value case that stalls with the defaults, but it leaves coarse levels unconverged where they are needed (districts from 64, counties) and makes those results much worse. A total iteration budget never binds except on counties, where it halves the cost at the same error. No change to the defaults is supported.
kind: exploration
topic: flow
status: led-to
related: exploration-multires-start, adaptive-step-control
date: 2026-10-12 23:30
before: main @ 5a4a5a2
after: the same checkout; stall parameters of the coarse levels and the iteration budget varied through a per-level loop
inputs: states (49) and districts (432), bundled, with population, area-like, inverse-area, smooth (sigma 2) and lognormal (sigma 2) values; 3,108 counties (prepared set, ESRI:102008, total_votes, area_scale 1e-6, not bundled). Tolerances 1 % / 3 %, n_iter 500 per level, adaptive_dt on, NUMBA_NUM_THREADS=8. Cost is iterations plus recomputes times the cost of one recompute at the grid of the last level (preset-review table; the 2048 value is extrapolated, so compare wall seconds for counties). True error is the output area against the target share of the total output area.
closed: 2026-10-12 23:30
---

`stall_levels.py` runs the cases (levels in a loop, so each level has its own stall parameters; the stall window is patched through `alg.cycle_length`), `make_tables.py` writes `data/tables.md`. Counties are read from `COUNTIES_PARQUET`.

Variants (window, patience, required improvement on the levels before the last; the last level always uses 10, 4, 2 %):

- `baseline`: 10, 4, 2 % on every level.
- `cpp`: 4, 1, 20 % (the cartogram-cpp trigger).
- `p1-20`: 10, 1, 20 %.
- `p2-10`: 10, 2, 10 %.
- `budget`: baseline parameters and a total of 600 iterations; each level before the last leaves 150 for the last, and unused iterations roll over.
- `cpp+budget`: both.
- `max-cpp`, `max-p1-20`, `max-p2-10`: the same parameters as `cpp`, `p1-20` and `p2-10`, but progress is judged on the maximum error alone (the mean error never counts), as in cartogram-cpp. The default monitor counts a cycle as progress if either the mean or the maximum error improves; both compare a cycle minimum with the best of the earlier cycles, not with the previous cycle only.

## Findings

- **Short windows on the coarse levels.** `p1-20` lowers the cost against the baseline on states with area-like values (430 against 673), states with lognormal values (1019 against 1758; the baseline stalls at a mean error of 15 %, `p1-20` converges), districts with inverse-area values (1725 against 2100, mean error 4.9 % against 18.7 %) and districts from 64 (709 against 877, same error).
- **Where it fails.** Counties: the coarse levels end after 20 iterations and the finest level starts from a state that is not converged, ending at a mean error of 798 % against 19 %. Districts with smooth (sigma 2) values: mean 10.0 % and max 250 % against 4.3 % and 44.8 %.
- **The cartogram-cpp window of 4 iterations** is worse than a window of 10 where levels are needed: districts from 64 end at a maximum error of 18 % (the baseline converges) after cutting each level at 8 iterations.
- **Maximum error alone.** The variants that judge progress on the maximum error alone stall more often than the default monitor. States with lognormal values: `max-p2-10` converges at a cost of 789 (the default monitor at `p2-10` stalls). Districts from 64: all three max-only variants stall at the last level (maximum errors 18.0 %, 13.6 % and 3.5 %), where the default monitor with `p1-20` and `p2-10` converges at a cost of 709 and 765. Counties and districts with smooth or inverse-area values are unchanged. So the maximum error alone does not make the early trigger safer.
- **Budget.** At 600 iterations it never binds on states and districts (identical to the baseline). On counties it reduces the iterations from 990 to 600 and the wall time from 21.7 s to 10.7 s at the same error, because the run returns its best iterate.
- **Conclusion.** The gains come on inputs where the ladder works and the losses on inputs with many sub-cell regions, which the resolution warning already identifies. A stall-parameter change per level is not supported as a default. A total budget is a safe cap with no measured downside.

| case | variant | status | iterations | recomputes | cost | seconds | true mean / max % | invalid | levels (grid, status, iterations) |
|---|---|---|---|---|---|---|---|---|---|
| states-area | baseline | converged | 193 | 40 | 673 | 1.3 | 0.86 / 2.7 | 6 | 64 stal 110, 128 stal 50, 256 conv 33 |
| states-area | cpp | converged | 55 | 17 | 259 | 0.4 | 0.33 / 2.7 | 2 | 64 stal 12, 128 stal 16, 256 conv 27 |
| states-area | p1-20 | converged | 166 | 22 | 430 | 0.5 | 0.31 / 2.9 | 5 | 64 stal 20, 128 stal 30, 256 conv 116 |
| states-area | p2-10 | converged | 153 | 36 | 585 | 0.5 | 0.86 / 2.7 | 6 | 64 stal 90, 128 stal 30, 256 conv 33 |
| states-area | budget | converged | 193 | 40 | 673 | 0.6 | 0.86 / 2.7 | 6 | 64 stal 110, 128 stal 50, 256 conv 33 |
| states-area | cpp+budget | converged | 55 | 17 | 259 | 0.4 | 0.33 / 2.7 | 2 | 64 stal 12, 128 stal 16, 256 conv 27 |
| states-lognormal2 | baseline | stalled | 270 | 124 | 1758 | 0.9 | 15.25 / 106.5 | 36 | 64 stal 160, 128 stal 50, 256 stal 60 |
| states-lognormal2 | cpp | completed | 516 | 56 | 1188 | 0.9 | 1.58 / 9.4 | 36 | 64 stal 8, 128 stal 8, 256 comp 500 |
| states-lognormal2 | p1-20 | converged | 383 | 53 | 1019 | 0.7 | 0.17 / 2.9 | 37 | 64 stal 20, 128 stal 20, 256 conv 343 |
| states-lognormal2 | p2-10 | stalled | 230 | 120 | 1670 | 0.8 | 15.25 / 106.5 | 36 | 64 stal 140, 128 stal 30, 256 stal 60 |
| states-lognormal2 | budget | stalled | 270 | 124 | 1758 | 0.9 | 15.25 / 106.5 | 36 | 64 stal 160, 128 stal 50, 256 stal 60 |
| states-lognormal2 | cpp+budget | completed | 516 | 56 | 1188 | 0.9 | 1.58 / 9.4 | 36 | 64 stal 8, 128 stal 8, 256 comp 500 |
| districts-smooth2 | baseline | stalled | 570 | 74 | 2272 | 3.4 | 4.26 / 44.8 | 121 | 128 stal 170, 256 stal 100, 512 stal 300 |
| districts-smooth2 | cpp | stalled | 296 | 42 | 1262 | 2.0 | 6.03 / 130.3 | 108 | 128 stal 8, 256 stal 8, 512 stal 280 |
| districts-smooth2 | p1-20 | stalled | 280 | 28 | 924 | 1.7 | 10.04 / 250.0 | 90 | 128 stal 20, 256 stal 20, 512 stal 240 |
| districts-smooth2 | p2-10 | stalled | 520 | 62 | 1946 | 2.4 | 3.41 / 43.3 | 111 | 128 stal 110, 256 stal 60, 512 stal 350 |
| districts-smooth2 | budget | stalled | 570 | 74 | 2272 | 2.6 | 4.26 / 44.8 | 121 | 128 stal 170, 256 stal 100, 512 stal 300 |
| districts-smooth2 | cpp+budget | stalled | 296 | 42 | 1262 | 2.1 | 6.03 / 130.3 | 108 | 128 stal 8, 256 stal 8, 512 stal 280 |
| districts-inverse | baseline | stalled | 490 | 70 | 2100 | 2.2 | 18.67 / 330.6 | 289 | 128 stal 230, 256 stal 140, 512 stal 120 |
| districts-inverse | cpp | stalled | 466 | 72 | 2122 | 2.9 | 4.84 / 130.3 | 172 | 128 stal 8, 256 stal 8, 512 stal 450 |
| districts-inverse | p1-20 | stalled | 460 | 55 | 1725 | 2.4 | 4.93 / 126.7 | 162 | 128 stal 20, 256 stal 20, 512 stal 420 |
| districts-inverse | p2-10 | stalled | 310 | 44 | 1322 | 1.8 | 14.99 / 265.5 | 283 | 128 stal 160, 256 stal 70, 512 stal 80 |
| districts-inverse | budget | stalled | 490 | 70 | 2100 | 2.6 | 18.67 / 330.6 | 289 | 128 stal 230, 256 stal 140, 512 stal 120 |
| districts-inverse | cpp+budget | stalled | 466 | 72 | 2122 | 3.1 | 4.84 / 130.3 | 172 | 128 stal 8, 256 stal 8, 512 stal 450 |
| districts-pop64 | baseline | converged | 229 | 36 | 877 | 1.4 | 0.18 / 2.6 | 109 | 64 stal 110, 128 conv 119 |
| districts-pop64 | cpp | stalled | 244 | 53 | 1463 | 2.9 | 0.97 / 18.0 | 61 | 64 stal 8, 128 stal 8, 256 stal 8, 512 stal 220 |
| districts-pop64 | p1-20 | converged | 169 | 30 | 709 | 1.5 | 0.18 / 2.6 | 109 | 64 stal 50, 128 conv 119 |
| districts-pop64 | p2-10 | converged | 189 | 32 | 765 | 1.2 | 0.18 / 2.6 | 109 | 64 stal 70, 128 conv 119 |
| districts-pop64 | budget | converged | 229 | 36 | 877 | 1.2 | 0.18 / 2.6 | 109 | 64 stal 110, 128 conv 119 |
| districts-pop64 | cpp+budget | stalled | 244 | 53 | 1463 | 2.1 | 0.97 / 18.0 | 61 | 64 stal 8, 128 stal 8, 256 stal 8, 512 stal 220 |
| counties | baseline | stalled | 990 | 99 | 24750 | 21.7 | 18.62 / 3076.1 | 139 | 512 stal 400, 1024 stal 280, 2048 stal 310 |
| counties | cpp | stalled | 66 | 7 | 1746 | 4.5 | 853.40 / 49411.7 | 2 | 512 stal 8, 1024 stal 8, 2048 stal 50 |
| counties | p1-20 | stalled | 90 | 9 | 2250 | 4.8 | 797.63 / 46128.5 | 4 | 512 stal 20, 1024 stal 20, 2048 stal 50 |
| counties | p2-10 | stalled | 110 | 11 | 2750 | 5.1 | 746.91 / 43146.3 | 4 | 512 stal 30, 1024 stal 30, 2048 stal 50 |
| counties | budget | completed | 600 | 60 | 15000 | 10.7 | 18.62 / 3076.1 | 139 | 512 stal 400, 1024 comp 50, 2048 comp 150 |
| counties | cpp+budget | stalled | 66 | 7 | 1746 | 4.5 | 853.40 / 49411.7 | 2 | 512 stal 8, 1024 stal 8, 2048 stal 50 |
| states-area | max-cpp | converged | 47 | 16 | 239 | 1.9 | 0.33 / 2.7 | 2 | 64 stal 8, 128 stal 12, 256 conv 27 |
| states-area | max-p1-20 | converged | 166 | 22 | 430 | 0.5 | 0.31 / 2.9 | 5 | 64 stal 20, 128 stal 30, 256 conv 116 |
| states-area | max-p2-10 | converged | 133 | 34 | 541 | 0.6 | 0.86 / 2.7 | 6 | 64 stal 70, 128 stal 30, 256 conv 33 |
| states-lognormal2 | max-cpp | completed | 516 | 56 | 1188 | 0.9 | 1.58 / 9.4 | 36 | 64 stal 8, 128 stal 8, 256 comp 500 |
| states-lognormal2 | max-p1-20 | converged | 383 | 53 | 1019 | 0.9 | 0.17 / 2.9 | 37 | 64 stal 20, 128 stal 20, 256 conv 343 |
| states-lognormal2 | max-p2-10 | converged | 297 | 41 | 789 | 0.8 | 0.72 / 3.0 | 39 | 64 stal 30, 128 stal 80, 256 conv 187 |
| districts-smooth2 | max-cpp | stalled | 296 | 42 | 1262 | 3.2 | 6.03 / 130.3 | 108 | 128 stal 8, 256 stal 8, 512 stal 280 |
| districts-smooth2 | max-p1-20 | stalled | 280 | 28 | 924 | 2.3 | 10.04 / 250.0 | 90 | 128 stal 20, 256 stal 20, 512 stal 240 |
| districts-smooth2 | max-p2-10 | stalled | 280 | 32 | 1016 | 2.4 | 7.07 / 96.2 | 91 | 128 stal 30, 256 stal 30, 512 stal 220 |
| districts-inverse | max-cpp | stalled | 466 | 72 | 2122 | 3.2 | 4.84 / 130.3 | 172 | 128 stal 8, 256 stal 8, 512 stal 450 |
| districts-inverse | max-p1-20 | stalled | 460 | 55 | 1725 | 2.4 | 4.93 / 126.7 | 162 | 128 stal 20, 256 stal 20, 512 stal 420 |
| districts-inverse | max-p2-10 | stalled | 420 | 57 | 1731 | 2.6 | 5.06 / 137.3 | 161 | 128 stal 30, 256 stal 30, 512 stal 360 |
| districts-pop64 | max-cpp | stalled | 244 | 53 | 1463 | 2.3 | 0.97 / 18.0 | 61 | 64 stal 8, 128 stal 8, 256 stal 8, 512 stal 220 |
| districts-pop64 | max-p1-20 | stalled | 220 | 60 | 1600 | 2.3 | 0.33 / 13.6 | 69 | 64 stal 20, 128 stal 20, 256 stal 20, 512 stal 160 |
| districts-pop64 | max-p2-10 | stalled | 200 | 90 | 2270 | 2.5 | 0.23 / 3.5 | 80 | 64 stal 30, 128 stal 30, 256 stal 90, 512 stal 50 |
| counties | max-cpp | stalled | 66 | 7 | 1746 | 7.0 | 853.40 / 49411.7 | 2 | 512 stal 8, 1024 stal 8, 2048 stal 50 |
| counties | max-p1-20 | stalled | 90 | 9 | 2250 | 5.1 | 797.63 / 46128.5 | 4 | 512 stal 20, 1024 stal 20, 2048 stal 50 |
| counties | max-p2-10 | stalled | 110 | 11 | 2750 | 5.2 | 746.91 / 43146.3 | 4 | 512 stal 30, 1024 stal 30, 2048 stal 50 |
