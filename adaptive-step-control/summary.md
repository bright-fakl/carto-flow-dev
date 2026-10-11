---
pr: 123
url: https://github.com/bright-fakl/carto-flow/pull/123
issue: 94, 109
title: Adaptive step size for the flow cartogram
description: MorphOptions.adaptive_dt (default on) shrinks the step when the regions' area errors alternate in sign and limits the first steps of a run that starts near the target. The sign of an error counts above a dead band tied to the max tolerance. 32 of 32 tight-tolerance runs converge against 17 (with and without recompute_on_rise), the late-phase oscillation of the true maximum error drops by a factor of 3 to 10, a continuation from a converged cartogram takes 1 iteration instead of 4, and all 12 runs at the default tolerances take the same iterations as constant dt. One multiresolution run (districts, 0.5 % / 1 %) stalls where constant dt converges.
kind: pr
topic: flow
branch: feat/adaptive-step
base: main
date: 2026-10-12 15:00
related: exploration-adaptive-step, exact-density-coverage, flow-convergence-synthesis
before: main @ 71b5157 (constant dt; reproduced with adaptive_dt=False)
after: feat/adaptive-step @ 25674d6
inputs: US states (49 incl. DC) and congressional districts (432), bundled; the three strong-anisotropy runs of the adaptive-recompute page (states, preset_balanced values, area_scale 1e-6, DirectionalTensor horizontal / tangential / tilted); 3,108 counties (prepared set, not bundled). MorphOptions defaults except where stated (dt 0.2, recompute_every 10, recompute_on_rise 0.01, exact rasterization, stall rule on, n_iter 400); NUMBA_NUM_THREADS=8, runs sequential. True error is the output area against the population share of the total output area. Cost = iterations + field recomputes x cost of one recompute in plain steps (states 9, 12, 24 at grids 128, 256, 512; districts 18, 21, 23; measured on adaptive-recompute-experiment).
---

`make_figures.py` runs every experiment below and writes the figures and `data/tables.md` (all tables, one row per run); `REUSE=1` reuses the stored `data/*.json`. The counties part runs when `COUNTIES_PARQUET` points at a GeoDataFrame file with `GEOID`, `total_votes` and `geometry`. `diagnostic_plots.py` writes the diagnostics_*.png figures and `dead_band_sweep.py` the dead band tables (`data/tables_dead_band.md`). The numbers in "How the rule was chosen" come from throwaway variants of the branch and are not regenerated; they were measured with the fixed dead band of 1e-3 that preceded the tied band.

## What changes

