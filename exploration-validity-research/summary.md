---
issue: 167
title: Validity-preserving flow cartograms without per-iteration meshes (validated windows)
description: Search for a cheap way to end with zero invalid output polygons and to keep the input vertices. A crossing test (uniform grid, numba) on the window-end state, splitting of the crossing segments at the midpoint of their window-start chord, and a replay of the new vertices through the recorded steps of the window give 0 invalid polygons of 3,108 counties (57 in the baseline, 50 to 116 for other step sizes) at 1.1 to 1.3 times the baseline time and +0.1 % vertices when run every 10 windows. Quadtree windows with an exact-crossing-checked pruning also reach 0 but cost 4.8 times the baseline and +61 % vertices. Higher-order advection, smaller steps and a floor on the target values do not reduce the invalid polygons.
kind: exploration
topic: flow
status: open
related: exploration-quadtree-windows, exploration-carried-points, exploration-invalid-regions-field, exploration-adaptive-densification, exploration-county-error-relation, exploration-stall-lagging-regions
date: 2026-10-19 14:00
before: main @ 06d4ff0
after: scratch worktree /home/fakl/cf-validity with hooks in algorithm.py (algorithm_hooks_vw.patch, includes the quadtree hook); not a PR
inputs: 3,108 counties (population) at max_segment_length 1000, congressional districts (432) at 1000, and the coarse county input (simplify_coverage tolerance 4000, 43 k vertices); ladder with min_resolution and levels auto, n_iter 1000, area_scale 1e-6, one run per row unless stated (the dynamics are chaotic and numba parallel kernels add run-to-run noise).
---

## The question

The flow cartogram moves vertices individually, so the image of a straight segment is not a straight segment. Where a region is squeezed to a strip narrower than the vertex spacing, chords cross and the polygon is invalid. The baseline ends with 57 invalid counties of 3,108. Which approach gives zero invalid polygons (or close to it) at a small cost, keeps every input vertex and gives each inserted vertex a lineage for backfilling earlier animation frames, and does not lose accuracy?

## Protocol

As specified in the task: 1 km county input (768,580 vertices), `morph_multiresolution(min_resolution="auto", levels="auto")`, `MorphOptions(area_scale=1e-6, n_iter=1000)`. Invalid = `shapely.is_valid` false on the returned best iterate. Errors are computed on the valid polygons only, with the targets normalized on them. Baseline: 20 s, 57 invalid, mean/median/p95 error 1.37/0.252/2.44 %, 60 valid counties above 10 %, levels 540/110/170 iterations (all stalled). `harness.py` runs and prints all metrics, `run.sh` runs a script against the worktree.

Two cautions that apply to every accuracy number below:

- The runs are chaotic. Changing `dt` from 0.20 to 0.18 or 0.22 changes the baseline invalid count to 90 and 116 and its median error from 0.252 % to 0.014 % and 0.020 %. Mean errors of the baseline over `dt` in 0.15 to 0.25 range from 0.67 % to 5.45 %. A difference of less than a factor of 2 to 3 in a mean error or in the count above 10 % is not a result.
- The counties above 10 % are the sub-cell counties (target area below about 5 cells of the finest grid, 18 km2). Their error depends on when the stall rule ends a level. The finest level ends after 50 to 300 iterations in all runs.

## Method that works: validated windows (`xing.py`, `vw.py`)

Inside a window (between two field recomputes) the field is fixed, so each vertex moves independently of all others. This has three consequences used here.

1. A vertex inserted at the start of the window can be advected through the recorded steps of the window afterwards (replay): it lands where the flow takes it, on the true path, not on the chord.
2. A segment that crosses another at the end of the window can therefore be repaired retroactively: split it at the midpoint of its window-start chord, replay the new vertices, test again, repeat (14 rounds at most, the new sub-segments are tested only against their neighborhood).
3. The polygon at the start of the window is not changed by the insertion (a vertex on the chord), so the repair does not create invalid polygons, and no original vertex moves or disappears.

What was built:

