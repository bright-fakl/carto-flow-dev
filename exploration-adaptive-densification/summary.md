---
issue: 167, 174
title: What the remaining invalid output polygons are, and adaptive densification
description: After the grid and stall fixes and input densified to 1 km, 57 of the 3,108 county polygons are still invalid. The first invalid polygons were Virginia counties next to enlarging independent cities (stretched segments); at 0.25 km the remaining ones are Great Plains counties that shrink 10 to 100 times into needles narrower than a cell, where chords between vertices 3 to 4 km apart cross across the width. Densifying by a pilot run (stretch and local width) reaches the quality of uniform 1 km densification with 40 to 90 % of its vertices but does not reach zero invalid polygons.
kind: exploration
topic: flow
status: superseded
related: segment-density-warning, exploration-county-hierarchical-prototype
date: 2026-10-19 21:00
before: main @ 08f3edf
after: the same checkout; scripts only, no library change
inputs: 3,108 bundled counties (population), ladder with grid auto, n_iter 1000, square grid margin 0.5, NUMBA_NUM_THREADS=8. Pilot: the same ladder on the 5 km bundled geometry, per-segment length at the end of every level.
closed: 2026-10-26 02:02
---

**Outcome (2026-10-26).** Superseded by the validity methods `validity="repair-crossings"` and `validity="repair-quadtree"` (PR 180 and PR 181, merged); the vertex-density warning and the `max_segment_length` option of the loaders remain the way to prepare coarse input.


## What the invalid polygons are

`inv_final.py` takes the 57 invalid polygons of the ladder on the counties densified to 1 km and, for each, the longest segment and the segment at the crossing, in cells of the finest grid (4.26 km).

- They are not sub-cell regions (median target 13 cells; 2 % below one cell) and not enlarging regions: the median area against the original is 0.08, so most regions shrink strongly.
- The first ones in the list are Virginia counties around independent cities that enlarge 10 to 30 times (Rockbridge, Rockingham, Harrisonburg, Staunton): segments up to 5 cells long at the crossing. That is the stretch of the previous page.
- With adaptive densification of the stretched segments (below) these disappear, and what remains at 0.25 km (39 invalid polygons, `inv2.py`) are counties of NE, SD, CO, ND, MT and KS that shrink 10 to 100 times (median area against the original 0.04, 1 to 10 cells in the target). The crossing segments are neighbors or second neighbors in the ring (22 of 39 within two positions, all within five), not degenerate in the input (separation of the two segments 198 m to 37 km, median 1.35 km), and the steps are small (0.01 to 0.03 cells per iteration).
- `when.py` and `when2.py` follow the polygons over the iterations: invalid polygons appear at 1024 and 2048 cells and some appear, heal and reappear (Rock County, Minnesota at iterations 41, 61, 76 and 96). `when2.py` shows Washington County, Colorado at its first invalid iteration (iteration 32 of the 1024 level): a needle about 15 km long and 0.5 to 2 km wide, in cells of 8.5 km, with vertices 3 to 4 km apart on each side.

## Reading

The crossings are the same kind as before, chords between vertices that are too sparse, but the relevant length is the local width of the squeezed polygon rather than the stretch. A step cannot fold a polygon (a bilinear field with a step of 0.2 cells moves two points at distance `w` by at most `0.4 w` relative to each other), but the straight chord between two vertices is not the image of the straight segment: its distance to the opposite side differs from the true one by the sagitta of the flow, of the order of the vertex spacing squared times the curvature of the displacement. When a region is squeezed into a strip narrower than that, chords of the two sides cross. Densifying uniformly lowers the sagitta (301, 73, 57 and 38 invalid polygons at 5, 2, 1 and 0.5 km on a ladder from 512) but cannot reach zero because a squeezed strip can become arbitrarily narrow.

## Adaptive densification from a pilot run

`adapt.py`, `adapt2.py` and `adapt3.py` run the ladder once on the bundled geometry, record the length of every segment at the end of every level (and for the width criterion the distance of every vertex to the nearest vertex more than three positions away in its ring), subdivide each input segment so that its longest recorded length is at most `c` cells (stretch) and at most `alpha` times the local width (width), identically for the two polygons that share it, and run the ladder again. Vertices are added in the input, so the animation correspondence is kept.

