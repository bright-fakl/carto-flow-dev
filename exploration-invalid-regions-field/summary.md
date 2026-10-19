---
issue: 171
title: Treating invalid regions separately in the flow loop (prototype)
description: Rasterizing a repaired polygon (shapely.make_valid) instead of the invalid ring when the density field is built lowers the median error of the valid counties from 0.25 % to 0.012 % and their p95 from 2.4 % to 1.3 %, and the median error of the valid neighbors of invalid regions from 0.86 % to 0.12 %. The number of invalid polygons rises from 57 to 83 and the number of counties above 10 % is unchanged. Excluding the invalid regions from the error statistics or measuring them by their point-set area makes the result worse.
kind: exploration
topic: flow
status: open
related: exploration-stall-lagging-regions, exploration-quadtree-windows, exploration-county-error-relation
date: 2026-10-19 20:00
before: main @ 06d4ff0
after: scratch worktree with hooks in algorithm.py (algorithm_hooks.patch); not a PR
inputs: 3,108 bundled counties (population) with max_segment_length 1000, auto ladder, n_iter 1000, area_scale 1e-6, default options. Errors are of the valid output polygons against targets normalized on the valid polygons only; neighbors are valid regions that intersect an invalid one. Runs are deterministic (repeating a run gives identical numbers).
---

## Why

An invalid (self-intersecting) polygon is rasterized with its winding-weighted coverage: a cell inside an overlap of the ring gets the density twice, a cell inside a reversed lobe gets a negative density, and the density of the region is its value over the signed shoelace area. The field around an invalid region is therefore wrong, and so is the velocity that moves its neighbors. Valid regions that touch an invalid one end at 3 to 10 times the median error of other valid regions of the same shrink class (`nbr.py`; exploration-stall-lagging-regions).

## Prototype

Hooks in `algorithm.py` (`algorithm_hooks.patch`, `INV_HOOK`), class `InvHook` in `inv.py`, driver `invrun.py <mode> <n_iter>`:

- `repair`: at every recompute (every 10 iterations) the polygons are checked with `shapely.is_valid` (0.04 s for 3,108 polygons with 0.77 M vertices) and each invalid one is replaced for the density field by the polygonal part of `shapely.make_valid` (0.32 s for 100 polygons). The vertices of the morph geometry are not changed.
- `exclude`: the area of an invalid region is set to its target in the error metrics (mean, max, stall rule, best-iterate score), so it does not count.
- `both`: the two together.
- `pointset`: the error metric uses the `make_valid` area of the invalid regions.

## Results

| mode | levels (iterations, S = stalled) | time | invalid | valid: mean / median / p95 | valid above 10 % | neighbors of invalid: median, above 5 % |
|---|---|---|---|---|---|---|
| none | 540 S, 110 S, 170 S | 21 s | 57 | 1.37 % / 0.252 % / 2.4 % | 60 | 0.86 %, 21 of 190 |
| repair | 540 S, 90 S, 150 S | 24 s | 83 | 0.94 % / 0.012 % / 1.3 % | 59 | 0.12 %, 44 of 252 |
| exclude | 640 S, 70 S, 90 S | 24 s | 53 | 2.14 % / 0.147 % / 6.0 % | 105 | 0.89 %, 34 of 177 |
| both | 690 S, 70 S, 90 S | 27 s | 66 | 1.62 % / 0.106 % / 5.4 % | 77 | 0.78 %, 38 of 208 |
| pointset | 630 S, 70 S, 90 S | 25 s | 66 | 1.62 % / 0.106 % / 5.4 % | 77 | 0.78 %, 38 of 208 |

(The `pointset` row is identical to `both` in every statistic; I have not checked whether that is a coincidence or a defect of the hook.)

- Repairing the polygons for the density field is the effective part. The valid regions get a 20 times lower median error and a lower tail, and the neighbors of invalid regions improve 7 times at the median; the cost is 3 s.
- It does not reduce the number of counties above 10 % (59 against 60), and the number of invalid polygons rises from 57 to 83, so the invalid regions are not repaired and more of them appear: those polygons no longer disturb the field, and nothing moves them back to validity.
- Excluding the invalid regions from the metrics is worse than doing nothing: the finest level stalls after 90 iterations instead of 170 and the tail grows (p95 6 %, 105 counties above 10 %). I did not isolate why; the stall rule and the best iterate are chosen on a score that now ignores those regions.
- Every level ends stalled in all modes: the stall rule is unchanged by the repair.

