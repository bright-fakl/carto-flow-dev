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

## Reading

The concern was justified: the invalid regions do disturb the field of their neighbors, and repairing them for the density removes most of that disturbance. Treating them separately in the progress statistics is not helpful as implemented. What remains is the invalid polygons themselves (83 at the end) and the lagging strongly shrunk counties.