- `xing.py`: crossing detection for all segments of all rings with a uniform grid in numba (build 20 to 40 ms, scan 10 ms for 0.77 M segments). It reports proper crossings; identical segments of two rings (shared boundaries) and shared end points have orientation exactly 0 and are not reported. On the baseline output it flags all 57 invalid polygons and 40 more polygons that overlap a neighbor (no polygon is flagged that is neither). It tests across polygons, so the output is also a valid coverage: `shapely.coverage_invalid_edges` finds 33 polygons with invalid edges and 17 overlapping neighbor pairs (0.48 km2) in the baseline and none in the repaired run (`t_cov.py`).
- `vw.py`: `split_segments` (inserts the midpoint of the S chord, with the end points ordered lexicographically so the two rings of a shared boundary get bit-identical vertices; twins are found through the grid), the replay, the best-iterate bookkeeping (the best state is extended with the replayed positions if it belongs to the span, with the chord midpoint otherwise, and is also tested for crossings), the ring offsets and metadata update without a shapely round trip, and `backfill(coords, events)`.
- Hook points in `algorithm.py` (`algorithm_hooks_vw.patch`): `repair` before the field recompute, `start_window`/`field`/`record`/`mark_best` per window and step, a forced repair before the terminal snapshot and the restore of the best iterate.
- Lineage: every insertion round is stored as `(new_idx, left, 0.5, step)`; the new vertex lies at the midpoint of the segment `(left, left + 1)` of the previous vertex structure. `backfill` lifts any earlier frame to the final structure. Checked in `t_backfill.py`: the 768,580 input vertices lifted through the 26 recorded rounds give 769,473 vertices, equal to the final structure, and the level-1 and level-2 results have 768,676 and 769,072 vertices. The lifted frames are the same point sets (the vertices lie on chords), so a frame that was valid stays valid.
- `check_every` (k): the detection and repair run every k windows instead of every window. The start-of-span coordinates are kept and the fields of the k windows are copied (46 MB per window at the finest grid), and the replay applies them in order. The state and the best iterate are tested at the end of the span.
- `max_len` (cells): optional rule that splits chords longer than `max_len` cells at every window start; needed for the coarse input only.
- `min_len` (cells, 1e-7) and `depth` (14): refinement stops at sub-segments shorter than `min_len` cells; the invalid polygons that remain contain hundreds of segments below 1 m (`t_inv.py`), i.e. zero-width features of the input geometry.

## Results

County, 1 km input, n_iter 1000. Time is wall time of the whole ladder. Error columns: valid polygons, targets normalized on them, mean / median / p95, then the number above 10 %. Rows marked (old) are from the earlier reports, with their protocol.

