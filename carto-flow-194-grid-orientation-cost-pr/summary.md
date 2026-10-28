---
pr: 196
title: "perf: vectorize the cost loops of the grid layout assignment"
description: The orientation cost, the neighbor penalty, the reverse neighbor penalty and the hop distances of assign_to_grid_hungarian run as array operations. The assignments of 9 grid cases equal those of main exactly; GridBasedLayout on the 432 districts with square or hexagon tiles takes 2 s instead of 126 to 137 s.
kind: pr
topic: symbol
project: carto-flow
url: https://github.com/bright-fakl/carto-flow/pull/196
issue: 194
branch: perf-grid-orientation-cost
base: main
date: 2026-10-28 14:30
before: main at f6b0a0c (step 3)
after: perf-grid-orientation-cost @ 295414f (2,072 passed, 2 skipped, 4 xfailed locally)
inputs: carto-flow f6b0a0c against 295414f; Python 3.10.18, bundled census data (49 states, 432 districts); 16-core WSL2 machine. Old and new ran one after the other, each case best of 3.
---

Fixes [#194](https://github.com/bright-fakl/carto-flow/issues/194). The change does not alter results, so the page has no figures; the evidence is the exact comparison of the assignments, the timings and the profile.

## What changed

All in `layouts/grid/_placement.py`, `assign_to_grid_hungarian`, refinement loop:

- Orientation cost: the loop over every pair (i, j) and every tile k with scalar `norm`, `arctan2` and angular error became a loop over j only. For each j, the rows i that have j as a neighbor are updated at once (`orientation_cost[rows, :] += (angle_err / pi) * w`). Per element the operations are the same as before and each row still accumulates its neighbors j in ascending order, so the sums are bit-identical. The same-cell test uses `sqrt(dx*dx + dy*dy) < 1e-12` instead of `np.linalg.norm`.
- Original angles (`orig_angles`, n x n): one `arctan2` over all pairs instead of a double Python loop; pairs that are not adjacent or share a source geometry are set to nan.
- Neighbor penalty: same loop over j, `neighbor_cost[rows, :] += penalty * w` for all rows at once (per element the same product and sum).
- Reverse neighbor penalty: counts of tile neighbors occupied by each region (`occupied`, n x m) times the matrix of non-adjacent region pairs. All entries are small integers in float64, so the matrix product is exact.
- `_bfs_distance_matrix` uses `scipy.sparse.csgraph.shortest_path` (unweighted); unreachable pairs keep the value m. It took 1.46 s of the 3.7 s that remained after the cost loops. The existing test for it passes unchanged.

## Identity

[identity_check.py](identity_check.py) (copy of the script of isotile-adoption-step-3-pr) with the sources of main on `PYTHONPATH` and with this branch; `assignments`, `source_indices` and the lattice size compared with `np.array_equal`. Cases: all 9 grid cases of the script (states: hexagon, square, triangle, quadrilateral, `scalloped_hexagon`, hexagon and square with a tile count column; districts: hexagon, square). The mosaic cases do not use this function. [identity_and_timing.txt](identity_and_timing.txt): all 9 identical, no tie had to be examined.

## Wall time

Best of 3 ([timing_old.txt](timing_old.txt), [timing_new.txt](timing_new.txt)); all old runs first, then all new runs.

| case | items | lattice tiles | identical | old (s) | new (s) | new / old |
|---|---|---|---|---|---|---|
| states grid hexagon | 49 | 149 | yes | 1.66 | 0.25 | 0.15 |
| states grid square | 49 | 160 | yes | 1.78 | 0.24 | 0.14 |
| states grid triangle | 49 | 168 | yes | 1.94 | 0.24 | 0.13 |
| states grid quadrilateral | 49 | 180 | yes | 0.77 | 0.23 | 0.30 |
| states grid scalloped_hexagon | 49 | 179 | yes | 1.95 | 0.26 | 0.14 |
| states grid hexagon tile_count | 154 | 427 | yes | 4.75 | 0.28 | 0.06 |
| states grid square tile_count | 154 | 468 | yes | 5.20 | 0.29 | 0.06 |
| districts grid hexagon | 432 | 1,159 | yes | 137.22 | 1.94 | 0.01 |
| districts grid square | 432 | 1,320 | yes | 125.70 | 2.07 | 0.02 |

## Profile (districts, square tiling)

[profile_districts.py](profile_districts.py); [profile_before.txt](profile_before.txt), [profile_after.txt](profile_after.txt).

| | before | after |
|---|---|---|
| total under cProfile | 182.9 s | 2.17 s |
| `assign_to_grid_hungarian` (cumulative) | 181.9 s | 1.11 s |
| scalar `np.linalg.norm` calls | 29.9 million, 77.5 s | none |
| `_bfs_distance_matrix` | about 1.5 s | 0.19 s |

What remains in `assign_to_grid_hungarian` (0.8 s of its own time) is the per-j loop (432 iterations per pass) and the n x n arrays; the 11 Hungarian solves take 0.09 s in total. The rest of the layout is shapely: `union_all` 0.32 s, 2,266 `intersection` calls 0.33 s. No Python loop dominates any more.

## Test

`tests/test_grid_placement_cost.py` (new): on random instances (30 regions with random weighted adjacency and source indices, 7 x 7 square grid, three seeds) the cost matrix passed to `linear_sum_assignment` in the first refinement pass is compared with `np.testing.assert_array_equal` to a reference that computes it with the former scalar loops (norm, arctan2, angular error per pair and tile, reverse penalty per tile and tile neighbor). Exact equality holds. Full suite: 2,072 passed, 2 skipped, 4 xfailed. `ruff check` and `ruff format` pass.
