---
pr: 123
url: https://github.com/bright-fakl/carto-flow/pull/123
issue: 94, 109
title: Adaptive step size for the flow cartogram
description: MorphOptions.adaptive_dt (default on) shrinks the step when the regions' area errors alternate in sign and limits the first steps of a run that starts near the target. The sign of an error counts above a dead band tied to the max tolerance. All 32 tight-tolerance runs converge against 18 for constant dt, the late-phase oscillation of the true maximum error drops by a factor of 3 to 9, a continuation from a converged cartogram takes 1 iteration instead of 4, the districts multiresolution run at 0.5 % / 1 % converges (157 against 173 iterations), and the 12 default-tolerance runs are identical to constant dt.
kind: pr
topic: flow
branch: feat/adaptive-step
base: main
date: 2026-10-11 13:41
related: exploration-adaptive-step, exact-density-coverage, flow-convergence-synthesis
before: main @ 7ba9f31 (constant dt; reproduced with adaptive_dt=False)
after: feat/adaptive-step @ a76dfb4
inputs: US states (49 incl. DC) and congressional districts (432), bundled; the three strong-anisotropy runs of the adaptive-recompute page (states, preset_balanced values, area_scale 1e-6, DirectionalTensor horizontal / tangential / tilted); 3,108 counties (prepared set, not bundled). MorphOptions defaults except where stated (dt 0.2, recompute_every 10, recompute_on_rise 0.01, exact rasterization, stall rule on, n_iter 400); NUMBA_NUM_THREADS=8, runs sequential. True error is the output area against the population share of the total output area. Cost = iterations + field recomputes x cost of one recompute in plain steps (states 9, 12, 24 at grids 128, 256, 512; districts 18, 21, 23; measured on adaptive-recompute-experiment).
---

`make_figures.py` runs every experiment below and writes the figures and `data/tables.md` (all tables, one row per run); `REUSE=1` reuses the stored `data/*.json`. `diagnostic_plots.py` writes the diagnostics_*.png figures, `dead_band_sweep.py` the dead band tables (`data/tables_dead_band.md`), and `contested_check.py` the check of a condition that was dropped (`data/tables_contested_check.md`; it needs the earlier head of the branch). The counties part of `make_figures.py` runs when `COUNTIES_PARQUET` points at a GeoDataFrame file with `GEOID`, `total_votes` and `geometry`; it was not run for this version. The numbers in "How the rule was chosen" come from throwaway variants of the branch and are not regenerated.

All measurements are on top of #124 (ring orientation in the exact rasterizer): before that fix some runs of the districts stalled because a region with a self-intersecting ring dropped out of the density field, which hid or mimicked effects of the step control (see "Considered and dropped").

## What changes

