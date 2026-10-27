---
issue: 167
title: Rebuilding the output polygons from carried subdivision points (option 3)
description: Subdivision points of the 1 km county boundaries are carried through the flow as extra coordinates and the polygons are rebuilt from them after the run. The morph is unchanged (same iterates, same area errors), and the invalid polygons drop from 57 to 29 (0.5 km points), 11 (0.25 km) and 10 (0.125 km) of 3,108, at 1.6, 2.7 and 4.3 times the run time. A floor of about 10 remains.
kind: exploration
topic: flow
status: superseded
related: exploration-adaptive-densification, segment-density-warning, census-max-segment-length
date: 2026-10-18 12:00
before: main @ 06d4ff0
after: the same checkout; script only, no library change
inputs: 3,108 bundled counties (population) densified to 1 km with load_us_census(max_segment_length=1000), CartogramWorkflow(coords=...).morph_multiresolution with min_resolution and levels auto, n_iter 1000, area_scale 1e-6. The carried points are densify_coverage(counties, s) for s in 500, 250 and 125 m (shared boundaries get identical points), all vertices carried including the original ones.
closed: 2026-10-26 02:02
---

**Outcome (2026-10-26).** Superseded by the validity methods `validity="repair-crossings"` and `validity="repair-quadtree"` (PR 180 and PR 181, merged): carrying subdivision points through the flow leaves invalid polygons and costs more per vertex than validated windows.


## Method

`opt3.py` densifies the input a second time with `densify_coverage` and passes every vertex of the densified geometries as `coords` to `CartogramWorkflow`. The morph itself runs on the 1 km geometry, so iterates, step sizes and stall detection are those of the baseline. After the run `shapely.set_coordinates` writes the displaced points back into the densified geometries, which have the same ring structure.

## Result

| carried points | points | run time | invalid polygons | mean / median area error |
|---|---|---|---|---|
| none (baseline) | 0.77 M | 22 s | 57 | 1.52 % / 0.250 % |
| 0.5 km | 1.53 M | 35 s | 29 | 1.56 % / 0.259 % |
| 0.25 km | 3.02 M | 60 s | 11 | 1.73 % / 0.259 % |
| 0.125 km | 5.78 M | 95 s | 10 | 1.61 % / 0.260 % |

- The morph output (error and invalid count of the 1 km polygons) is identical in all runs: carrying points does not change the flow.
- The rebuilt polygons have the same median error as the baseline. The mean moves by a few hundredths of a percent at 0.5 km and by 0.2 points at 0.25 km, which is the area change of the polygons that are still fixed up by the finer boundary.
- Run time grows linearly with the number of carried points: about 17 s per 1 M points on this machine, so the cost of 0.25 km points is 2.7 times the baseline, not 2.
- The invalid count levels off at 10 to 11: the remaining polygons are needles whose width is below even a 0.125 km spacing at some iteration, or true folds of the flow.

## Reading

Option 3 does what it should (the animation correspondence of the input is kept, and the output follows the true image of the boundary), and 0.25 km removes 80 % of the invalid polygons. It is not free: it triples the run time, and it does not reach zero.

## Possible reductions of the cost

- Carry only the new points. The original vertices are already in the morph geometry (this run carries them twice).
- Carry points only for the polygons that end invalid or thin in the baseline output and rebuild those, a second pass restricted to about 60 polygons instead of all 3,108. This would cost a small fraction of the baseline, but needs the morph to run twice, or a morph that starts carrying points when it detects a thin polygon.
- Skip the per-point area-scaling bookkeeping in `coords` (`coords_area_scaling`), which is needed only for the uniform view of the points.
