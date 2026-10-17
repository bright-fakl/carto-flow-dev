---
issue: 129
title: County flow cartograms: hierarchical prototype, and the stall rule as the main obstacle
description: A single global morph of the 3,108 counties reaches a mean error of 1.0 % and a median of 0.01 % at grid 2048 (126 s) and 2.2 % / 0.13 % at grid 1024 (23 s) once the stall rule is off; with only stall_min_improvement lowered to 0.002 the default stack reaches 5.4 % mean at 1024 in 8 s. The earlier county failures were the stall rule ending slow progress after 50 iterations, not sub-cell regions alone. The hierarchical prototype (states first, then counties per state) fixes the county areas but leaves the state outlines free, so the states overlap by 11.6 %; it is not needed to get a county cartogram. A plain Arizona (15 counties) converges at every grid once the stall rule is off.
kind: exploration
topic: flow
status: open
related: exploration-hierarchical-morph, exploration-multires-start, exploration-counties-subcell
date: 2026-10-18 21:00
before: main @ cf7d1bb
after: the same checkout; prototype scripts only, no library change
inputs: 3,108 contiguous counties from cb_2020_us_county_500k with the 2020 Census population estimate (co-est2020-alldata.csv), ESRI:102008, coverage-simplified at 1000 m with 5 km segments. The vote set of the earlier explorations is not available, so the numbers are not comparable one to one. MorphOptions grid_margin 0.5, square, area_scale 1e-6, n_iter 500; NUMBA_NUM_THREADS=8. Error is the output area against the population share of the total output area.
---

`prep_counties.py` builds the set, `hier129.py` runs the three stages (member grid, state grid and polish grid as arguments), `hier_ladder.py` runs stage 2 as a ladder, `probe_az*.py` are the Arizona probes. Logs are in `data/`.

## Global morph without the stall rule

A single morph of all counties (`hier_global.py`; `MorphOptions(grid=N, grid_margin=0.5, grid_square=True, area_scale=1e-6, stall_patience=None)`), from the original geometries. State error is computed from the summed county areas.

| grid | iterations | time | county mean / median / p95 / max % | state mean / max % | counties off by > 10 % (target < 1 cell) | invalid |
|---|---|---|---|---|---|---|
| 512 | 2000 | 17 s | 12.2 / 1.24 / 54 / 651 | 1.65 / 16.5 | | 408 |
| 1024 | 1500 and 4000 (same result) | 23 s / 50 s | 2.25 / 0.13 / 8.7 / 458 | 0.22 / 3.6 | 142 (90 of them) | 228 |
| 2048 | 4000 | 126 s | 1.02 / 0.01 / 1.2 / 356 | 0.04 / 1.2 | 57 (15 of them) | 127 |

At grid 1024 the default stall rule ends at 50 iterations with a mean error of 929 %. Lowering only `stall_min_improvement` (patience 4) to 0.002 gives a run of 650 iterations in 8 s with mean 5.41 %, median 0.18 %, max 627 % (status stalled); 0.0005 with patience 6 gives the same. The invalid polygons are self-intersections (226 of 228 at 1024); 98 of the 127 at 2048 belong to counties within 5 % of their target. Starting the global morph from the state stage output is not better (1024: mean 5.49 %, 171 invalid).

figure: fig_global.png — County area error log2(area/target) of the single-grid result at grid 1024 and 2048, stall rule off. The remaining large errors are a few sub-cell counties around Washington (grid 1024: a patch in Virginia and Maryland).

## Hierarchical prototype

1. **States.** The counties of each state are dissolved and the 49 states are morphed to their population (grid 512), with every county vertex passed as `coords`, so the counties follow the state flow. 3 s, converged in 212 iterations, state area error mean 0.45 %, max 6.2 %.
2. **Members.** Each state's counties are morphed on a grid fitted to the state, independently, with the outline free.
3. **Polish.** One global morph on the result.

## Findings

- **Stage 2 fixes the county areas.** Member grid 256, single level: 17 to 20 s for 49 states, median county error 1.07 %, mean 3.48 %, 168 invalid output polygons; four states (CA, GA, TX, VA) stall. Start 1000 % mean, 145 % median; after stage 1, 506 % and 144 %. The global multiresolution run on the earlier county set had 22 % mean and no converged level.
- **The outline is not fixed, so the states overlap.** The symmetric difference of a state's outline before and after stage 2 is a median 35 % of the state area. The sum of the state areas exceeds the area of their union by 11.6 % (figure). The polish at grid 512 stalls after 50 iterations and changes neither (11.8 %). Pinning the outline (options 1 to 3 of the issue) is required, not optional.
- **Finer member grids fail for a different reason than sub-cell regions.** At member grid 512, nine states stall after 50 iterations and the county mean is 232 %. Arizona alone (15 counties, none below one cell) shows why: start mean error 446 %; after 120 iterations the mean error is 155 % at grid 256 and 252 % at grid 512. The step moves the fastest point `dt` grid cells, so the distance per iteration is proportional to the cell size and the iterations needed grow with the grid. The stall rule (2 % improvement over a cycle) then ends the run at 50 iterations, near the start error (grid 512: 405 %, grid 1024: 426 %); without the rule, 300 iterations reach 117 %. `adaptive_dt` off and `dt` 0.05 give the same result. This is probably the unexplained "fine start fails" of the multires-start exploration: a region far from its target on a fine grid needs more iterations than the stall rule allows.
- **A ladder per state is not better.** Stage 2 as a ladder 64 to 512: 24 s, mean 10.6 %, median 1.74 %, 497 invalid, 13 states not converged. The coarse levels meet the sub-cell problem again at the scale of the state.

## Stages

figure: fig_stages.png — County area error log2(area/target) at the start, after the state stage, after the member stage (grid 256) and after the polish; thin lines are the state outlines of the dissolved counties. After stage 2 the counties are at their target (grey), but the states overlap.

## Open

- The hierarchical approach is not needed to get a county cartogram: the global morph is far better once it runs long enough. It remains an option for speed and for the sub-cell counties.
- Pin or decompose the outline (issue options 1 to 3), if the hierarchical approach is pursued. Option 2 (global flow from the state level plus a local part from each member's deviation from the state mean density) fits the prototype best: stage 1 already provides the global part.
- Step size in physical units, or a stall rule that counts progress per distance moved, so a far start on a fine grid is not cut off (separate issue candidate).
- Invalid output polygons (168 at member grid 256) need the repair the flow output already has an issue for (#85).
- Counties with the vote values of the earlier explorations, to compare directly.