The step moves the fastest point `dt` grid cells whatever the error (`dt_prime = dt * min(dx, dy) / max_v`; the field's strength cancels). Near the target that is more than the correction asks for: the area of each region alternates around its target with an amplitude proportional to `dt`, and a tolerance below the amplitude is met only when the oscillation dips below it ([exact-density-coverage](../exact-density-coverage/index.html), section "Late phase").

`MorphOptions.adaptive_dt` (default `True`; `False` is the constant step of main) multiplies `dt` by a fraction `f` in [1/8, 1]:

- **Sign changes.** A region is inverted if the sign of its area error (current area against target, as `log2` of the ratio) changed in any of the last 3 iterations; a change is only recorded between two iterations in which the region's error exceeds a dead band of `0.1 * log2(1 + max_tol)` (4.1e-3 at the default tolerances, 1.4e-3 at 0.5 % / 1 %, 5.8e-4 at 0.2 % / 0.4 %; regions inside the dead band are skipped, the last significant sign is not kept). When more than 30 % of the regions are inverted, `f` is multiplied by `1 - 0.6 s` (`s`: share of inverted regions), and the next 3 iterations cannot shrink it again. `f` never grows back. Apart from the dead band the rule uses neither the score nor the tolerances, and it does not depend on `recompute_on_rise`.
- **Restart.** In the first `max(recompute_every, 10)` iterations `f` is also limited to the score of the current state (for the first step: of the input geometries) divided by 10, not below 1/8. A run that starts far from the target (score above 10) is not affected.

The constants (3 iterations, 0.1 for the dead band, 30 %, 0.6, 1/8, 10) are fixed in `stepsize.py`; the only option is the switch. The controller is created for each morph call, so every level of a multiresolution run starts again at fraction 1.

figure: inversion_share.png — Share of regions with a sign change in the last 3 iterations (orange) against the true maximum area error (blue, right axis), states at grid 256, dt 0.2, constant dt, every iteration recorded. The share is about 0 while the error falls from 1700 % to 10 % and 0.75 to 0.9 once the oscillation starts around iteration 112.

## Late phase

figure: late_phase.png — Left: true maximum area error at each of the last 80 of 300 iterations, states at grid 256, dt 0.2, tolerances 1e-6 (unreachable), dead band as for a max tolerance of 0.4 %, stall rule off, every iteration recorded (default `recompute_on_rise`). Right: highest and median over the last 50 iterations against dt.

True maximum error over the last 50 of 300 iterations, with every iteration recorded and computed from the geometry of each snapshot (the cycle has period 2, so sampling every n-th iteration is not representative). The tolerances of these runs are unreachable (1e-6), so the dead band is set explicitly as for a max tolerance of 0.4 % (`0.1 * log2(1.004)` = 2.9e-4).

| input | dt | recompute_on_rise | constant dt: lowest / median / highest % | adaptive_dt: lowest / median / highest % |
|---|---|---|---|---|
| states | 0.1 | 0.01 | 0.426 / 0.622 / 2.160 | 0.013 / 0.278 / 0.746 |
| states | 0.1 | None | 0.228 / 4.159 / 17.562 | 0.060 / 1.111 / 3.785 |
| states | 0.2 | 0.01 | 0.302 / 0.814 / 2.003 | 0.101 / 0.108 / 0.322 |
| states | 0.2 | None | 0.303 / 5.322 / 14.540 | 0.075 / 0.482 / 1.435 |
| states | 0.4 | 0.01 | 1.287 / 2.371 / 6.223 | 0.001 / 0.385 / 0.808 |
| states | 0.4 | None | 1.114 / 8.717 / 19.548 | 0.061 / 1.128 / 3.184 |
| districts | 0.2 | 0.01 | 0.388 / 0.964 / 2.742 | 0.034 / 0.335 / 0.813 |
| districts | 0.2 | None | 2.849 / 5.947 / 14.051 | 0.171 / 1.958 / 4.034 |

The highest error drops by a factor of 3 to 9 with the default recompute (2.0 to 0.32 % at dt 0.2). Without `recompute_on_rise` the field is stale for up to 10 iterations and the constant-dt cycle is much larger (14 to 20 %); the rule reduces it by a factor of 4 to 10, and what remains is the stale field, not the step.

figure: tight_traces.png — Score per iteration, states at grid 256, tolerances 0.2 % / 0.4 %, stall rule off. Constant dt oscillates between about 1.3 and 20 and converges when it happens to dip (148 and 100 iterations); with adaptive_dt the oscillation decays after the first shrinks.

## Tight tolerances

32 runs: states at grids 128, 256, 512 and districts at grid 256, tolerances (mean / max) 0.2 % / 0.4 % and 0.5 % / 1 %, dt 0.2 and 0.4, `recompute_on_rise` 0.01 and None (rows in `data/tables.md`).

| | constant dt converges | adaptive_dt converges |
|---|---|---|
| `recompute_on_rise` 0.01 (16 runs) | 10 | 16 |
| `recompute_on_rise` None (16 runs) | 8 | 16 |
| total | 18 of 32 | 32 of 32 |

Of the 18 runs where both converge the median cost ratio is 0.78 (range 0.20 to 1.10); two cost more: states at grid 256, 0.5 % / 1 %, dt 0.4, default recompute (64 iterations, cost 160, against 68, 176) and districts at grid 256, 0.5 % / 1 %, dt 0.2, default recompute (156, 555 against 160, 559). States at grid 128, 0.5 % / 1 %, dt 0.2: 182 iterations (cost 776) against 71 (152). The true maximum error of the output is equal or lower in 27 of the 32 runs; in the five others it is higher but within the tolerance (0.34 against 0.20 %; 0.95 against 0.85 %; 0.99 against 0.85 %; 0.98 against 0.97 %; 0.24 against 0.23 %). The two districts runs at grid 256 with `recompute_on_rise=None` and dt 0.4 stall in constant dt with a 62 % true maximum error (a region that had dropped out of the field before #124 was merged; they stall at the same point on main) and converge with adaptive_dt (167 and 184 iterations).

figure: cost_ratio.png — Cost with adaptive_dt over cost with constant dt per run (log scale). Left: the 12 runs at the default tolerances. Right: the 32 tight-tolerance runs. Triangles mark runs where only adaptive_dt converged (their ratio compares against a stalled or capped constant-dt run, so it understates the gain).

## Runs at the default tolerances

12 runs; wall time is the minimum of two. All 12 are identical to constant dt in status, iterations and final error (the dead band at the default tolerances, 4.1e-3, is wider than the sign changes of the late cycle), and wall times agree within noise:

| input | grid | dt | iterations, constant dt | iterations, adaptive_dt | wall s, constant dt / adaptive_dt |
|---|---|---|---|---|---|
| states | 128 | 0.2 | 62 | 62 | 0.14 / 0.14 |
| states | 256 | 0.2 | 112 | 112 | 0.30 / 0.23 |
| states | 512 | 0.2 | 214 | 214 | 0.54 / 0.55 |
| districts | 256 | 0.2 | 145 | 145 | 0.57 / 0.56 |
| states | 256 | 0.4 | 62 | 62 | 0.15 / 0.15 |
| districts | 256 | 0.4 | 81 | 81 | 0.41 / 0.42 |
| horizontal | 256 | 0.2 | 207 | 207 | 0.35 / 0.35 |
| horizontal | 256 | 0.6 | 122 | 122 | 0.38 / 0.28 |
| tangential | 256 | 0.2 | 187 | 187 | 0.32 / 0.30 |
| tangential | 256 | 0.6 | 118 | 118 | 0.26 / 0.27 |
| tilted | 256 | 0.2 | 162 | 162 | 0.27 / 0.28 |
| tilted | 256 | 0.6 | 95 | 95 | 0.22 / 0.21 |

## Continuation from an existing geometry

A second `CartogramWorkflow.morph` on the result of a first run, tolerances 0.5 % / 1 % (rows in `data/tables.md`):

| input | grid | first run | constant dt: iterations (cost), score after iteration 1 | adaptive_dt: iterations (cost), score after iteration 1 |
|---|---|---|---|---|
| states | 256 | converged at 0.5 % / 1 % | 4 (28), 2.5 | 1 (13), 0.4 |
| states | 256 | converged at 5 % / 20 % | 92 (620), 1.6 | 3 (27), 1.5 |
| states | 512 | converged at 0.5 % / 1 % | 4 (52), 2.7 | 1 (25), 0.3 |
| states | 512 | converged at 5 % / 20 % | 4 (52), 8.0 | 3 (27), 8.0 |
| districts | 256 | converged at 0.5 % / 1 % | 4 (46), 2.3 | 1 (22), 0.3 |
| districts | 256 | converged at 5 % / 20 % | 7 (70), 7.0 | 13 (97), 7.0 |

The restart limit is needed. In a throwaway variant without it (measured with an earlier version of the rule: states, grid 128, tolerances 0.5 % / 1 %, converged first run) the second run took 19 iterations (score 8.9, 18.7, 13.9 after the first three iterations) against 4 with constant dt and 1 with the limit: the first step undoes the convergence before any sign change can be seen, and the sign rule then shrinks the step for a run that has to converge again.

The districts at grid 256 started from a loose result are slower with adaptive_dt (7 against 13 iterations): the score of the start is 7, so the limit takes 70 % of the step although a full step was right.

figure: restart.png — Iterations of the second run on the output of a first run.

### Multiresolution

`morph_multiresolution(min_resolution=128, levels=3)`, 300 iterations per level; the loop stops at the first converged level (cost over the levels run):

| input | tolerances | dt | constant dt | adaptive_dt |
|---|---|---|---|---|
| states | default 5 % / 10 % | 0.2 | 128: converged 63; cost 126 | 128: converged 63; cost 126 |
| states | default 5 % / 10 % | 0.4 | 128: converged 39; cost 93 | 128: converged 39; cost 93 |
| states | 0.5 % / 1 % | 0.2 | 128: converged 94; cost 292 | 128: converged 70; cost 151 |
| states | 0.5 % / 1 % | 0.4 | 128: converged 45; cost 126 | 128: converged 49; cost 112 |
| districts | default 5 % / 10 % | 0.2 | 128: converged 123; cost 447 | 128: converged 123; cost 447 |
| districts | default 5 % / 10 % | 0.4 | 128: converged 102; cost 480 | 128: converged 102; cost 480 |
| districts | 0.5 % / 1 % | 0.2 | 128: converged 173; cost 947 | 128: converged 157; cost 715 |
| districts | 0.5 % / 1 % | 0.4 | 128: stalled 160 256: stalled 50 512: stalled 50; cost 3154 | 128: stalled 170 256: stalled 50 512: stalled 50; cost 3509 |

Equal or cheaper in five of the eight runs (states 0.5 % / 1 % at dt 0.2 and 0.4, districts 0.5 % / 1 % at dt 0.2: 947 to 715, and the two default-tolerance dt 0.2 runs are equal); the districts at 0.5 % / 1 % and dt 0.4 stall at every level in both modes (grid 128 reaches a 5 to 6 % maximum error: not a step problem); the states at dt 0.4 with default tolerances take the same iterations.

## recompute_on_rise

The tables above use both settings where it matters. The one false stall of an earlier design (states, dt 0.2, tolerances 0.2 % / 0.4 %, `recompute_on_rise=None`) does not occur: adaptive_dt converges in 151 iterations, constant dt in 192.

| input | dt | tolerances | recompute_on_rise | constant dt: status, it, cost | adaptive_dt: status, it, cost |
|---|---|---|---|---|---|
| states | 0.2 | (0.002, 0.004) | 0.01 | converged, 148, 508 | converged, 118, 286 |
| states | 0.2 | (0.002, 0.004) | None | converged, 192, 432 | converged, 151, 343 |
| states | 0.4 | (0.002, 0.004) | 0.01 | converged, 100, 412 | converged, 70, 178 |
| states | 0.4 | (0.002, 0.004) | None | stalled, 210, 462 | converged, 122, 278 |
| tilted | 0.6 | default | 0.01 | converged, 95, 275 | converged, 95, 275 |
| tilted | 0.6 | default | None | stalled, 130, 286 | stalled, 130, 286 |
| horizontal | 0.6 | default | 0.01 | converged, 122, 338 | converged, 122, 338 |
| horizontal | 0.6 | default | None | converged, 164, 368 | converged, 164, 368 |

Tilted at dt 0.6 without `recompute_on_rise` stalls in both modes at the same iteration (the rule does not fire there).

## Counties

3,108 counties, grid 256, 300 iterations: constant dt and adaptive_dt gave the same run before #124 (stalled at 210 iterations, best iteration 169, true mean 49.6 %, max 5018 %; targets far below one cell). Not re-measured on top of #124; whether the counties are affected by the ring orientation is open.

## Per-iteration diagnostics

`diagnostic_plots.py` records every iteration of ten scenarios, with the settings of the tables above, for adaptive_dt off and on. Panels, same x axis: (1) true maximum area error from the geometry of each snapshot with the tolerance and the stopping iteration (dotted); (2) share of regions whose error sign changed in the last 3 iterations (the controller's detection and dead band), the threshold 0.3 and the shrink events (filled triangles: on run; open triangles: events the controller would have produced on the constant-dt run); (3) fraction of dt: actual for the on run, predicted for the constant-dt run by replaying the controller on its recorded errors (open loop); (4) true mean area error with its tolerance.

### Scenarios where the rule is inactive or costs

figure: diagnostics_horizontal_dt06.png — Horizontal anisotropy, dt 0.6, default tolerances: 122 iterations in both modes.
figure: diagnostics_tangential_dt06.png — Tangential anisotropy, dt 0.6: 118 in both modes.
figure: diagnostics_tilted_dt06.png — Tilted anisotropy, dt 0.6: 95 in both modes.
figure: diagnostics_districts_multires.png — Districts, coarse multiresolution level (grid 128), dt 0.2, default tolerances: 123 in both modes.
figure: diagnostics_states_tight.png — States grid 256, dt 0.2, tolerances 0.5 % / 1 %: 112 in both modes.
figure: diagnostics_districts_continuation.png — Districts grid 256, second run at 0.5 % / 1 % on a result converged at 5 % / 20 %: 7 against 13; panel 3 shows the restart limit.
figure: diagnostics_tilted_stall.png — Tilted anisotropy, dt 0.6, `recompute_on_rise=None`: stalls at 130 iterations in both modes.

- **Anisotropy at dt 0.6, districts at default tolerances, states at 0.5 % / 1 %.** No shrink event in the anisotropy and districts runs (the dead band at the default tolerances is 4.1e-3), so the runs are identical to constant dt; the only shrink in the states run is in the final iteration, after the last step.
- **Continuation from a loose result.** The restart limit decides: the fraction falls from 1 to 0.27 in iterations 1 to 6 and stays there until the window ends after iteration 10; the maximum error is flat at about 2.6 to 2.7 % (tolerance 1 %) in iterations 5 to 9, and the run converges at 13 after the limit is lifted. Constant dt oscillates (7.2, 4.3, 8.8, 4.9, 1.8, 3.6 %) and lands at 0.78 % at iteration 7. The limit is proportional to the score (about 2.7 here), which stays far from converged for 10 iterations, so the window of 10 iterations costs more than the first step it protects against.
- **Remaining stall (tilted, dt 0.6, `recompute_on_rise=None`).** Both runs stall at 130 and neither gets below 20 % maximum error; the controller does not fire (no shrink events). The stall comes from the stale field, not from the step size.

### Scenarios that benefit

figure: diagnostics_districts_multires_tight.png — Districts, coarse multiresolution level (grid 128), dt 0.2, tolerances 0.5 % / 1 %: 173 against 157 iterations.
figure: diagnostics_states_tight_none.png — States grid 256, dt 0.2, tolerances 0.2 % / 0.4 %, `recompute_on_rise=None`: 192 against 151.
figure: diagnostics_states_late.png — States grid 256, dt 0.4, unreachable tolerances, dead band as for a 0.4 % max tolerance, stall rule off: late phase.

- **Districts coarse level, 0.5 % / 1 %.** Constant dt oscillates between 1 % and 6 % maximum error and lands below 1 % at iteration 173. The on run shrinks 6 times (final fraction 0.23), the oscillation of the maximum error ends and the run converges at 157.
- **Tight, `recompute_on_rise=None`.** The share of the constant-dt run jumps to 0.8 at each cycle, and its maximum error cycles between about 1 % and 60 %. With the rule, 5 shrinks (fraction 0.20) lower the peaks, and the run converges at 151.
- **Late phase at dt 0.4.** Constant dt alternates between about 1 % and 6 % maximum error for 240 iterations. The rule shrinks 3 times and holds a fraction of 0.21; the maximum error then alternates between about 0.1 % and 0.8 %.

## Considered and dropped: a contested-regions condition

Before #124 the districts multiresolution run at 0.5 % / 1 % and dt 0.2 stalled at every level with the first version of this rule (170, 50, 50 iterations, true maximum error 6.4 %; constant dt: 173 iterations). One region (a thin district about 4 grid cells wide at grid 128) stayed about 10 % off while the others oscillated within 3 %, the oscillation shrank the step, and the stall rule stopped the run. I added a condition that the step shrinks only when the regions with the largest errors (at least 80 % of the largest) oscillate.

The cause turned out to be the ring orientation of the exact rasterizer (fixed in #124, see [exact-ring-orientation](../exact-ring-orientation/index.html)): the polygon of that region had a small self-intersection, reached the rasterizer with the wrong sign and was missing from the density field, so it received no force from its own error. Repairing that polygon alone (an area change of 0.00 %) converged it. With #124 in, the condition costs more than it gains (13 single runs and 5 multiresolution runs, rows in `data/tables_contested_check.md`, script `contested_check.py`):

| | constant dt | dead band only | contested condition (0.8) |
|---|---|---|---|
| sum of iterations over 13 single runs | 2674 | 1497 | 1631 |
| districts multiresolution 0.5 % / 1 %, dt 0.2 | c173 | c157 | c152 |
| districts multiresolution 0.2 % / 0.4 %, dt 0.2 | s270, s50, c3 | s240, c12 | stalls at all three levels |
| districts 256, dt 0.4, 0.5 % / 1 %, `recompute_on_rise=None` | stalls, 62 % | converges, 184 iterations, 0.86 % | stalls, 62 % |
| states 128, 0.1 % / 0.2 %, dt 0.2 | 400, not converged | 74 | 138 |
| states 128, 0.2 % / 0.4 %, dt 0.2, `recompute_on_rise=None` | stalls at 270 | 103 | 182 |

so the condition was dropped; the rule is the dead-band rule described above.

## Further checks of the rule

These were run on the PR branch after the per-iteration diagnostics and with the fixed dead band of 1e-3 that preceded the tied band (with the tied band the tangential dt 0.6 run is identical to constant dt), to test ideas about the skewed error distribution. The scripts are `signed_errors_symlog.py` and `signed_errors_linear.py` for the figures; the other numbers were measured in throwaway scripts and are not regenerated.

figure: signed_errors_tangential.png — Signed relative area error per region and iteration, tangential anisotropy, dt 0.6, `adaptive_dt` off (118 iterations) and on (162), symlog axis (lines colored by target area, dark = small) and heatmap (largest target area at the top).
figure: signed_errors_tangential_linear.png — The same lines on a linear axis, clipped at 40 %.

- **Who oscillates.** In the last 40 iterations before the stop, the peak-to-peak swing per region (linear %) has a median of 5.9 % (constant dt) and 1.6 % (adaptive), a 90th percentile of 34 % and 21 %, a maximum of 47 % (Nebraska, Colorado) and 36.5 %; 18 and 10 of 49 regions swing by more than 10 %. The mean absolute error at the stop is 1.07 % and 0.56 %. The eight smallest regions reach a mean maximum error of 18 % (constant) and 9 % (adaptive), the eight largest 2.5 % and 1.3 %.
- **Who creeps.** DC (0.2 % of the area, about 0.15 grid cells) stays 17 % (constant) and 12.6 % (adaptive) below its target over the last 40 iterations; Kansas 13.5 % above in the constant run. The stopping iteration is set by such regions: at iteration 100 one region is above 10 % for constant dt and five for adaptive; at iteration 118 none against seven.
- **Flips by size.** Flip frequency is unrelated to target area (rank correlation -0.04 to -0.21; smallest and largest quartile both 0.42 in the late cycle of the states), and the share by count (0.39) equals the share by area (0.40). Weighting the share by the error magnitude gives the same first crossing (iterations 85/85, 72/76, 62/63 for horizontal, tangential, tilted, at max errors of 44 to 70 %): the large-error regions are flipping too. Large errors sit in small regions (rank correlation of target area with mean absolute error -0.40 to -0.59), but the flips are not concentrated there.
- **Field recomputes in the tangential run.** All recomputes are on the 10-iteration schedule until iteration 67; from there 14 (constant) and 13 (adaptive) are triggered by `recompute_on_rise`, with intervals of 3 to 6 and 6 to 8 iterations. Both runs do 21 field computations, so the cost is +12 % for +37 % iterations.
- **Cost of the dt 0.6 anisotropy runs** (iterations + 12 x field computations; wall time, minimum of two): horizontal 338 to 369 (+9 %, 0.25 to 0.28 s), tangential 370 to 414 (+12 %, 0.26 to 0.30 s), tilted 275 to 313 (+14 %, 0.23 to 0.24 s).
- **A gamma modulation of the velocity magnitude** (`v * (|v| / vmax)^(g - 1)` after the anisotropy modulator, constant dt) is worse almost everywhere: strong anisotropy at dt 0.2 needs 207/187/162 iterations at g=1 against 276/229/199 at g=1.5 and 400/344/222 at g=2; only tangential at dt 0.6 improves (118 to 106 at g=1.5); the late-phase highest true error of the states at dt 0.2 is 2.0 % at g=1 against 25 % at g=1.5.

## How the rule was chosen

These numbers come from throwaway variants of the branch, measured before #124 and with the fixed band of 1e-3 (the detector and shrink tables are not regenerated) (states at grid 256, every iteration recorded, dt 0.2 unless stated). An earlier version of this page described a rule on the score (halve the step when the score rises by 1 %, recover by 25 % per iteration); the reviewer asked for a trigger that does not share the event of `recompute_on_rise`, a step that never recovers, and the sign of each region's error as the signal. The first design and its comparison with an error-driven step are in git history of the branch `feat/adaptive-step-v1` only.

Detection (logging with the step unchanged, tolerances 1e-6, `recompute_on_rise` 0.01):

| detector | far phase (error above 20 %): mean / max share | late share: mean / std | first shrink | late-phase highest % with control |
|---|---|---|---|---|
| sign differs from the previous iteration | 0.004 / 0.22 | 0.40 / 0.40 | iteration 109 | 0.27 |
| any change in the last 2 iterations | 0.006 / 0.37 | 0.60 / 0.35 | 109 | 0.26 |
| any change in the last 3 iterations (adopted) | 0.006 / 0.37 | 0.81 / 0.03 | 109 | 0.23 |
| any change in the last 4 iterations | 0.007 / 0.39 | 0.82 / 0.02 | 109 | 0.23 |
| sign against the last significant sign, last 2 | 0.011 / 0.61 | 0.75 / 0.35 | 109 | 0.23 |
| sign against 2 iterations ago, last 2 | 0.010 / 0.57 | 0.96 / 0.03 | 109 | 0.23 |

The share swings between about 0.8 and 0 within one iteration (period 2; some regions have period 4), and a window of 3 makes it smooth (std 0.03). Every detector fires 3 iterations before the error first falls below 5 %. Without `recompute_on_rise` the per-iteration detector and the window of 2 reach 0.5 % and 3.6 % (median) while windows of 3 and 4 reach 0.58 % both; the window of 3 is the shortest that is reliable. The dead band skips regions with a small error; keeping the last significant sign (the two "last significant sign" variants) did not change the outcome and raised the far-phase share.

Size of the shrink, window 3, share threshold 0.1, `recompute_on_rise` 0.01 / None (iterations: default tolerances, 0.2 % / 0.4 % at dt 0.2, at dt 0.4; late-phase highest %): fixed halving: 120, 128, 79 / 120, 166, 93; 0.23 / 1.24. Proportional to the error at the first trigger: 114, 121, 72 / 114, 125, 82; 0.31 / 1.10. Multiply by `1 - 0.6 s`: 112, 117, 75 / 112, 132, 82; 0.30 / 1.95. The proportional rules cost fewer iterations at the default tolerances (112 to 114 against 120 for the fixed halving; constant dt takes 112) because a mild trigger shrinks less. The share-based rule needs no reference error and was kept.

Threshold and pause, `1 - 0.6 s`, window 3 (iterations: horizontal 0.6, tangential 0.6, districts grid 128 at the default tolerances; states 0.2 % / 0.4 % at dt 0.2 and 0.4 with `recompute_on_rise` 0.01 / None; late-phase highest %, 0.01 / None). Constant dt: 122, 118, 123; 148, 100 / 192, stalled; 2.0 / 14.5.

| threshold, pause | iterations (default tolerances) | iterations (tight) | late-phase highest % |
|---|---|---|---|
| 0.1, none | 174, 191, 256 | 117, 75 / 132, 82 | 0.30 / 1.95 |
| 0.1, 3 | 169, 203, 163 | 123, 70 / 152, 123 | 0.45 / 3.23 |
| 0.3, none | 165, 166, 153 | 118, 73 / 151, 81 | 0.56 / 4.52 |
| 0.3, 3 (adopted) | 165, 162, 124 | 118, 70 / 152, 122 | 0.68 / 3.75 |
| 0.5, 3 | 148, 123, 123 | 121, 68 / 151, 102 | 0.70 / 20.07 |

At threshold 0.1 regions flip sign while the error is still large (score around 9 to 11 on the anisotropy runs and the districts at grid 128) and several consecutive triggers from the same sign change take the step to the floor; the districts at grid 128 needed 256 iterations. A threshold of 0.3 with a pause of one window costs 124 and keeps most of the late-phase gain; 0.5 is cheaper but leaves 20 % in the stale-field cycle, worse than constant dt.

## Dead band

The band is tied to the max tolerance, `c * log2(1 + max_tol)`, so a tight tolerance sees the sign of smaller errors. A fixed band of 1e-3 (the first version) cost iterations at the default tolerances (the dt 0.6 anisotropy runs +35 to 40 %), a band of 1e-2 or more never fires (identical to constant dt), and smaller bands (0 to 1e-4) give a calmer late phase and fewer iterations at tight tolerances but cost iterations at the default tolerances. `dead_band_sweep.py` compares constant dt, the fixed band and c = 0.01, 0.03, 0.1 (rows in `data/tables_dead_band.md`); c = 0.03 was first chosen on 11 cases, and the held-out cases below were not used for the choice. Sum of iterations (all converge unless noted):

| set | constant dt | fixed 1e-3 | c 0.01 | c 0.03 | c 0.1 |
|---|---|---|---|---|---|
| 11 original cases | 1406 | 1476 | 1454 | 1362 | 1339 |
| 15 held-out fresh runs (anisotropy at dt 0.4 and 0.8, states at grids 128 and 512 at dt 0.4, districts at dt 0.2 and 0.4, states 128 and 256 at 1 % / 2 % and 0.1 % / 0.2 %); constant dt does not converge in 2 of them (400 and 260 iterations) | 1994 | 1743 | 1689 | 1553 | 1509 |
| held-out multiresolution (states, districts) and continuations | 316 | 210 | 214 | 210 | 209 |
| districts multiresolution at 3 tolerances (1 % / 2 %, 0.5 % / 1 %, 0.2 % / 0.4 %) and states 0.2 % / 0.4 % | 914 | 599 | 721 (one stall) | 736 (one stall) | 644 |
| districts grid 128, 4 tolerances x 4 dt | 2745 | 2952 | 3052 | 2766 | 2724 |

Held-out cases where the choice matters (iterations):

| case | constant dt | fixed 1e-3 | c 0.03 | c 0.1 |
|---|---|---|---|---|
| horizontal dt 0.8 | 96 | 150 | 118 | 96 |
| tangential dt 0.8 | 109 | 150 | 117 | 109 |
| tilted dt 0.8 | 76 | 124 | 90 | 86 |
| states 128, 0.1 % / 0.2 %, dt 0.2 | 400 (not converged) | 118 | 74 | 74 |
| states 256, 0.1 % / 0.2 %, dt 0.2 | 260 (stalled) | 122 | 121 | 121 |
| states 256, 0.2 % / 0.4 %, dt 0.2 | 148 | 118 | 119 | 118 |
| multires states 0.5 % / 1 % | 94 | 70 | 72 | 70 |

Late phase (unreachable tolerance, band as for 0.4 %, median / highest true max error over the last 50 of 300 iterations, states grid 256):

| recompute_on_rise | dt | constant dt | fixed 1e-3 | c 0.01 | c 0.03 | c 0.1 | c 0.3 |
|---|---|---|---|---|---|---|---|
| 0.01 | 0.2 | 0.81 / 2.00 | 0.27 / 0.68 | 0.11 / 0.30 | 0.11 / 0.23 | 0.11 / 0.32 | 0.30 / 0.67 |
| 0.01 | 0.4 | 2.37 / 6.22 | 0.23 / 0.57 | 0.23 / 0.50 | 0.22 / 0.54 | 0.38 / 0.81 | 0.24 / 0.64 |
| None | 0.2 | 5.32 / 14.54 | 1.36 / 3.75 | 0.70 / 1.86 | 0.68 / 1.85 | 0.48 / 1.44 | 1.79 / 4.26 |
| None | 0.4 | 8.72 / 19.55 | 1.56 / 4.35 | 6.45 / 15.40 | 5.55 / 14.46 | 1.13 / 3.18 | 1.42 / 4.06 |

Choice: c = 0.1. It takes the same iterations as constant dt on all default-tolerance cases but one (tilted at dt 0.8: 76 against 86), keeps the tight-tolerance gains (32 of 32 converge), has the lowest sums on every set, and is the only factor that converges the districts multiresolution at all three tolerances (c = 0.01 and 0.03 stall at 0.2 % / 0.4 %); c = 0.03 costs more at the default tolerances (tilted dt 0.8: 90; dt 0.6 anisotropy 129 / 128 / 108 against 122 / 118 / 95 for constant dt) and c = 0.01 and 0.03 are poor without `recompute_on_rise` at dt 0.4 (14 to 15 % highest error). c = 0.3 has the highest amplitude at dt 0.2 with the default recompute. The held-out cases agree with the original choice in direction (tied band against fixed band). Before #124 the districts multiresolution run at 0.5 % / 1 % stalled with c = 0.1; it converges now (157 iterations).

## Design alternatives and trade-offs

1. Default `adaptive_dt=False`: no change for anyone; users with tight tolerances or large presets opt in. The cost of default-on is now: 6 more iterations on the continuation from a loose result, a 3 % cost increase on two tight runs, and a stopping point that differs from constant dt when the rule fires (within the tolerance, not necessarily as close to the target as a constant step that lands low).
2. Let the step recover slowly: not done, as the reviewer asked for a decrease-only step.
3. Make the shrink depend on the error magnitude: measured earlier (with the fixed band), a proportional rule saves iterations at default tolerances (3 to 8 %) but needs a reference error; the share rule was kept.
4. Expose the constants (band factor): not justified.

## Not verified or not changed

- Not tested: grid 1024, the `"center"` rasterizer, `prescale_components`; the districts at grid 512 (stall in both modes at 0.5 % / 1 %) were dropped from the comparison; the counties on top of #124. The dead band factor was chosen on 11 cases and checked on about 40 more (fresh, multiresolution, continuation, late phase); every case set is small.
- A restart from a loose result on the districts at grid 256 is slower (7 against 13 iterations).
- Existing tests pin behavior of the constant step (a deliberately diverging step, the best-iterate bookkeeping, the rise count of the recompute rule, the accuracy gain of exact rasterization at the stopping point) and now set `adaptive_dt=False`; with the control a run stops after a shrunk step at an error well inside the tolerance but not necessarily as low as a constant step that lands low.
