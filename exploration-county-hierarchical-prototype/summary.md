---
issue: 129
title: County flow cartograms: global morph, ladder, and hierarchical prototype
description: A resolution ladder from grid 256 to 2048 with the default options reaches a county mean error of 2.1 % (median 0.11 %) in 12 s; starts at 128 or 64 tangle the counties, and the dt schedule and the stall threshold change little. A single global morph of the 3,108 counties reaches a mean error of 1.0 % and a median of 0.01 % at grid 2048 (126 s) and 2.2 % / 0.13 % at grid 1024 (23 s) once the stall rule is off; with only stall_min_improvement lowered to 0.002 the default stack reaches 5.4 % mean at 1024 in 8 s. The earlier county failures were the stall rule ending slow progress after 50 iterations, not sub-cell regions alone. The hierarchical prototype (states first, then counties per state) fixes the county areas but leaves the state outlines free, so the states overlap by 11.6 %; it is not needed to get a county cartogram. A plain Arizona (15 counties) converges at every grid once the stall rule is off.
kind: exploration
topic: flow
status: led-to
related: exploration-hierarchical-morph, exploration-multires-start, exploration-counties-subcell
date: 2026-10-18 21:00
before: main @ cf7d1bb
after: the same checkout; prototype scripts only, no library change
inputs: 3,108 contiguous counties from cb_2020_us_county_500k with the 2020 Census population estimate (co-est2020-alldata.csv), ESRI:102008, coverage-simplified at 1000 m with 5 km segments. The vote set of the earlier explorations is not available, so the numbers are not comparable one to one. MorphOptions grid_margin 0.5, square, area_scale 1e-6, n_iter 500; NUMBA_NUM_THREADS=8. Error is the output area against the population share of the total output area.
closed: 2026-10-27 15:00
---

`prep_counties.py` builds the set, `hier129.py` runs the three stages (member grid, state grid and polish grid as arguments), `hier_ladder.py` runs stage 2 as a ladder, `probe_az*.py` are the Arizona probes. Logs are in `data/`.

## Summary

