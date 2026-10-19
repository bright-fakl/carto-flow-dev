---
issue: 167
title: Piecewise-affine windows on a quadtree mesh with vertex insertion (after Miaji et al.)
description: Prototype of the line densification of Miaji et al. inside the flow loop. At every field recompute a graded quadtree is built from the density, its leaves are triangulated, vertices are inserted where the boundaries cross triangle edges, and the vertices move with the piecewise-affine map of the advected mesh nodes for the next 10 iterations. Without pruning the 3,108 counties end with 0 invalid polygons (57 in the baseline) but with 7 to 11 times the vertices and a worse area error; with a simple pruning the vertex count is +40 % but 41 to 91 polygons are invalid again, because the pruning itself creates invalid polygons.
kind: exploration
topic: flow
status: open
related: exploration-carried-points, exploration-adaptive-densification, segment-density-warning
date: 2026-10-18 18:00
before: main @ 06d4ff0
after: scratch worktree with a hook in algorithm.py (algorithm_hooks.patch); not a PR
inputs: 3,108 counties (population) at max_segment_length 1000, ladder with min_resolution and levels auto, n_iter 1000, area_scale 1e-6, single run per row (the dynamics are chaotic: rows differ by more than their settings suggest).
---

## What was built

`pw.py` builds the mesh, `pw2.py` is the hook, `pw2run.py` runs the ladder, `algorithm_hooks.patch` adds the three call sites to `algorithm.py`.

1. At every recompute the density is padded to a power-of-two square and a quadtree is built by splitting the leaf with the largest density range until `n_cells * 2^-x` leaves exist, then graded (neighboring leaves differ by at most one level, as in the paper).
2. Every leaf is split into a fan of triangles from its center to its corner and hanging nodes. The paper uses a constrained Delaunay triangulation; the fan is simpler and has the same property that matters here, that the map is continuous across leaves. The center is the mean of the four corners, not advected.
3. Optional insertion: every boundary segment is split where it crosses a leaf edge or a fan edge, with identical points on the two sides of a shared boundary (computed from the lexicographically ordered end points).
4. The nodes are advected with the velocity field each iteration, and the vertices are placed with their (fixed) barycentric coordinates in their triangle. After 10 iterations the field is recomputed and the mesh is rebuilt.
5. The best-iterate restore needs the vertex set of the best iterate: the insertions and removals are recorded as `(a, b, t)` maps (a new vertex lies at fraction `t` between old vertices `a` and `b`) and the restored coordinates are lifted through them. The same maps would backfill the vertices into earlier frames of an animation.

## Results

Baseline (no hook): 25 s, 820 iterations, mean error 1.52 %, median 0.25 %, 57 invalid, 0.77 M vertices.

| mesh leaves (cells x) | insertion | pruning | time | vertices | mean / median error | invalid |
|---|---|---|---|---|---|---|
| 2^-8 | no | | 34 s | 0.77 M | 4.24 % / 1.06 % | 183 |
| 2^-6 | no | | 36 s | 0.77 M | 1.97 % / 0.04 % | 206 |
| 2^-4 | no | | 28 s | 0.77 M | 2.25 % / 0.28 % (center advected) | 135 |
| 2^-4 | no, center = mean of corners | | 40 s | 0.77 M | 1.29 % / 0.26 % | 71 |
| 2^-8 | yes | none | 93 s | 5.2 M | 6.9 % / 2.4 % | 0 |
| 2^-6 | yes | none | 269 s | 8.6 M | 5.7 % / 0.67 % | 0 |
| 2^-6 | yes | 0.02 cell | 99 s | 1.08 M | 1.72 % / 0.11 % | 91 |
| 2^-6 | yes | 0.002 cell | 79 s | 1.10 M | 3.59 % / 0.05 % | 76 |
| 2^-6 | yes | 0.0002 cell | 86 s | 1.18 M | 4.41 % / 0.65 % | 41 |

(The 2^-4 run with insertion and no pruning did not finish: it ran out of memory.)

- The mesh alone (no insertion) does not help: 71 to 206 invalid polygons. The guarantee needs every sub-segment inside one triangle, so the inserted vertices are the essential part.
- With insertion and no pruning no invalid polygon appears in two runs, and no mesh triangle was inverted in any of the sampled windows. The vertex count is the problem: the points inserted in one window are not removed, and the next window inserts new ones.
- The pruning removes an inserted vertex when it lies within a tolerance of the chord of its neighbors. `pw2run.py ... dbg` counts the invalid polygons before and after each pruning: most of the increase comes from the pruning step itself (for example 6 to 10, 52 to 61), a minority from the flow window. A tolerance of 1 m (0.0002 cell) still gives invalid polygons, so the squeezed strips are narrower than that at some iteration, or the chord removed lies across a nearby boundary.
- The area error is worse than the baseline in most rows because the piecewise-affine window is a coarser approximation of the flow than the per-vertex bilinear advection, and the runs are chaotic (the same settings other than the tolerance move the mean from 1.7 % to 4.4 %). I did not average over several runs.
- Time: the hook costs 45 to 65 s of the 80 to 100 s (mesh construction, vertex insertion, rebuilding the geometry metadata), mostly in unoptimized Python and numba code; the baseline iteration cost is unchanged.

