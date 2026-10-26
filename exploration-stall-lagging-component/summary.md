---
issue: 177
title: Which stall-rule component follows the lagging regions? Candidates on real county, district, state and scene runs
description: Four candidate progress measures for the stall rule (count of regions above max_tol, the same by efficiency, the total log2 excess over the tolerance, the median of the lagging regions) were run in the library on the county ladder (repair-crossings and check), districts, states and strip scenes. Applied on all ladder levels they use the budget on the coarse levels; on the finest level only, the count and the excess behave alike (counties, repair-crossings, budget 3000, no invalid polygons at the stall: CONVERGED after 1842 iterations, mean 0.32 %, none above 10 %), the excess also continues in check mode, and choosing the best iterate by the same excess measure improves the returned iterate. The median does not help. Districts and states are unchanged.
kind: exploration
topic: flow
status: led-to
related: exploration-stall-after-validity, exploration-unresolved-regions, stall-lagging-pr
date: 2026-10-26 23:00
before: feat/unresolved-regions @ f30c2b4
after: feat/stall-lagging-regions (library runs of each candidate on an experimental option)
inputs: 3,108 bundled counties (1 km input, auto ladder), validity="repair-crossings" and "check", n_iter 1000 and 3000 (the total budget of the ladder), default tolerances. Districts (1 km input) and states, n_iter 500 and 1000. Strip scenes of the test suite (seeds 3, 7, 11, 19, 23, 31; grid 64, n_iter 400, mean_tol 2 %, max_tol 5 %). Single runs; several runs shared the machine, so the times are indicative only (iterations are the cost measure). Errors of the valid polygons against targets normalized on the valid polygons.
---

`trace.py` records the three measures at every iteration of the chosen design (counties, repair-crossings, n_iter 3000) and `trace_fig.py` plots them and replays the old rule on the recorded values; `compare.py` runs the candidates (an experimental option, removed again), `final.py` the shipped design, `tables.py` builds the table and the figure.

figure: fig1_designs.png — Counties, repair-crossings: mean error against the iterations of the ladder for each design, at a budget of 1000 and of 3000 iterations. Red: the chosen design.

figure: fig2_trace.png — The finest county level (grid 2048) of the chosen design, per iteration: the mean error ratio and the max error ratio (the two measures of the old rule) and the lagging error (the new one). Red dashed: the iteration at which the old rule, replayed on the same values, stalls (200). Green dashed: where the run ends with the new rule (CONVERGED, 1842).

## Candidates

All judge the cycle minimum like the mean and max components (progress if it falls by the fraction `stall_min_efficiency * moved`):

- (a) the count of regions above `max_tol` (a variant: any fall by 1 or more, and one by the efficiency rule);
- (b) the total log2 excess of the regions above `max_tol` (plus the excess of the mean over `mean_tol`, times the number of regions);
- (c) the median log2 error of the regions above `max_tol`.

"All levels" applies the component on every ladder level; "finest level only" only on the finest. "Best by excess" returns the iterate with the lowest excess instead of the lowest mean/max score.

## Counties