- A county flow cartogram works with the existing code and no new algorithm: a resolution ladder from grid 256 to 2048 with default options gives a mean county error of 2.1 % (median 0.11 %) in 12 s. A single grid 2048 with the stall rule off gives 1.0 % (median 0.01 %) in 126 s.
- The earlier county failures came from the ladder starting at 128 or 64, where 89 % and 97 % of the counties are below one cell and the coarse level tangles them. The start at 512 (the "2.5 cells" auto rule) is also worse than 256.
- On a single grid at 512 or finer, the stall rule ends the run early: the step is `dt` grid cells, so progress per iteration shrinks with the grid (Arizona alone: 119, 208, 384 and 758 iterations to converge at grids 128 to 1024, but stalled at 50 above 256). In the ladder the stall threshold and the dt schedule change little.
- About 130 to 700 output polygons are invalid (self-intersections), mostly counties that are within 5 % of their target. `Cartogram.get_geometry(repair=True)` and `to_geodataframe(repair=True)` (#85) already repair them as an opt-in; the repair adds vertices, so it must not be used on geometries that are animated.
- The hierarchical idea (states first, then counties on state-fitted grids) fixes the county areas but leaves the state outlines free, so states overlap by 11.6 %. It is not needed for a county cartogram.

## Remaining next steps

- Other county data. Rerun with a second value set (votes or another census variable) so the numbers compare with the earlier reports and with other value distributions, and add counties to the benchmarks (#113, open).

## Outcome (2026-10-27)

The ladder works for counties and the hierarchical idea is not needed. The follow-ups merged: the stall rule scales with the grid (PR #171, issue #166), a gallery example of a county flow cartogram (PR #172), a warning when the input segments are too long for the expected stretch of their regions (PR #173, issue #167), and the validity options `repair-crossings` (PR #180) and `repair-quadtree` (PR #181) that keep the output polygons valid. Issue #129 was closed as not planned on 2026-10-26. Issue #113 stays open, for the benchmarks only. The other next steps written on 2026-10-18 (ladder robustness, the stall rule, the hierarchical follow-up, invalid output polygons, a county example) are done or dropped. See [stall-rule-grid-scaling](../stall-rule-grid-scaling/index.html), [county-gallery-example](../county-gallery-example/index.html), [segment-density-warning](../segment-density-warning/index.html), [validated-windows-pr](../validated-windows-pr/index.html) and [quadtree-windows-pr](../quadtree-windows-pr/index.html).

## Global morph without the stall rule

A single morph of all counties (`hier_global.py`; `MorphOptions(grid=N, grid_margin=0.5, grid_square=True, area_scale=1e-6, stall_patience=None)`), from the original geometries. State error is computed from the summed county areas.

| grid | iterations | time | county mean / median / p95 / max % | state mean / max % | counties off by > 10 % (target < 1 cell) | invalid |
|---|---|---|---|---|---|---|
| 512 | 2000 | 17 s | 12.2 / 1.24 / 54 / 651 | 1.65 / 16.5 | | 408 |
| 1024 | 1500 and 4000 (same result) | 23 s / 50 s | 2.25 / 0.13 / 8.7 / 458 | 0.22 / 3.6 | 142 (90 of them) | 228 |
| 2048 | 4000 | 126 s | 1.02 / 0.01 / 1.2 / 356 | 0.04 / 1.2 | 57 (15 of them) | 127 |

At grid 1024 the default stall rule ends at 50 iterations with a mean error of 929 %. Lowering only `stall_min_improvement` (patience 4) to 0.002 gives a run of 650 iterations in 8 s with mean 5.41 %, median 0.18 %, max 627 % (status stalled); 0.0005 with patience 6 gives the same. The invalid polygons are self-intersections (226 of 228 at 1024); 98 of the 127 at 2048 belong to counties within 5 % of their target. Starting the global morph from the state stage output is not better (1024: mean 5.49 %, 171 invalid).

figure: fig_global.png — County area error log2(area/target) of the single-grid result at grid 1024 and 2048, stall rule off. The remaining large errors are a few sub-cell counties around Washington (grid 1024: a patch in Virginia and Maryland).

## Resolution ladder

`ladder2.py` runs `CartogramWorkflow.morph_multiresolution` with one `MorphOptions` per level (n_iter 1000 per level, margin 0.5, square) and reports every level. A ladder that starts at 256 and ends at 2048 (4 levels) converges to a usable result with the default stall rule in 12 s. The earlier county failures started at 128, where 89 % of the counties are below one cell.

| ladder | stall rule | dt per level | time | level 256 | 512 | 1024 | 2048 (mean / median % , invalid) |
|---|---|---|---|---|---|---|---|
| 256 to 2048 | default | 0.2 | 12 s | mean 69.8 | 37.1 | 4.09 | 2.10 / 0.11, 689 |
| 256 to 2048 | min improvement 0.002 | 0.2 | 18 s | 69.8 | 37.1 | 4.09 | 2.37 / 0.32, 721 |
| 256 to 2048 | min improvement 0.0003, patience 6 | 0.2 | 22 s | 69.8 | 37.1 | 4.09 | 2.37 / 0.32, 721 |
| 256 to 2048 | off, 600 iterations per level | 0.2 | 48 s | 69.8 | 37.1 | 3.39 | 2.73 / 0.60, 734 |
| 256 to 2048 | min improvement 0.002 | 0.2 0.4 0.8 1.0 | 13 s | 69.8 | 34.6 | 4.84 | 4.67 / 0.12, 935 |
| 256 to 2048 | min improvement 0.002 | 0.1 0.2 0.4 0.8 | 14 s | 61.5 | 46.8 | 4.64 | 3.43 / 0.09, 745 |
| 256 to 2048 | min improvement 0.002 | 0.05 0.1 0.2 0.4 | 19 s | 62.0 | 13.3 | 8.38 | 8.29 / 0.20, 785 |
| 512 to 2048 | min improvement 0.002 | 0.2 | 15 s | | 15.1 (512) | 6.63 | 6.39 / 0.12, 324 |
| 128 to 2048 (5 levels) | min improvement 0.002 | 0.2 | 20 s | | | | 13.98 / 1.39, 1662 |
| 64 to 2048 (6 levels) | min improvement 0.002 | 0.2 | 21 s | | | | 56.1 / 21.7, 2363 |

The level columns give the mean error after the levels at grids 256, 512, 1024 and 2048 for the 256 start. The 512-start row lists its levels 512, 1024 and 2048 under the 512, 1024 and 2048 columns; the 128 and 64 rows list only the final level.

- Levels 256 and 512 never converge (sub-cell regions: mean 70 % and 37 %); the work is done at 1024 and 2048, where the shares under one cell are 5 % and 0.3 %.
- The dt schedule changes little. Constant physical step (dt doubling per level, capped at 1.0) and a half-size schedule end within 2 to 8 % mean error, with the default `0.2` best or equal. The stall rule threshold does not matter either once the ladder starts at 256.
- The starting grid matters most. Starting at 128 or 64 leaves the coarse level with tangled counties (1,660 and 2,360 invalid polygons) that finer levels do not repair; starting at 512 is worse than starting at 256 (6.4 % against 2.1 %), the fine-start effect again.
- Against the single grid. Single grid 2048 with the stall rule off reaches 1.0 % mean and 127 invalid polygons in 126 s; the ladder reaches 2.1 % and 689 invalid in 12 s. The ladder's output has about five times as many invalid polygons.

## Hierarchical prototype

1. States. The counties of each state are dissolved and the 49 states are morphed to their population (grid 512), with every county vertex passed as `coords`, so the counties follow the state flow. 3 s, converged in 212 iterations, state area error mean 0.45 %, max 6.2 %.
2. Members. Each state's counties are morphed on a grid fitted to the state, independently, with the outline free.
3. Polish. One global morph on the result.

## Findings

- Stage 2 fixes the county areas. Member grid 256, single level: 17 to 20 s for 49 states, median county error 1.07 %, mean 3.48 %, 168 invalid output polygons; four states (CA, GA, TX, VA) stall. Start 1000 % mean, 145 % median; after stage 1, 506 % and 144 %. The global multiresolution run on the earlier county set had 22 % mean and no converged level.
- The outline is not fixed, so the states overlap. The symmetric difference of a state's outline before and after stage 2 is a median 35 % of the state area. The sum of the state areas exceeds the area of their union by 11.6 % (figure). The polish at grid 512 stalls after 50 iterations and changes neither (11.8 %). Pinning the outline (options 1 to 3 of the issue) is required, not optional.
- Finer member grids fail for a different reason than sub-cell regions. At member grid 512, nine states stall after 50 iterations and the county mean is 232 %. Arizona alone (15 counties, none below one cell) shows why: start mean error 446 %; after 120 iterations the mean error is 155 % at grid 256 and 252 % at grid 512. The step moves the fastest point `dt` grid cells, so the distance per iteration is proportional to the cell size and the iterations needed grow with the grid. The stall rule (2 % improvement over a cycle) then ends the run at 50 iterations, near the start error (grid 512: 405 %, grid 1024: 426 %); without the rule, 300 iterations reach 117 %. `adaptive_dt` off and `dt` 0.05 give the same result. This is probably the unexplained "fine start fails" of the multires-start exploration: a region far from its target on a fine grid needs more iterations than the stall rule allows.
- A ladder per state is not better. Stage 2 as a ladder 64 to 512: 24 s, mean 10.6 %, median 1.74 %, 497 invalid, 13 states not converged. The coarse levels meet the sub-cell problem again at the scale of the state.

## Stages

figure: fig_stages.png — County area error log2(area/target) at the start, after the state stage, after the member stage (grid 256) and after the polish; thin lines are the state outlines of the dissolved counties. After stage 2 the counties are at their target (grey), but the states overlap.