| input geometry | vertices | mean / median / 95th percentile error | invalid polygons | time |
|---|---|---|---|---|
| bundled, 5 km | 193,856 | 3.40 / 0.15 / 14.0 % | 301 | 11.5 s |
| uniform 2 km | 451,364 | 3.40 / 0.24 / 12.9 % | 73 | 12.4 s |
| uniform 1 km | 768,580 | 1.52 / 0.25 / 2.7 % | 57 | 19.4 s |
| uniform 0.5 km | 1,453,552 | 1.54 / 0.11 / 6.2 % | 38 | 28.6 s |
| pilot, stretch c = 1 (final lengths only) | 306,086 | 3.31 / 0.15 / 14.7 % | 67 | 11.2 s |
| pilot, stretch c = 1 (longest over the levels) | 309,549 | 1.40 / 0.31 / 2.9 % | 130 | 10.1 s |
| pilot, stretch c = 0.5 | 499,415 | 1.31 / 0.21 / 4.0 % | 64 | 19.2 s |
| pilot, stretch c = 0.25 | 892,497 | 1.47 / 0.09 / 6.2 % | 39 | 24.6 s |
| pilot, stretch c = 0.5, second round | 571,312 | 1.01 / 0.18 / 3.2 % | 80 | 20.8 s |
| pilot, stretch c = 1 and width alpha = 1 | 457,233 | 3.34 / 0.18 / 14.9 % | 34 | 11.7 s |
| pilot, stretch c = 1 and width alpha = 0.5 | 712,072 | 3.33 / 0.17 / 14.9 % | 14 | 12.5 s |
| pilot, stretch c = 0.5 and width alpha = 0.5 | 806,668 | 1.81 / 0.03 / 7.0 % | 62 | 20.1 s |

- The stretch criterion from the longest length over the levels reaches the error of uniform 1 km densification (1.3 to 1.4 % mean) with 310,000 to 500,000 vertices instead of 770,000, but the invalid polygons (64 to 130) stay at the level of uniform 1 km.
- Adding the width criterion lowers the invalid polygons to 14 to 34, with 460,000 to 710,000 vertices, and does not reach zero.
- The error and the invalid polygons vary from run to run by more than the differences between neighboring settings (the ladder is sensitive: a change of vertices changes the flow), so single runs of this table are indications, not a ranking.

## Literature

Miaji, Singhania, Goh, Le, Tharatipyakul and Gastner, "Topology-Preserving Line Densification for Creating Contiguous Cartograms" ([arXiv 2511.08121](https://arxiv.org/abs/2511.08121)), address the same problem for the flow-based method of Gastner, Seguy and More (2018). They insert points in the original space at the intersections of polygon edges with the edges of a constrained Delaunay triangulation whose corners come from a quadtree refined where the density contrast is highest (about 200 to 17,000 leaves, graded so that neighbors differ by one level). The projection of a point is the piecewise affine map of its triangle, which is continuous across triangle edges, so neighboring polygons stay connected and non-overlapping. A topology-preserving simplification caps the number of vertices at 15 times the number of polygons or 10,000. On 32 maps their method (5FCarto) had no intersections and raised the vertex count by 62 % on average (median 20 %); uniform insertion at regular spacing (ggplot2 `coord_munch()`) raised it by 431 % (median 201 %) and still left intersections on 13 maps. For the US counties they report 2.2 s and no overlaps for 5FCarto against 195 and 323 for two flow-based baselines without it. The method works after the projection is known (the density-equalizing map is computed once on the grid) and replaces the polygon vertices by a piecewise affine image, so it differs from our iteration, which advects the vertices step by step and rasterizes the density from them.

## Options

- Leave as is: 2 % invalid polygons at the finest level, `repair=True` for static maps (adds vertices), uniform densification to 1 km documented and recommended by the warning.
- A pilot-based adaptive densification utility (`densify_adaptive(gdf, values, ...)` or an option of the loaders): about half of the vertices of uniform 1 km at the same error, no guarantee of validity.
- A topology-preserving final step after the run in the manner of the paper: carry the subdivision points of the polygon edges through the recorded displacements (the morph already carries `coords` with the flow) and rebuild the polygons from them, which makes the output faithful without changing the morph. The subdivision points can be added to the input geometry with the same correspondence, so animations are unaffected.
