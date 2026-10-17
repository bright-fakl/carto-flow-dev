---
issue: 129
title: Hierarchical flow morph on counties: first prototype
description: Morphing the states first (county vertices carried along) and then each state's counties on a grid fitted to the state brings the county median error from 144 % to 1.1 % and the mean from 1000 % to 3.5 % in about 25 s, against 22 % mean for the global multiresolution run. Without a fixed outline the states overlap by 11.6 % of the map and a global polish does not repair it. Separately, a plain state at grid 512 or finer stalls at its start error because the step is dt grid cells and the stall rule fires before enough iterations have run.
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

## Prototype

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

- Pin or decompose the outline (issue options 1 to 3). Option 2 (global flow from the state level plus a local part from each member's deviation from the state mean density) fits the prototype best: stage 1 already provides the global part.
- Step size in physical units, or a stall rule that counts progress per distance moved, so a far start on a fine grid is not cut off (separate issue candidate).
- Invalid output polygons (168 at member grid 256) need the repair the flow output already has an issue for (#85).
- Counties with the vote values of the earlier explorations, to compare directly.