## The analysis of the county errors, baseline against repair

`repair_plots.py <output dir>` runs the baseline and the density-field repair (n_iter 1000) and draws the same figures as exploration-county-error-relation, with the baseline on the left and the repair on the right. Errors are of valid polygons against targets normalized on the valid polygons; the invalid polygons are shown by their own signed-area error.

figure: fig1_error_vs_shrink.png — Absolute area error against the shrink factor, colored by target size, baseline and repair. The bulk of the counties moves down, many to the 0.01 % floor of the plot; the strongly shrunk small counties at the upper left do not move. The invalid polygons (red crosses) increase from 57 to 83 and appear at all shrink factors, some with errors of several hundred percent.
figure: fig2_error_vs_target.png — The same against the target size in grid cells, colored by shrink factor. The failures stay at targets below about 10 cells.
figure: fig3_share_over_10pct.png — Share of valid counties above 10 % by shrink and target size. The failing corner is unchanged (shrink below 0.1 and target below 16 cells); some cells are slightly worse (shrink 0.01 to 0.03 with a target of 1 to 4 cells: 23 % to 31 %; 4 to 16 cells: 3 % to 5 %), one better (shrink below 0.01, 4 to 16 cells: 18 % to 9 %).
figure: fig4_where.png — The two outputs, the valid counties above 10 % in red and the invalid polygons in black. The repair leaves the same strips and the Virginia cluster, with more and larger invalid polygons in the western strips and one new large invalid polygon in the west.
figure: fig5_past_stall.png — Continuation of the finest level past the stall for 1,500 iterations, baseline against repair. The lagging valid counties (above 10 % at the stall) fall faster with the repair (median error 0.23 % against 0.69 % at 1,500); the mean error of the valid counties is the same (0.118 %) from iteration 1,000; the number of invalid polygons grows to 205 with the repair against 100 without. (The median of the valid counties is at the 0.01 % floor of the plot in both.)

## Quadtree windows against the repair, same input and metric

`cmphook.py <mode> <n_iter>`: 1 km input, auto ladder, valid polygons, targets on valid polygons. The hook is the quadtree-window hook with coverage simplification at 0.02 cell (exploration-quadtree-windows), leaves 2^-6.

| run | time | vertices at the end | invalid | valid: mean / median / p95 | valid above 10 % |
|---|---|---|---|---|---|
| baseline, n_iter 1000 | 21 s | 0.77 M | 57 | 1.37 % / 0.252 % / 2.4 % | 60 |
| density repair, n_iter 1000 | 25 s | 0.77 M | 83 | 0.94 % / 0.012 % / 1.3 % | 59 |
| density repair + 1,500 iterations past the stall | | | 205 | 0.118 % | 6 |
| quadtree windows, n_iter 1000 (levels 720 S, 210 S, 70 budget) | 93 s | 0.60 M | 0 | 1.64 % / 0.110 % / 5.9 % | 80 |
| quadtree windows, n_iter 3000 (finest level 2,070 iterations, budget) | 432 s | 0.57 M | 0 | 0.194 % / 0.127 % / 0.68 % | 1 |

- The bulk accuracy gain (median) comes from the repair of the density field, not from the mesh: the repair reaches a median of 0.012 % in 25 s, the quadtree windows 0.11 to 0.13 % (the piecewise-affine window is a coarser flow map than the per-vertex advection).
- What the windows add is validity (0 invalid polygons in both runs) and, given the iterations, the lagging counties: 1 valid county above 10 % after 3,000 iterations, against 59 at the repair's stall and 6 after 1,500 more iterations of the repair, which then has 205 invalid polygons.
- The price is 20 times the run time at the same stall-free finest level, and the budget (the finest level used 2,070 iterations and ended at the cap, not at a stall).

## Reading

The concern was justified: the invalid regions do disturb the field of their neighbors, and repairing them for the density removes most of that disturbance. Treating them separately in the progress statistics is not helpful as implemented. What remains is the invalid polygons themselves (83 at the end) and the lagging strongly shrunk counties.