| validity | budget | design | iterations | levels (status, iterations) | invalid | mean % | median % | max % | above 10 % | above 5 % |
|---|---|---|---|---|---|---|---|---|---|---|
| repair-crossings | 1000 | baseline (mean, max) | 780 | stal 500 / stal 80 / stal 200 | 0 | 1.08 | 0.20 | 548 | 45 | 84 |
| repair-crossings | 1000 | (a) count above max_tol, all levels | 1000 | stal 840 / comp 160 | 1 | 3.71 | 0.27 | 543 | 247 | 408 |
| repair-crossings | 1000 | (b) excess, all levels | 1000 | stal 500 / stal 360 / comp 140 | 0 | 1.51 | 0.20 | 515 | 74 | 127 |
| repair-crossings | 1000 | (c) median of lagging, all levels | 920 | stal 500 / stal 100 / stal 320 | 0 | 0.94 | 0.24 | 517 | 26 | 51 |
| repair-crossings | 1000 | (a) count, finest level only | 1000 | stal 500 / stal 80 / comp 420 | 0 | 0.65 | 0.14 | 496 | 16 | 27 |
| repair-crossings | 1000 | (b) excess, finest level only | 1000 | stal 500 / stal 80 / comp 420 | 0 | 0.65 | 0.14 | 496 | 16 | 27 |
| repair-crossings | 1000 | (a) count, finest only, best by excess | 1000 | stal 500 / stal 80 / comp 420 | 0 | 0.46 | 0.04 | 497 | 16 | 26 |
| repair-crossings | 1000 | (b) excess, finest only, best by excess = chosen | 1000 | stal 500 / stal 80 / comp 420 | 0 | 0.46 | 0.04 | 497 | 16 | 26 |
| repair-crossings | 3000 | baseline (mean, max) | 780 | stal 500 / stal 80 / stal 200 | 0 | 1.08 | 0.20 | 548 | 45 | 84 |
| repair-crossings | 3000 | (a) count above max_tol, all levels | 2320 | stal 840 / stal 580 / stal 900 | 10 | 0.69 | 0.32 | 48 | 12 | 20 |
| repair-crossings | 3000 | (b) excess, all levels | 1760 | stal 500 / stal 360 / stal 900 | 2 | 0.17 | 0.02 | 69 | 6 | 15 |
| repair-crossings | 3000 | (c) median of lagging, all levels | 920 | stal 500 / stal 100 / stal 320 | 0 | 0.94 | 0.24 | 517 | 26 | 51 |
| repair-crossings | 3000 | (a) count, finest level only | 2422 | stal 500 / stal 80 / conv 1842 | 1 | 0.32 | 0.18 | 10 | 0 | 2 |
| repair-crossings | 3000 | (b) excess, finest level only | 2422 | stal 500 / stal 80 / conv 1842 | 1 | 0.32 | 0.18 | 10 | 0 | 2 |
| repair-crossings | 3000 | (a) count, finest only, best by excess | 2422 | stal 500 / stal 80 / conv 1842 | 1 | 0.32 | 0.18 | 10 | 0 | 2 |
| repair-crossings | 3000 | (b) excess, finest only, best by excess = chosen | 2422 | stal 500 / stal 80 / conv 1842 | 1 | 0.32 | 0.18 | 10 | 0 | 2 |
| check | 1000 | baseline (mean, max) | 820 | stal 540 / stal 110 / stal 170 | 57 | 1.37 | 0.25 | 523 | 60 | 86 |
| check | 1000 | (a) count above max_tol, all levels | 1000 | comp 1000 | 15 | 14.46 | 1.22 | 865 | 763 | 1023 |
| check | 1000 | (b) excess, all levels | 1000 | stal 580 / comp 420 | 38 | 5.38 | 0.72 | 628 | 298 | 485 |
| check | 1000 | (c) median of lagging, all levels | 940 | stal 540 / stal 230 / stal 170 | 57 | 1.37 | 0.25 | 523 | 60 | 86 |
| check | 1000 | (a) count, finest level only | 820 | stal 540 / stal 110 / stal 170 | 57 | 1.37 | 0.25 | 523 | 60 | 86 |
| check | 1000 | (b) excess, finest level only | 1000 | stal 540 / stal 110 / comp 350 | 57 | 1.37 | 0.25 | 523 | 60 | 86 |
| check | 1000 | (a) count, finest only, best by excess | 820 | stal 540 / stal 110 / stal 170 | 60 | 1.01 | 0.03 | 544 | 58 | 80 |
| check | 1000 | (b) excess, finest only, best by excess = chosen | 1000 | stal 540 / stal 110 / comp 350 | 64 | 0.56 | 0.00 | 557 | 32 | 61 |
| check | 3000 | baseline (mean, max) | 820 | stal 540 / stal 110 / stal 170 | 57 | 1.37 | 0.25 | 523 | 60 | 86 |
| check | 3000 | (a) count above max_tol, all levels | 1700 | stal 1160 / stal 370 / stal 170 | 57 | 1.37 | 0.25 | 523 | 60 | 86 |
| check | 3000 | (b) excess, all levels | 1740 | stal 580 / stal 630 / stal 530 | 71 | 0.40 | 0.00 | 519 | 17 | 37 |
| check | 3000 | (c) median of lagging, all levels | 940 | stal 540 / stal 230 / stal 170 | 57 | 1.37 | 0.25 | 523 | 60 | 86 |
| check | 3000 | (a) count, finest level only | 820 | stal 540 / stal 110 / stal 170 | 57 | 1.37 | 0.25 | 523 | 60 | 86 |
| check | 3000 | (b) excess, finest level only | 1180 | stal 540 / stal 110 / stal 530 | 71 | 0.40 | 0.00 | 519 | 17 | 37 |
| check | 3000 | (a) count, finest only, best by excess | 820 | stal 540 / stal 110 / stal 170 | 60 | 1.01 | 0.03 | 544 | 58 | 80 |
| check | 3000 | (b) excess, finest only, best by excess = chosen | 1180 | stal 540 / stal 110 / stal 530 | 70 | 0.42 | 0.00 | 528 | 18 | 44 |

