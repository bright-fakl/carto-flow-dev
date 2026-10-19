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

## Reading

The guarantee of the paper is reproduced in this setting: with the mesh and the insertion, the output has no invalid polygons, also for the squeezed strips that remain at 10 invalid polygons with 0.125 km carried points (exploration-carried-points). The open problem is what the paper solves with a topology-preserving simplification: keeping the vertex count bounded without creating the invalid polygons again. A simplification that is safe needs a check against nearby boundaries (an intersection test of the new chord against a spatial index of the segments), which I did not try. The area error and the run time are also not competitive yet.