The step moves the fastest point `dt` grid cells whatever the error (`dt_prime = dt * min(dx, dy) / max_v`; the field's strength cancels). Near the target that is more than the correction asks for: the area of each region alternates around its target with an amplitude proportional to `dt`, and a tolerance below the amplitude is met only when the oscillation dips below it ([exact-density-coverage](../exact-density-coverage/index.html), section "Late phase").

`MorphOptions.adaptive_dt` (default `True`; `False` is the constant step of main) multiplies `dt` by a fraction `f` in [1/8, 1]:

- **Sign changes.** A region is inverted if the sign of its area error (current area against target, as `log2` of the ratio) changed in any of the last 3 iterations; a change is only recorded between two iterations in which the region's error exceeds a dead band of `0.1 * log2(1 + max_tol)` (4.1e-3 at the default tolerances, 4.3e-4 at 0.5 % / 1 %, 1.4e-4 at 0.2 % / 0.4 %; regions inside the dead band are skipped, the last significant sign is not kept). When the share `s` of inverted regions exceeds 30 %, `f` is multiplied by `1 - 0.6 s`, and the next 3 iterations cannot shrink it again. `f` never grows back. Apart from the dead band the rule uses neither the score nor the tolerances, and it does not depend on `recompute_on_rise`.
- **Restart.** In the first `max(recompute_every, 10)` iterations `f` is also limited to the score of the current state (for the first step: of the input geometries) divided by 10, not below 1/8. A run that starts far from the target (score above 10) is not affected.

The constants (3 iterations, 0.1 for the dead band, 30 %, 0.6, 1/8, 10) are fixed in `stepsize.py`; the only option is the switch.

figure: inversion_share.png — Share of regions with a sign change in the last 3 iterations (orange) against the true maximum area error (blue, right axis), states at grid 256, dt 0.2, constant dt, every iteration recorded. The share is about 0 while the error falls from 1700 % to 10 % and 0.75 to 0.9 once the oscillation starts around iteration 112.

## Late phase

figure: late_phase.png — Left: true maximum area error at each of the last 80 of 300 iterations, states at grid 256, dt 0.2, tolerances 1e-6 (unreachable), dead band as for a max tolerance of 0.4 %, stall rule off, every iteration recorded (default `recompute_on_rise`). Constant dt alternates between 0.3 % and 2.0 %; adaptive_dt between 0.1 % and 0.3 %. Right: highest and median over the last 50 iterations against dt.

True maximum error over the last 50 of 300 iterations, with every iteration recorded and computed from the geometry of each snapshot (the cycle has period 2, so sampling every n-th iteration is not representative). The tolerances of these runs are unreachable (1e-6), so the dead band is set explicitly as for a max tolerance of 0.4 % (`0.1 * log2(1.004)` = 2.9e-4); with the band of a 1e-6 tolerance the rule would see signs of errors far below any cycle.

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

The highest error drops by a factor of 3 to 10 (2.0 to 0.32 % at dt 0.2). Without `recompute_on_rise` the field is stale for up to 10 iterations and the constant-dt cycle is much larger (14 to 20 %); the rule reduces it by a factor of 3 to 6, and what remains is the stale field, not the step. Against the fixed band of 1e-3 the amplitude is lower in six of the eight rows (0.68 to 0.32 % at dt 0.2) and higher in two (states dt 0.4 with the default recompute: 0.81 against 0.57 %; districts without `recompute_on_rise`: 4.03 against 3.90 %).

figure: tight_traces.png — Score per iteration, states at grid 256, tolerances 0.2 % / 0.4 %, stall rule off. Constant dt oscillates between about 1.3 and 20 and converges when it happens to dip (148 and 100 iterations); with adaptive_dt the oscillation decays after the first shrinks (118 and 70 iterations).

## Tight tolerances

32 runs: states at grids 128, 256, 512 and districts at grid 256, tolerances (mean / max) 0.2 % / 0.4 % and 0.5 % / 1 %, dt 0.2 and 0.4, `recompute_on_rise` 0.01 and None (rows in `data/tables.md`).

| | constant dt converges | adaptive_dt converges |
|---|---|---|
| `recompute_on_rise` 0.01 (16 runs) | 10 | 16 |
| `recompute_on_rise` None (16 runs) | 7 | 16 |
| total | 17 of 32 | 32 of 32 |

Of the 17 runs where both converge the median cost ratio is 0.79 (range 0.20 to 1.10); one costs more than 5 % more (states at grid 256, 0.5 % / 1 %, dt 0.4, default recompute: 64 iterations (cost 160) against 68 (176)). States at grid 128, 0.5 % / 1 %, dt 0.2: 182 iterations (cost 776) against 71 (152). The true maximum error of the output is equal or lower in 27 of the 32 runs; in the five others it is higher but within the tolerance (0.20 against 0.34 %; 0.85 against 0.95 %; 0.23 against 0.24 %; 0.97 against 0.98 %; 0.85 against 0.99 %).

figure: cost_ratio.png — Cost with adaptive_dt over cost with constant dt per run (log scale). Left: the 12 runs at the default tolerances. Right: the 32 tight-tolerance runs. Triangles mark runs where only adaptive_dt converged (their ratio compares against a stalled or capped constant-dt run, so it understates the gain).

## Runs at the default tolerances

12 runs; wall time is the minimum of two. Iterations with constant dt against adaptive_dt:

| input | grid | dt | iterations, constant dt | iterations, adaptive_dt | wall s, constant dt / adaptive_dt |
|---|---|---|---|---|---|
| states | 128 | 0.2 | 62 | 62 | 0.14 / 0.14 |
| states | 256 | 0.2 | 112 | 112 | 0.29 / 0.21 |
| states | 512 | 0.2 | 214 | 214 | 0.50 / 0.52 |
| districts | 256 | 0.2 | 145 | 145 | 0.54 / 0.54 |
| states | 256 | 0.4 | 62 | 62 | 0.15 / 0.15 |
| districts | 256 | 0.4 | 81 | 81 | 0.40 / 0.41 |
| horizontal | 256 | 0.2 | 207 | 207 | 0.34 / 0.35 |
| tangential | 256 | 0.2 | 187 | 187 | 0.31 / 0.31 |
| tilted | 256 | 0.2 | 162 | 162 | 0.27 / 0.28 |
| horizontal | 256 | 0.6 | 122 | 122 | 0.26 / 0.26 |
| tangential | 256 | 0.6 | 118 | 118 | 0.27 / 0.28 |
| tilted | 256 | 0.6 | 95 | 95 | 0.22 / 0.22 |

All 12 runs are identical to constant dt in iterations, recomputes and result: at the default tolerances the dead band (4.1e-3) hides the sign changes of the approach, so the rule did not fire in the runs examined in the diagnostics. Wall times agree within noise (the 0.29 / 0.21 s of the states at grid 256 is the same 112 iterations). The held-out cases of the dead band section (anisotropy at dt 0.4 and 0.8, states at grids 128 and 512 at dt 0.4, districts at dt 0.2 and 0.4) are identical too, except tilted at dt 0.8 (76 against 86 iterations).

## Continuation from an existing geometry

A second `CartogramWorkflow.morph` on the result of a first run, tolerances 0.5 % / 1 % (rows in `data/tables.md`):

| input | grid | first run | constant dt: iterations (cost), score after iteration 1 | adaptive_dt: iterations (cost), score after iteration 1 |
|---|---|---|---|---|
| states | 256 | converged at 0.5 % / 1 % | 4 (28), 2.5 | 1 (13), 0.4 |
| states | 512 | converged at 0.5 % / 1 % | 4 (52), 2.7 | 1 (25), 0.3 |
| districts | 256 | converged at 0.5 % / 1 % | 4 (46), 2.3 | 1 (22), 0.3 |
| states | 256 | converged at 5 % / 20 % | 92 (620), 1.6 | 3 (27), 1.5 |
| states | 512 | converged at 5 % / 20 % | 4 (52), 8.0 | 3 (27), 8.0 |
| districts | 256 | converged at 5 % / 20 % | 7 (70), 7.0 | 13 (97), 7.0 |

The restart limit is needed. In a throwaway variant without it (measured with the fixed band of 1e-3) (states, grid 128, tolerances 0.5 % / 1 %, converged first run) the second run took 19 iterations (score 8.9, 18.7, 13.9 after the first three iterations) against 4 with constant dt and 1 with the limit: the first step undoes the convergence before any sign change can be seen, and the sign rule then shrinks the step for a run that has to converge again.

The districts at grid 256 started from a loose result are slower with adaptive_dt (7 against 13 iterations): the score of the start is 7, so the limit takes 70 % of the step although a full step was right.

figure: restart.png — Iterations of the second run on the output of a first run.

### Multiresolution

`morph_multiresolution(min_resolution=128, levels=3)`, 300 iterations per level; the loop stops at the first converged level (cost over the levels run):

| input | tolerances | dt | constant dt | adaptive_dt |
|---|---|---|---|---|
| states | default | 0.2 | 128: converged 63 it; cost 126 | same |
| states | default | 0.4 | 128: converged 39; cost 93 | same |
| states | 0.5 % / 1 % | 0.2 | 128: converged 94; cost 292 | 128: converged 70; cost 151 |
| states | 0.5 % / 1 % | 0.4 | 128: converged 45; cost 126 | 128: converged 49; cost 112 |
| districts | default | 0.2 | 128: converged 123; cost 447 | same |
| districts | default | 0.4 | 128, 256, 512: stalled (120, 50, 50 it); cost 1317 | same stalls; cost 1317 |
| districts | 0.5 % / 1 % | 0.2 | 128: converged 173; cost 947 | 128, 256, 512: stalled (170, 50, 50); cost 1504; true max 6.4 % |
| districts | 0.5 % / 1 % | 0.4 | 128, 256, 512: stalled (140, 50, 50 it); cost 1499 | same stalls (150, 50, 50); cost 1375 |

Equal or cheaper in six of the eight runs, one costs more with the same outcome (states, 0.5 % / 1 %, dt 0.4: 45 against 49 iterations, cost 126 against 112), and one fails: the districts at 0.5 % / 1 % and dt 0.2 converge at 173 iterations with constant dt but stall at 170 on the coarse level with the control (see the diagnostics: the maximum error is flat at about 10 % after iteration 140). The districts at dt 0.4 stall at every level in both modes (sub-cell plateau; the step control does not address it). The stall of the coarse districts level moves with the dead band factor: see "Dead band".

## recompute_on_rise

The tables above use both settings where it matters. The one false stall of an earlier design (states, dt 0.2, tolerances 0.2 % / 0.4 %, `recompute_on_rise=None`) does not occur: adaptive_dt converges in 151 iterations, constant dt in 192.

| input | dt | tolerances | recompute_on_rise | constant dt | adaptive_dt |
|---|---|---|---|---|---|
| states | 0.2 | 0.2 / 0.4 % | 0.01 | converged, 148 it, cost 508 | converged, 118, 286 |
| states | 0.2 | 0.2 / 0.4 % | None | converged, 192, 432 | converged, 151, 343 |
| states | 0.4 | 0.2 / 0.4 % | 0.01 | converged, 100, 412 | converged, 70, 178 |
| states | 0.4 | 0.2 / 0.4 % | None | stalled, 210, 462 | converged, 122, 278 |
| tilted | 0.6 | default | 0.01 | converged, 95, 275 | converged, 95, 275 |
| tilted | 0.6 | default | None | stalled, 130, 286 | stalled, 130, 286 |
| horizontal | 0.6 | default | 0.01 | converged, 122, 338 | converged, 122, 338 |
| horizontal | 0.6 | default | None | converged, 164, 368 | converged, 164, 368 |

Tilted at dt 0.6 without `recompute_on_rise` stalls in both modes at the same iteration (the rule does not fire there).

## Counties

3,108 counties, grid 256, 300 iterations (`data/tables.md`): constant dt and adaptive_dt give the same run (stalled at 210 iterations, best iteration 169, true mean 49.6 %, max 5018 %). The counties do not respond (targets far below one cell; not a step problem).

## Per-iteration diagnostics

`diagnostic_plots.py` records every iteration of ten scenarios, with the settings of the tables above, for adaptive_dt off and on. Panels, same x axis: (1) true maximum area error from the geometry of each snapshot with the tolerance and the stopping iteration (dotted); (2) share of regions whose error sign changed in the last 3 iterations (the controller's detection and dead band), the threshold 0.3, and the shrink events (filled triangles: on run; open triangles: events the controller would have produced on the constant-dt run); (3) fraction of dt: actual for the on run, predicted for the constant-dt run by replaying the controller on its recorded errors (open loop); (4) true mean area error with its tolerance.

### Scenarios where the rule is inactive or costs

figure: diagnostics_horizontal_dt06.png — Horizontal anisotropy, dt 0.6, default tolerances: 122 iterations in both modes.
figure: diagnostics_tangential_dt06.png — Tangential anisotropy, dt 0.6: 118 in both modes.
figure: diagnostics_tilted_dt06.png — Tilted anisotropy, dt 0.6: 95 in both modes.
figure: diagnostics_districts_multires.png — Districts, coarse multiresolution level (grid 128), dt 0.2, default tolerances: 123 in both modes.
figure: diagnostics_states_tight.png — States grid 256, dt 0.2, tolerances 0.5 % / 1 %: 112 in both modes.
figure: diagnostics_districts_continuation.png — Districts grid 256, second run at 0.5 % / 1 % on a result converged at 5 % / 20 %: 7 against 13; panel 3 shows the restart limit.
figure: diagnostics_districts_multires_tight.png — Districts, coarse multiresolution level (grid 128), dt 0.2, tolerances 0.5 % / 1 %: constant dt converges at 173, adaptive_dt stalls at 170.
figure: diagnostics_tilted_stall.png — Tilted anisotropy, dt 0.6, `recompute_on_rise=None`: stalls at 130 iterations in both modes.

- **Anisotropy at dt 0.6, districts coarse level, tilted stall.** With the dead band at 4.1e-3 the controller never shrinks the step in these runs (0 shrinks, fraction 1 throughout), and the runs are identical to constant dt. Before the dead band was tied to the tolerance the share crossed 0.3 while the maximum error was still 3 to 5 times the tolerance, 5 to 8 shrinks took the fraction to 0.14 to 0.33, and the runs needed 35 to 40 % more iterations.
- **States, 0.5 % / 1 %.** Identical to constant dt (112 iterations): the only shrink event of the on run is in the final iteration, after the last step, so it has no effect (the earlier design with the fixed band shrank at iteration 110, when the maximum error was about 20 times the tolerance, and needed 118 iterations).
- **Continuation from a loose result.** The on run has no shrink (the share stays below 0.19); all of the difference comes from the restart limit. The fraction falls from 1 to 0.27 in iterations 1 to 6 and stays there until the window ends after iteration 10; the maximum error is flat at about 2.6 to 2.7 % (tolerance 1 %) in iterations 5 to 9, and the run converges at 13 after the limit is lifted (1.4 %, 3.2 %, 0.6 % in iterations 11 to 13). Constant dt oscillates (7.2, 4.3, 8.8, 4.9, 1.8, 3.6 %) and lands at 0.78 % at iteration 7. The limit is proportional to the score (about 2.7 here), which stays far from converged for 10 iterations, so the window of 10 iterations costs more than the first step it protects against.
- **Districts coarse level at 0.5 % / 1 % (the stall).** The share first crosses 0.3 at iteration 109 (maximum error about 30 %, tolerance 1 %); 6 shrinks bring the fraction to 0.23 by iteration 136. From iteration 140 the maximum error of the on run is flat at about 10 % with the share between 0 and 0.2 (no oscillation), and the stall rule (4 windows without progress) stops it at 170. Constant dt keeps oscillating between about 1 % and 6 % with the share at 0.6 to 0.85 and lands below 1 % at iteration 173. The small districts (sub-cell regions) keep the maximum error at about 10 % while the step is small, and the oscillation of the constant run is what reaches the tolerance; this is the same plateau that stalls the districts at dt 0.3 and above in every mode.

### Scenarios that benefit

figure: diagnostics_states_tight_none.png — States grid 256, dt 0.2, tolerances 0.2 % / 0.4 %, `recompute_on_rise=None`: 192 against 151.
figure: diagnostics_states_late.png — States grid 256, dt 0.4, unreachable tolerances, dead band as for a 0.4 % max tolerance, stall rule off: late phase.

- **Tight, `recompute_on_rise=None`.** The share of the constant-dt run jumps to 0.8 at each cycle (iterations 112, 132, 150 to 190), and its maximum error cycles between about 1 % and 60 %. With the rule, 5 shrinks (fraction 0.20) lower the peaks to about 35 %, 10 % and 10 %, and the run converges at 151 on a dip below 0.4 %; the predicted fractions on the constant-dt run reach 0.125, so the controller would have shrunk more there than it did on the run it controlled.
- **Late phase at dt 0.4.** Constant dt alternates between about 1 % and 6 % maximum error for 240 iterations with the share at 0.8 to 1. The rule shrinks 3 times between iterations 57 and 67 and holds a fraction of 0.21; the maximum error then alternates between about 0.1 % and 0.8 %, and the low end keeps falling (0.003 % at iteration 300). After the shrinks the share falls from 0.3 to 0 over 100 iterations, so the remaining period-2 oscillation of the maximum error is not a sign alternation of the regions.

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

These numbers come from throwaway variants of the branch (states at grid 256, every iteration recorded, dt 0.2 unless stated). An earlier version of this page described a rule on the score (halve the step when the score rises by 1 %, recover by 25 % per iteration); the reviewer asked for a trigger that does not share the event of `recompute_on_rise`, a step that never recovers, and the sign of each region's error as the signal. The first design and its comparison with an error-driven step are in git history of the branch `feat/adaptive-step-v1` only.

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

The fixed band of 1e-3 was a compromise: a band of 1e-2 or more never fires (identical to constant dt); a smaller band (0 to 1e-4; this sweep was run by the reviewer) gives a calmer late phase and fewer iterations at tight tolerances but costs iterations at the default tolerances (tangential at dt 0.6: 185 against 162 with the fixed band; districts grid 128: 149 to 158 against 124). The band is therefore tied to the max tolerance, `c * log2(1 + max_tol)`. `dead_band_sweep.py` compares constant dt, the fixed band and c = 0.01, 0.03, 0.1 (rows in `data/tables_dead_band.md`). c = 0.03 was first chosen on 11 cases; the held-out cases below were not used for the choice. Iterations (status c converged, s stalled; true max error % of the output in `data/tables_dead_band.md`):

| set | constant dt | fixed 1e-3 | c 0.01 | c 0.03 | c 0.1 |
|---|---|---|---|---|---|
| 11 original cases, sum of iterations | 1406 | 1476 | 1454 | 1362 | 1339 |
| 15 held-out fresh runs (anisotropy at dt 0.4 and 0.8, states at grids 128 and 512 at dt 0.4, districts at dt 0.2 and 0.4, states 128 and 256 at 1 % / 2 % and 0.1 % / 0.2 %), sum | 1994 | 1743 | 1689 | 1553 | 1509 |
| held-out multiresolution (states, districts) and continuations, sum | 316 | 210 | 214 | 212 | 209 |
| of which constant dt does not converge | 2 of 15 (400 and 260 iterations) | | | | |

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

Late phase (unreachable tolerance, band as for 0.4 %, highest true max error over the last 50 of 300 iterations, states grid 256): c = 0.03 / 0.1 / 0.3: 0.23 / 0.32 / 0.67 % (dt 0.2, rise on), 0.54 / 0.81 / 0.64 % (dt 0.4, rise on), 1.85 / 1.44 / 4.26 % (dt 0.2, rise None), 14.5 / 3.2 / 4.1 % (dt 0.4, rise None). c = 0.3 has the highest amplitude at dt 0.2; c = 0.1 is the lowest of the three in the two stale-field rows and higher than c = 0.03 only at dt 0.4 with the default recompute.

Choice: c = 0.1. It takes the same iterations as constant dt on all default-tolerance cases but one (tilted at dt 0.8: 76 against 86), keeps the tight-tolerance gains (32 of 32 converge), and has the lowest sums on both the original and the held-out cases (1339 against 1362 and 1509 against 1553 for c = 0.03). The held-out cases agree with the original choice in direction (tied band against fixed band) but c = 0.03 costs more at the default tolerances (tilted dt 0.8: 90; dt 0.6 anisotropy 129 / 128 / 108 against 122 / 118 / 95 for constant dt).

Where the tied band is worse: the coarse level of a districts multiresolution run is sensitive. Constant dt and the fixed band converge in all three tolerances tested (1 % / 2 %, 0.5 % / 1 %, 0.2 % / 0.4 %); each tied factor stalls in exactly one (c = 0.1 at 0.5 % / 1 %: 270 iterations, 6.4 % true maximum error; c = 0.05 at 1 % / 2 %; c = 0.03 and 0.01 at 0.2 % / 0.4 %). On the districts at grid 128 alone (4 tolerances, 4 dt values) the same 8 of 16 runs converge in every mode, and iterations are within 5 % of constant dt in total (c = 0.1: 2914, constant dt: 2776), so the failures are not a general effect; they are stalls on a sub-cell plateau that depend on the stopping point of an oscillation.

## Design alternatives and trade-offs

1. Default `adaptive_dt=False`: no change for anyone; users with tight tolerances or large presets opt in. The cost of default-on is now small: no change in the 12 default-tolerance runs (and 9 of 10 held-out default-tolerance ones), +13 % in iterations on tilted at dt 0.8, +6 iterations on the continuation from a loose result, and one stalled districts multiresolution run.
2. Let the step recover slowly: not done, as the reviewer asked for a decrease-only step. With the tied band the early permanent shrink at default tolerances no longer occurs in the measured runs.
3. Make the shrink depend on the error magnitude: measured above (with the fixed band), a proportional rule saves iterations at default tolerances (3 to 8 %) but needs a reference error; the share rule was kept.
4. Expose the constants (including the band factor): not justified; c = 0.03 to 0.1 give the same tight-tolerance results.

## Not verified or not changed

- Not tested: grid 1024, the `"center"` rasterizer, `prescale_components`; the districts at grid 512 (stall in both modes, sub-cell plateau) were dropped from the comparison. The dead band factor was chosen on 11 cases and checked on about 40 more (fresh, multiresolution, continuation, late phase); every case set is small.
- A restart from a loose result on the districts at grid 256 is slower (7 against 13 iterations); the districts multiresolution at 0.5 % / 1 % and dt 0.2 stalls with the control (see "Dead band").
- Existing tests pin behavior of the constant step (a deliberately diverging step, the best-iterate bookkeeping, the rise count of the recompute rule, the accuracy gain of exact rasterization at the stopping point) and now set `adaptive_dt=False`; with the control a run stops after a shrunk step at an error well inside the tolerance but not necessarily as low as a constant step that lands low (states at grid 256 with tight tolerances: 0.2 % / 0.4 % converged outputs have a true maximum error of 0.1 to 0.4 % in both modes).
