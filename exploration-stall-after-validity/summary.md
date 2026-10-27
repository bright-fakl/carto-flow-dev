---
issue: 177
title: Does the stall rule still lose progress now that validity="repair-crossings" exists?
description: With validity="repair-crossings" the county ladder has no invalid polygons and its mean error falls from 1.37 to 1.08 %, but every level still ends STALLED and 45 valid counties stay above 10 %. Continued for 1,000 iterations they fall to 8 (mean 1.0 to 0.68 %). The earlier gain (mean 1.3 to 0.11 %) came from the normalization on invalid polygons; the real gain of continuing is smaller, and the unresolved tail is sub-cell counties.
kind: exploration
topic: flow
status: led-to
related: exploration-stall-lagging-regions, exploration-county-error-relation, validated-windows-pr
date: 2026-10-26 17:00
before: main @ 4271a3b
after: the same checkout; scripts only, no library change
inputs: 3,108 bundled counties (population), max_segment_length 1000, auto ladder, n_iter 1000, area_scale 1e-6, grid 2048 for the continuation. Errors of valid polygons against targets normalized on the valid polygons. Single runs; NUMBA default threads.
---

**Outcome (2026-10-27).** Led to the issue 177 work: PR 185 (`area_tol_cells`, `n_unresolved`, stall warning with the continuation call) and PR 186 (`wait_for_lagging_regions`). Both merged.

`ladder_modes.py <dir>` runs the ladder per validity mode, `continue_valid.py <dir>` continues the finest level of the `"repair-crossings"` run with the stall rule off and snapshots every 20 iterations, `analyze.py` replays candidate progress measures on those snapshots, `fig.py` draws the figure.

figure: fig1_continue_valid.png — The finest county level continued for 1,000 iterations after its stall (validity="repair-crossings", no invalid polygons). Left: valid counties above 10 % and above 5 %. Middle: the maximum error. Right: mean and median error.

## 1. How the ladder ends per validity mode

| mode | time | levels (grid: status, iterations) | invalid | mean / median / p95 error | above 10 % | max error |
|---|---|---|---|---|---|---|
| "check" | 39 s | 512: stalled 540, 1024: stalled 110, 2048: stalled 170 | 57 | 1.37 / 0.25 / 2.44 % | 60 | 523 % |
| "repair-crossings" | 47 s | 512: stalled 500, 1024: stalled 80, 2048: stalled 200 | 0 | 1.08 / 0.20 / 2.63 % | 45 | 548 % |
| "repair-quadtree" | 36 s | 512: stalled 760, 1024: completed 240 | 0 | 5.34 / 0.24 / 27.99 % | 303 | 540 % |

The quadtree run ended at grid 1024 (the ladder has two levels with it); its numbers are at that grid and are not comparable with the other two.

## 2. Continuing the finest level (repair-crossings)

| iterations after the stall | mean | median | above 10 % | above 5 % | max |
|---|---|---|---|---|---|
| 0 | 1.01 % | 0.17 % | 45 | 77 | 549 % |
| 200 | 0.81 % | 0.22 % | 22 | 38 | 428 % |
| 500 | 0.69 % | 0.25 % | 9 | 20 | 175 % |
| 1000 | 0.68 % | 0.32 % | 8 | 13 | 50 % |

The continuation takes 109 s (the ladder took 47 s). Of the 45 counties above 10 % at the stall, 7 remain above it, their median falling from 14.9 % to 1.9 %. The 8 counties above 10 % at the end all shrink by more than 10 times in area. The median error of all counties rises from 0.17 to 0.32 % while the tail falls. The returned best iterate of this run (iteration 992) has a mean of 0.35 % and 113 counties above 1 %, the final iterate (1000) a mean of 0.68 % and 651 above 1 %; the error is not monotone in the iteration.

## 3. Candidate progress measures, replayed on the snapshots

The stall rule (patience 4 cycles, efficiency 0.05) applied to other measures of the 20-iteration snapshots (a cycle here is 20 iterations, the library's is 10, and `moved` is taken as 0.1 per iteration):

| measure | stalls after |
|---|---|
| max error | never within 1,000 iterations |
| count of valid counties above 10 % | 581 iterations |
| sum of log2(1 + error) over the counties above 10 % | never within 1,000 iterations |
| median error of the counties that were above 10 % at the start | never within 1,000 iterations |

## Reading

- The invalid polygons are no longer part of the problem when `validity="repair-crossings"` is used: the earlier gain from continuing (mean 1.3 to 0.11 %, 60 to 6 above 10 %) was measured with targets normalized on a set that contained invalid polygons and is not reproduced. With valid polygons the gain is mean 1.0 to 0.68 % and 45 to 8 counties above 10 %, for 2.3 times the ladder time.
- Two problems remain. (1) Every county ladder ends `STALLED` although the counties above tolerance keep improving; the three candidate measures that follow the lagging counties would continue for 581 to more than 1,000 iterations, which is 1 to 2 minutes on counties. (2) `CONVERGED` stays unreachable: the max is held by sub-cell counties (548 % at the stall, 50 % after 1,000 iterations).
- Replaying on snapshots gives the order of magnitude only; a change to the rule needs a run of the library.