| candidate | guarantee | time | invalid | vertices | mean / median / p95 error | >10 % | vertex correspondence |
|---|---|---|---|---|---|---|---|
| baseline | none | 20 s | 57 | 768,580 | 1.37 / 0.252 / 2.44 | 60 | identical |
| baseline, dt 0.15 / 0.18 / 0.22 / 0.25 | none | 18 / 21 / 27 / 16 s | 62 / 90 / 116 / 76 | 768,580 | 5.45 / 1.12 / 0.67 / 1.25 (mean) | 371 / 65 / 28 / 77 | identical |
| baseline, dt 0.05, n_iter 3000 | none | 36 s | 105 | 768,580 | 4.52 / 0.045 / 23.2 | 258 | identical |
| RK2 advection | none | 25 s | 60 | 768,580 | 1.72 / 0.390 / 3.99 | 73 | identical |
| RK4 advection | none | 28 s | 53 | 768,580 | 3.01 / 0.431 / 11.6 | 177 | identical |
| Euler, 4 substeps per step | none | 35 s | 65 | 768,580 | 1.61 / 0.283 / 3.79 | 81 | identical |
| target values floored at 0.05 / 0.2 x median | none | 25 / 24 s | 63 / 50 | 768,580 | measured against the true values: 2.02 / 17.5 (mean) | 84 / 281 | identical |
| carried points 0.5 / 0.25 / 0.125 km (old) | none, empirical | 1.6 / 2.7 / 4.3 x | 29 / 11 / 10 | not reported | unchanged morph | | all input vertices kept, extra points rebuilt after the run |
| quadtree 2^-8, insertion, no pruning (old) | construction, no inverted triangle seen | 93 s | 0 | 5.2 M | 6.9 / 1.06 (mean / median) | | inserted vertices with lift maps |
| quadtree 2^-6, insertion, pruning by chord distance 0.02 cell (old) | none | 99 s | 91 | 1.08 M | 1.72 / 0.11 (mean / median) | | lift maps; pruning removes vertices |
| quadtree 2^-6, insertion, pruning 0.02 cell checked with the crossing test (new) | exact test at each window start | 97 s | 0 | 1.24 M | 3.49 / 0.055 / 15.4 | 207 | removed vertices include input vertices |
| validated windows, every window | exact test at each window end | 32 s | 0 | 770,600 | 2.03 / 0.097 / 6.56 | 108 | input vertices kept, +2,020 with lineage |
| validated windows, every 2 | same, 2 windows | 29 s | 0 | 770,974 | 1.53 / 0.173 / 6.16 | 63 | same |
| validated windows, every 3 | same, 3 windows | 24 s | 3 | 770,203 | 1.78 / 0.134 / 4.75 | 89 | same |
| validated windows, every 5 | same, 5 windows | 26 s | 0 | 770,256 | 1.76 / 0.110 / 5.62 | 90 | same |
| validated windows, every 10 | same, 10 windows | 22 s (26 s in a repeat) | 0 | 769,473 | 1.08 / 0.195 / 2.63 | 45 | same, +893 |
| validated windows, every 20 | same | 22 s | 0 | 769,411 | 1.08 / 0.196 / 2.68 | 45 | same |
| validated windows, every 10, dt 0.15 / 0.18 / 0.22 / 0.25 | same | 22 / 20 / 27 / 20 s | 0 / 0 / 0 / 0 | +1.0 k / 1.1 k / 2.8 k / 1.6 k | 2.44 / 2.91 / 1.16 / 3.69 (mean) | 167 / 177 / 71 / 217 | same |
| validated windows, every window, dt 0.18 / 0.22 (min_len 1e-4 or 1e-7) | same | 41 / 46 s | 7 / 2 to 6 | +3.9 k / +11 k | 0.93 / 1.24 (mean) | 41 / 53 | same |

Levels (iterations, all stalled except where the budget ended the level): baseline 540/110/170, every 10: 500/80/200, every window: 620/70/90. With every 10 the hook time is about 2 s per run (detection 1.1 s, repair 0.8 s). The `dt` rows pair a baseline with a validated run at the same step size; the validated runs have 0 invalid in all five step sizes, the baselines 57 to 116. For the mean error, the validated run is lower than its baseline for dt 0.15 and 0.20 and higher for 0.18, 0.22 and 0.25; I cannot tell a difference from the noise.

Other inputs:

| input | run | time | invalid | vertices | mean / median / p95 error | >10 % |
|---|---|---|---|---|---|---|
| congressional districts, 1 km | baseline | 1.6 s | 2 | 343,042 | 0.48 / 0.264 / 1.90 | 0 |
| congressional districts, 1 km | validated windows, every 10 | 1.8 s | 0 | 343,046 | 0.48 / 0.262 / 1.89 | 0 |
| coarse counties (43 k vertices) | baseline | 11 s | 327 | 43,084 | 12.3 / 0.934 / 49.7 | 508 |
| coarse counties | quadtree 2^-6 + coverage_simplify 0.02 cell (old) | 94 s | 0 | 552 k | 1.34 / 0.074 / 4.0 | |
| coarse counties | validated windows, every window, `max_len` 1 cell, refinement stop after 3 rounds without progress, min_len 1e-6 | 28 s | 12 | 300,606 (230 k from `max_len`) | 1.15 / 0.147 / 3.67 | 53 |
| coarse counties | same, every 3, min_len 1e-7 | 23 s | 24 | 294,222 | 1.16 / 0.038 / 3.11 | 73 |
| coarse counties | same, every 10 | 27 s | 39 | 301,451 | 3.18 / 0.066 / 15.1 | 200 |
| coarse counties | same as every window without the stop rule | 470 s | 5 | 327,801 | 1.15 / 0.148 / 3.67 | 53 |
| coarse counties | validated windows, no `max_len`, every window (first version, min_len 1e-4) | 142 s | 3 | 110,322 | 5.98 / 0.287 / 26.2 | 305 |