The shipped design (excess, finest level only, best by excess), `final.py`, with the old rule (stall_lagging False) beside it:

| validity | budget | stall_lagging | iterations | levels | invalid | mean % | above 10 % | returned vs final iterate above 10 % (finest) |
|---|---|---|---|---|---|---|---|---|
| repair-crossings | 500 | False / True | 500 / 500 | one level, budget used by the coarse level | 0 / 0 | 14.09 / 14.09 | 744 / 744 | |
| repair-crossings | 1000 | False | 780 | stal 500 / stal 80 / stal 200 | 0 | 1.08 | 45 | 46 / 46 |
| repair-crossings | 1000 | True | 1000 | stal 500 / stal 80 / comp 420 | 0 | 0.46 | 16 | 17 / 18 |
| repair-crossings | 3000 | True | 2422 | stal 500 / stal 80 / conv 1842 | 1 | 0.32 | 0 | 0 / 0 |
| check | 1000 | False | 820 | stal 540 / stal 110 / stal 170 | 57 | 1.37 | 60 | 74 / 71 |
| check | 1000 | True | 1000 | stal 540 / stal 110 / comp 350 | 64 | 0.56 | 32 | 45 / 45 |
| check | 3000 | True | 1180 | stal 540 / stal 110 / stal 530 | 70 | 0.42 | 18 | 29 / 27 |

## Districts, states, scenes

- Districts and states (ladder, n_iter 500) end `CONVERGED` after 135 and 65 iterations with and without the component, with identical errors.
- Strip scenes (6 seeds, check and repair-crossings, 12 pairs): status and iterations are identical in all 12 pairs (the scenes mostly run to `n_iter`; seed 19 converges). The best iterate by excess has the lower mean error in 10 of 12 pairs (seed 7: 6.06 to 1.66 %) and a higher max in 9 (seed 31: 3712 to 4052 %), and one pair (seed 11, repair-crossings) returns 1 invalid polygon where the baseline returns 0. These scenes are chaotic by construction (two regions with 0.3 % of the target).

## The three measures over the iterations (finest county level)

- **Mean ratio:** below 1 (satisfied) from the first iterations, and it swings within every 10-iteration cycle (the field is recomputed once per cycle), between about 0.01 and 0.15. A satisfied component does not count as progress.
- **Max ratio:** about 20 at the old stall (iteration 200) and still 20 at iteration 400, then it falls steadily to 2 by iteration 1,400 and to 1 at 1,842. The old rule stops while this fall has not yet started to show in a cycle minimum by the required fraction.
- **Lagging error:** 10 at iteration 200, falling smoothly to 0.7 at 1,400 and to 0 at 1,842, without the swings of the mean. The step at about 1,420 is a group of regions entering the tolerance.
- The old rule's stall point (200) lies on the part of the curves where both the max ratio and the lagging error are still 10 to 20 times above their values at the end of the run.

## Reading

- The component must not be on at the coarse levels: with the budget shared by the ladder (`n_iter` is the total), the coarse level 512 keeps improving its unresolvable sub-cell regions and uses 840 to 1000 of the 1000 iterations in four of the "all levels" runs (mean error 1.8 to 14.5 % against 1.08 %).
- Count and excess give the same finest-level runs in repair-crossings; in check mode (invalid polygons that grow) the count never counts progress and the excess does. The excess is smooth where the count has thresholds and noise at them, needs no parameter, and is also the measure that chooses the best iterate, so one measure serves both.
- The best iterate must follow the same measure: with the old score the returned iterate can be an earlier one with many more regions above tolerance (check mode, budget 1000: mean 1.37 % returned although the run continued for 350 iterations; by excess 0.56 %).
- The median (c) does not help: it stalls like the baseline in check mode and gives 0.94 % at repair-crossings, since regions entering or leaving the lagging set move it.
- Runs that stagnate still stall (counties with validity="check" and the count, 170 iterations; the "finest level only" runs of the old rule), and no run exceeds the budget. The cost is iterations up to the budget: 780 to 1000 at a budget of 1000, 2422 at 3000 (about 5 times the time of the stalled ladder).
- Remaining defect: longer runs with `"repair-crossings"` can end with a few invalid polygons (1 at 3000 iterations on counties; 6 to 10 in the all-level runs).