## Coarse input (the paper caps the geometry at about 15 vertices per region)

The paper simplifies the geometry after every iteration to `max(10,000, 15 * regions)` vertices. The bundled counties have 194 k vertices; `simplify_coverage(tolerance=4000)` (a distance in meters) leaves 43 k, 14 per county, with the shared boundaries kept. `pw2run.py <bits> <ins|noins> coarse <tol>` runs it.

| mesh leaves | insertion | pruning | time | vertices | mean / median error | invalid |
|---|---|---|---|---|---|---|
| none (baseline) | no | | 14 s | 43 k | 18.2 % / 1.23 % | 327 |
| 2^-8 | yes | none | 78 s | 4.2 M | 6.35 % / 1.74 % | 0 |
| 2^-6 | yes | none | 192 s | 10.8 M | 1.44 % / 0.243 % | 0 |
| 2^-6 | yes | 0.02 cell | 75 s | 0.32 M | 25.5 % / 3.8 % | 432 |
| 2^-6 | yes | 0.002 cell | 87 s | 0.36 M | 12.8 % / 1.19 % | 508 |

- The flow alone cannot use the coarse input (segments of several cells, 327 invalid polygons and 18 % mean error), as expected.
- With the mesh and insertion at 2^-6 the same input gives 0 invalid polygons and an error (1.44 % mean, 0.243 % median) equal to the 1 km densified baseline (1.52 %, 0.250 %), from 43 k instead of 0.77 M input vertices. This is the property the paper claims, reproduced.
- The vertex count again grows to millions, because nothing is removed.
- My pruning is unusable here: dropping an inserted vertex puts the next insertion on a straight chord instead of on the bent image of the segment, and the errors compound (432 and 508 invalid polygons). A pruning has to keep the vertices where the image bends, and the criterion that decides which are safe to drop is the unsolved part.

## Coverage simplification at every window (coarse input)

At each window start, before the insertion, `shapely.coverage_simplify` (shared boundaries simplified once, topology kept) runs on the current geometry, with a tolerance given in cells of the current grid (`COV=<cells> pw2run.py 6 ins coarse 0`). The kept vertices are matched to the old ones by coordinates (the simplifier rotates the ring start), so the lift maps stay valid. The restore of the best iterate now stores that iterate's ring structure, instead of lifting its coordinates through later events: the lifted best iterate was itself simplified by later windows, and gave 16 invalid polygons at the first level change.

| tolerance | time | vertices | mean / median / p95 / p99 error | invalid |
|---|---|---|---|---|
| 0.02 cell | 94 s | 552 k | 1.34 % / 0.074 % / 4.0 % / 25 % | 0 |
| 0.05 cell | 72 s | 442 k | 4.41 % / 0.119 % / 19.5 % / 78 % | 0 |
| 0.1 cell | 76 s | 204 k | 4.23 % / 0.492 % / 17.3 % / 66 % | 0 |
| 0.2 cell | 71 s | 175 k | 4.85 % / 0.185 % / | 0 |
| (densified 1 km baseline, no hook) | 25 s | 0.77 M | 1.52 % / 0.250 % / | 57 |

- All simplified runs end with 0 invalid polygons from the 43 k-vertex input, with 175 k to 552 k vertices at the end (4 to 13 times the input, 0.2 to 0.7 times the 1 km input), against 10.8 M without simplification.
- The 0.02 cell run matches the baseline accuracy (median 0.074 %). The 0.05 to 0.2 cell runs have the same or lower median but 4 % mean and heavy tails (p95 17 to 20 %): they end earlier or on a worse iterate. These are single runs of a chaotic process, so I cannot tell a tolerance effect from run-to-run variation; the five rows should be repeated.
- The time is 3 to 4 times the baseline, mostly in the hook (mesh, insertion, simplification, rebuilding the geometry metadata), none of it optimized.
- The correspondence with the input vertices is lost: the simplifier removes original vertices too, and the animation frames before a removal cannot be reconstructed from the lift maps.

## Reading

The guarantee of the paper is reproduced in this setting: with the mesh and the insertion, the output has no invalid polygons, also for the squeezed strips that remain at 10 invalid polygons with 0.125 km carried points (exploration-carried-points). The open problem is what the paper solves with a topology-preserving simplification: keeping the vertex count bounded without creating the invalid polygons again. A simplification that is safe needs a check against nearby boundaries (an intersection test of the new chord against a spatial index of the segments), which I did not try. The area error and the run time are also not competitive yet.