figure: fig1_invalid_counts.png — Invalid output polygons of the 3,108 counties for the baseline at five step sizes, for the alternatives that did not help, for the quadtree with checked pruning and for validated windows every 10 windows at the same five step sizes.
figure: fig2_example.png — A county that is invalid in the baseline and the same county in the validated run (the two runs diverge, so the shapes differ): the thin tail is resolved by vertices inserted on the flow path.

## What works

- Validated windows give 0 invalid polygons on the 1 km counties in five of the six runs at the default step size (`check_every` 1, 2, 5, 10, 20; every 3 gave 3), in all five step sizes with `check_every` 10, and on the districts. The every-window runs at other step sizes gave 2 to 7. They keep every input vertex, add 0.1 % vertices and cost 10 to 30 % time with `check_every` 10 to 20 (22 to 27 s against 20 s). The detection costs 40 to 80 ms per call; every window it adds 6 s to the 20 s baseline, every 10 windows 1 s.
- The result is a valid coverage, not only valid polygons, so the density and velocity fields are computed from valid regions when the check runs every window (not between checks when `check_every` is larger).
- A long check interval (10 to 20 windows, i.e. a check about once per level) works on the 1 km input because the repair is retroactive: the vertices follow the same flow lines whatever the polygon looked like in between. It does not work on the coarse input (39 invalid at every 10, 12 at every window), where the chords are long and the crossings pile up.
- On the coarse input the combination with the length rule gets 7 times the vertices of the input for 12 invalid polygons and mean error 1.15 %, at 28 s against 94 s for the quadtree with coverage simplification (0 invalid, 552 k vertices).
- Safe removal of inserted vertices by a crossing test works as a method (91 to 0 invalid for the quadtree pruning) but the quadtree itself stays expensive.

## What does not work, or is open

- Higher-order or sub-stepped advection (RK2, RK4, 4 Euler substeps), a smaller step (dt 0.05) and a floor on the target values (0.05 and 0.2 times the median) do not change the invalid count (53 to 105; the baseline varies from 57 to 116 with the step size). The cause is the chord, not the integrator: a strip narrower than the vertex spacing has crossing chords whatever the path accuracy. A step limit cannot help for the same reason (the width goes below the spacing even with infinitely small steps).
- The quadtree with checked pruning: 4.8 times the time and 61 % more vertices, with removal of input vertices, and the median error is the best of the table but the mean and the number above 10 % are not (the finest level was cut by the budget at 40 iterations). It is dominated by validated windows.
- The remaining invalid polygons (every-window runs with other step sizes, coarse input) contain zero-width features: segments of 1 mm to 1 m at both sides of a crossing with start-of-window chords that already nearly coincide (`t_fail.py`, `t_inv.py`). Splitting the chord cannot separate two curves that touch at the start of the window. They would need a different treatment (collapsing the spike, which changes vertices) or are accepted as a floor.
- Without a stop rule a failing refinement cascades (every window on the coarse input: 470 s, 246 k unresolved segments). The stop after 3 rounds without progress and a `min_len` bound it.
- Accuracy: the tail (counties above 10 %) is dominated by the sub-cell counties and by when the stall rule ends the finest level; with every window the finest level stalled after 90 iterations with the best iterate at 42 and 99 baseline-valid counties above 10 % (against 60), with every 10 windows 43 (`cmp2.py`, `where.py`). The 97 counties above 5 % in the first run are the plains counties that have shrunk to 8 % of their area and are below target (82 of 97). I did not find a systematic effect of the repair on accuracy; I could not exclude one.
- The check state is only exact at the end of a span and for the best iterate. Snapshots taken in the middle of a span (`snapshot_every`) and the frames stored per level are not repaired. A fold that appears and disappears inside a span is not detected (not observed).
- Not tested: combination with the density-field repair (the repair is subsumed when the check runs every window; with a long interval the fields still see invalid polygons), the paper's constrained Delaunay triangulation, the continuous collision control with backtracking, the mesh-deformation formulation, shared arcs.
- Numba noise: a repeated run of one every-window configuration gave 2 and 4 invalid polygons.

## Assessment of the other ideas (not built unless a row above says so)

| idea | expected payoff | reason |
|---|---|---|
| continuous collision control with shorter steps (B1) | low | The crossing is caused by the chord of a squeezed strip, so a shorter step only delays it. Smaller dt gave 105 invalid (row above). Detection is useful, and was used. |
| local subdivision driven by stretch and local width (B2) | covered | Validated windows are this with the exact crossing test as criterion. The stretch is not predictive: the stretch of the flagged segments has median 1.00 (`diag1.py`). |
| fold detection and local repair by re-integration (B3) | covered | Validated windows. |
| higher-order integration (B4) | none | Measured, no effect. |
| shared arcs (B5) | speed only | Would halve the advection of shared vertices and remove the twin search, but advection is not the cost. |
| mesh deformation (B6) | unknown, high cost | The quadtree prototype is the cheaper approximation of it and it costs 4 to 5 times the baseline. |
| value floor / shrink limit (B7) | none | Measured, no effect on the invalid count. |
| coverage-aware or twin-free repair | n/a | Twins are found through the grid; no problem seen. |

Literature: Miaji et al. (arXiv 2511.08121) is the only paper found that treats the invalid topology of density-equalizing cartograms (line densification plus topology-preserving simplification). Andrieu et al. (2007, rubber-sheet cartograms) try a smaller force vector when the topology fails and reject the deformation if it still fails; that is the step-limit idea above and it does not address a strip narrower than the vertex spacing.

## Recommendation, ranked

1. Build validated windows as an option of the flow algorithm (`check_every` about 10 windows for dense input, 1 to 3 with `max_len` 1 cell for coarse input). It is the only candidate with 0 invalid polygons at about baseline cost and 0.1 % extra vertices, it keeps all input vertices and has a lineage. Library parts: `xing.py` (crossing detection, candidate for `geo_utils`), `split_segments` and `backfill`, the span/replay bookkeeping, and an extra field in the result for the insertion events (`new_idx`, `left`, `t`, step). Needs: the hook points as proper code, the memory of the stored fields (460 MB at 10 windows on the finest grid; bound `check_every` by memory), repair of the mid-run snapshots if they are used for animation, and a decision on the residual zero-width cases (report them in `invalid_regions`, which exists).
2. Keep the quadtree prototype only as a reference. Drop RK2/RK4, smaller steps and the value floor.
3. Open: whether the invalid polygons seen by the density between checks (long `check_every`) cost accuracy on other inputs than the counties (not seen here, but the coarse input fails at every 10); whether an adaptive interval (check every window while crossings are found, every 10 otherwise) removes that; repeated runs for the accuracy columns.

## Files

`xing.py`, `vw.py`, `algorithm_hooks_vw.patch`, `harness.py` (protocol and metrics), `run.sh`, `base.py`, `runvw.py` (environment variables `EVERY`, `MAXLEN`, `MINLEN`, `DEPTH`, `STOPR`, `MORPH_OPTS`, `LABEL`), `expb.py` (RK2/RK4/substeps, value floor), `pw2.py`, `pw.py`, `pwrun_h.py` (quadtree with checked pruning, `SAFE=1`), `t_backfill.py`, `t_cov.py`, `t_inv.py`, `t_fail.py`, `diag1.py`, `cmp.py`, `cmp2.py`, `where.py`, `figs.py`, `batch1.sh` to `batch4.sh` with their logs. The scripts import each other from their own directory; `run.sh` has the scratch path of this session hard-coded.
