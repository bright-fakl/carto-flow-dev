---
issue: 75, 109
title: GSM step scale in the flow loop
description: Does replacing carto-flow's constant per-step scale with the GSM scale 1/rho(x,t), inside the existing flow loop, converge faster or more stably? The spatial pattern alone (B1) is slower, adds self-intersections and keeps the tail; the physical magnitude (B2, B4) cuts the cost 3 to 5 times on states and fixes the multires plateau, but needs a per-step cap, stalls on districts (B4) and fails on counties like the baseline. Precomputing the field (B3) is faster only when vertices outnumber grid cells.
branch: investigate/gsm-scale
base: fix/stall-detection
date: 2026-10-09 18:30
before: fix/stall-detection @ 8441681
after: investigate/gsm-scale @ bfb4253 (prototype, not for merging)
updated: 2026-10-09 22:15
inputs: US states (49 incl. DC), congressional districts (432), 3,108 counties (prepared set, ESRI:102008, total_votes, area_scale 1e-6), the three strong-anisotropy runs of the adaptive-recompute page (preset_balanced settings, area_scale 1e-6), the multiresolution coarse level of the states; MorphOptions defaults of fix/stall-detection (stall rule on, recompute_every 10, dt 0.2), n_iter 400 (counties 300), each run with refresh_on_rise off (None) and on (0.01); NUMBA_NUM_THREADS=4
kind: exploration
topic: flow
status: on-hold
related: exploration-overview
---

An investigation, not a change. The prototype adds four `MorphOptions` fields (`step_scale_mode`, `step_scale_floor`, `step_scale_precompute`, `step_scale_max_cells`) and a module `step_scale.py`; the default (constant) mode reproduces the stored baseline trace for states 256 (113 iterations). One run per cell; load average 0.3 to 1.6; wall times are indicative and the cost model (iterations plus recomputes times the ratio) is the primary metric. `tables.md` has every variant; the patch is in `code/gsm_scale.patch`.

## Variants (all inside the carto-flow loop, applied after the velocity modulators)

| name | mode | per step |
|---|---|---|
| A | constant | current: the fastest grid point moves dt cells |
| B1 | gsm_normalized | velocity times `rho_mean / rho(x,t)`, renormalized every step so the fastest grid point moves dt cells (pattern only) |
| B2 | gsm_physical | raw velocity times `1 / (recompute_every * rho(x,t))`; path length 1 per round, as in the GSM preview prototype |
| B3 | step_scale_precompute | grid field `W_k = v f_k` per step, one interpolation (applies to B1 and B2) |
| B4ii | integral_normalized / integral_physical | closed-form round field `W = v ln(rho_mean/rho0) / (rho_mean - rho0)` applied in `recompute_every` sub-steps |
| B4i | integral_oneshot | the same field applied once per round, with a recompute every iteration |

`rho(x,t)` is clamped below at `floor * rho_mean` (default 0.02; 0.01 and 0.1 tested), and `t = k / recompute_every` for step k of a round. `step_scale_max_cells` caps the displacement per vertex per step: 1 cell for B2 and B4ii physical, 3 cells for B4i. Without a cap, B4i produces NaN coordinates on 6 of 11 case/grid combinations, and B2 and B4ii stall on districts and counties.

## Results

figure: convergence_states.png — States at grids 128, 256 and 512 and the multiresolution coarse level; refresh off on top, on below.
figure: convergence_anisotropy.png — The three strong-anisotropy runs.
figure: convergence_districts_counties.png — Districts at 256 and 512, counties at 256 and 512.

Cost is iterations plus recomputes times the ratio (states 128/256/512: 9/12/24; districts 256/512: 21/23; counties 256/512: 47.5/28.5). Runs stop at the first score below 1, so the mean error is a stopping tolerance. "off / on" is refresh_on_rise off / on.

| case | variant | it | rec | cost | mean % | max % | invalid | rises below 20 |
|---|---|---|---|---|---|---|---|---|
| states 256 | A | 113 | 12 | 257 | 0.31 | 4.4 | 0 | 0 |
| | B1 | 135 | 14 | 303 | 0.83 | 3.8 | 6 | 0 |
| | B3 on B1 | 130 | 13 | 286 | 2.4 | 9.1 | 2 | 0 |
| | B2 (cap 1) | 34 | 4 | 82 | 0.62 | 8.4 | 6 | 0 |
| | B3 on B2 | 29 | 3 | 65 | 0.90 | 7.8 | 5 | 0 |
| | B4ii normalized | 117 | 12 | 261 | 1.9 | 9.0 | 3 | 0 |
| | B4ii physical (cap 1) | 27 | 3 | 63 | 1.0 | 9.9 | 4 | 0 |
| | B4i one step (cap 3) | 6 | 6 | 78 | 0.31 | 2.5 | 10 | 0 |
| states 512 | A | 214 | 22 | 742 | 0.51 | 7.3 | 0 | 0 |
| | B1 | 270 | 27 | 918 | 0.83 | 9.0 | 21 | 0 |
| | B2 (cap 1) | 39 | 4 | 135 | 0.67 | 7.0 | 6 | 0 |
| | B4ii physical (cap 1) | 38 | 4 | 134 | 0.79 | 9.2 | 6 | 0 |
| | B4i one step (cap 3) | 10 | 10 | 250 | 0.19 | 1.5 | 10 | 0 |
| states 128 | A | 63 | 7 | 126 | 1.19 | 7.8 | 0 | 0 |
| | B1 | 103 | 11 | 202 | 1.2 | 4.2 | 0 | 2 (off), 1 (on) |
| | B2, B4ii | stalled at 60 (score 13.6) | 6 | 114 | 41 | 232 | 3 | 0 |
| | B4i one step (cap 3) | 5 | 5 | 50 | 0.65 | 5.4 | 18 | 0 |
| multires coarse | A | 100, stalled | 10 | 190 | 28.7 | 264 | 1 | 0 |
| | B1 | 91 | 10 | 181 | 0.58 | 6.5 | 10 | 0 |
| | B2 (cap 1) | 71 | 8 | 143 | 0.38 | 8.8 | 23 | 0 |
| | B4ii normalized | 64 | 7 | 127 | 2.4 | 8.0 | 2 | 0 |
| | B4ii physical (cap 1) | 53 / 38 | 6 / 5 | 107 / 83 | 0.4 / 0.7 | 9.7 | 14 | 5 / 1 |
| | B4i one step (cap 3) | 8 | 8 | 80 | 0.51 | 8.3 | 22 | 0 |
| horizontal 256 | A | 245 / 233 | 25 / 27 | 545 / 557 | 1.0 / 1.3 | 8.9 | 0 | 17 / 9 |
| | B1 | 251 | 26 | 563 | 1.8 | 8.5 | 11 | 1 |
| | B2 (cap 1) | 158 | 16 | 350 | 0.39 | 9.0 | 9 | 0 |
| | B4ii physical (cap 1) | 84 | 9 | 192 | 1.3 | 8.7 | 4 | 0 |
| tangential 256 | A | 226 / 216 | 23 | 502 / 492 | 1.2 / 1.7 | 9.0 | 1 | 10 / 4 |
| | B1 | 276 / 265 | 28 | 612 / 601 | 1.5 | 7.8 | 3 | 8 / 2 |
| | B2 (cap 1) | 92 | 10 | 212 | 1.6 | 8.1 | 6 | 4 |
| | B4ii physical (cap 1) | 114 / 108 | 12 | 258 / 252 | 1.4 | 8.5 | 2 | 5 / 2 |
| tilted 256 | A | 171 / 169 | 18 | 387 / 385 | 1.7 / 1.1 | 8.8 | 1 | 3 / 1 |
| | B1 | 233 / 231 | 24 | 521 / 519 | 1.4 | 7.0 | 5 | 2 / 1 |
| | B2 (cap 1) | 212 | 22 | 476 | 0.28 | 9.1 | 9 | 0 |
| | B4ii physical (cap 1) | 99 | 10 | 219 | 1.5 | 8.7 | 3 | 0 |
| districts 256 | A | 154 / 150 | 16 | 490 / 486 | 1.07 | 8.1 | 23 | 4 / 2 |
| | B1 | 281 / 284 | 29 / 31 | 890 / 935 | 0.46 | 8.5 | 192 | 12 / 9 |
| | B3 on B1 | 187 | 19 | 586 | 1.3 | 8.0 | 123 | 3 |
| | B2 (cap 1) | 116 | 12 | 368 | 0.29 | 9.5 | 175 | 0 |
| | B2 cap 3 / no cap | stalled | | | 1.5 / 0.7 | 92 / 22 | 288 / 299 | 44 / 31 |
| | B4ii normalized | 174 / 168 | 18 | 552 | 1.5 | 7.5 | 102 | 6 |
| | B4ii physical (cap 1) | stalled | 8 | 248 | 43 | 273 | 121 | 0 |
| | B4i one step (cap 3) | stalled | 50 | 1,100 | 17.5 | 412 | 256 | 2 |
| districts 512 | A | 263 | 27 | 884 | 0.61 | 9.5 | 20 | 0 |
| | B1 | not converged in 400 | 40 | 1,320 | 9.8 | 182 | 271 | 9 |
| | B3 on B1 | 334 | 34 | 1,116 | 1.8 | 9.9 | 232 | 12 |
| | B2 (cap 1) | 69 | 7 | 230 | 0.18 | 9.2 | 188 | 0 |
| | B4ii normalized | 303 | 31 | 1,016 | 0.38 | 8.9 | 218 | 0 |
| | B4ii physical (cap 1) | stalled | 16 | 528 | 0.30 | 21 | 157 | 56 |
| | B4i one step (cap 3) | 25 | 25 | 600 | 0.06 | 8.8 | 213 | 2 |
| counties 256 | A | 260 stalled / 300 | 26 / 45 | 1,495 / 2,438 | 57 | 2,057 | 112 / 158 | 30 / 40 |
| | all B variants | stalled or 300 | | 288 to 2,425 | 48 to 1,142 | 4,000 to 215,000 | 408 to 2,755 | |
| counties 512 | A | 300 | 30 | 1,155 | 26 | 2,812 | 48 | 5 |
| | B2 (cap 1) | stalled at 240 | 24 | 924 | 32 | 1,587 | 752 | 53 |
| | B4ii physical (cap 1) | stalled at 210 | 21 | 808 | 22 | 1,437 | 763 | 13 |
| | B1, B3, B4ii normalized | 300 | 30 | 1,155 | 109 to 186 | 11,500 to 26,800 | 872 to 1,000 | 0 |

Iterations to converge across dt, states 256, refresh on:

| variant | dt 0.1 | 0.2 | 0.4 | 0.6 |
|---|---|---|---|---|
| A | 216 | 113 | 66 | 45 |
| B1 | 274 | 135 | 69 | 49 |
| B3 on B1 | 258 | 130 | 64 | 43 |
| B4ii normalized | 242 | 117 | 63 | 41 |

## Answers

- The GSM spatial pattern (B1) does not help. It needs 1.2 to 1.9 times the iterations of A (states 256: 135 vs 113; states 512: 270 vs 214; districts 256: 281 vs 154; districts 512 does not converge in 400). The trace shape is unchanged (a slow descent, then a steep cliff), so the tail is not removed. It reduces the rises on strong anisotropy (horizontal 17 to 1) but not reliably, and creates self-intersections (states 256: 6 invalid polygons against 0 for A; states 512: 21; districts 100 to 300 against 20 to 24).
- The physical magnitude (B2, B4ii) matters a lot, but only with the per-step cap. Cost drops 3 to 5 times on states (82 vs 257 at grid 256, 135 vs 742 at 512) and on districts 512 (230 vs 884), and does not depend on dt. On anisotropy: horizontal 350 vs 545, tangential 212 vs 502, tilted 476 vs 387 (worse). It adds invalid polygons, B4ii stalls on districts, and the cap is untuned.
- The clamp: floors 0.01 and 0.02 give identical results on states, districts and counties 512; 0.1 changes only the final error. No blow-up occurred at any floor, but zero-valued targets were not run, so the floor was never really tested.
- Precomputing the field (B3) is not equivalent to computing on the fly, because rho0 is discontinuous at region borders and interpolating the product smooths it. The one-step displacement differs by up to 0.6 to 0.8 of a step length (99th percentile 0.2 to 0.3) at t = 0, falling to 0.4 to 4.6 % of the displacement at t = 0.9. Per step, B3 against B1 takes 0.24 against 0.31 ms on states 256, 0.55 against 0.77 ms on districts 256, 1.13 against 1.65 ms on counties 256, and 1.42 against 1.82 ms on counties 512. At grid 1024 B3 is slower (states 4.2 vs 1.3 ms). It wins only when vertices outnumber grid cells, at grids up to 512.
- B4 (closed-form round integral): normalized sub-steps are about equal to A on states (261 vs 257) and slower on districts (552 vs 490); physical sub-steps are the fastest on states (63 at 256, 134 at 512) and anisotropy (192, 258, 219) but stall on districts. One step per round (B4i) converges in 5 to 25 iterations with a recompute each, but needs the cap, stalls on districts 256 and counties, and each iteration costs 15 to 50 ms.
- Counties: every variant fails, as A does (400 to 2,800 invalid polygons).
- The multiresolution coarse plateau: B1, B2, B4ii and B4i all converge (cost 181, 143, 83 to 127 and 80, against 190 for the stalled A). At states 128 (DC has no cell centre) the physical variants and B3 stall at 13.6 like A, while B1 converges. The mechanism was not investigated.
- Refresh-on-rise had no effect on the states runs (no rises). It lowers A's rises on anisotropy (17 to 9, 10 to 4, 3 to 1), and for B2 on counties it costs more recomputes (24 to 42).

## Recommendation

- Do not adopt the GSM spatial pattern (B1, or B3 on B1), as a default or an option: it is slower and adds self-intersections. The hypothesis that the two methods overlap except for the step magnitude is largely confirmed.
- The physical magnitude is the part worth exploring: B2 with a per-step cap of 1 cell, or B4ii physical, cuts the cost 3 to 5 times on states and removes the multires plateau. It is not adoptable as is: more invalid polygons than A, B4ii stalls on districts, the cap is untuned, it fails on counties, and tilted anisotropy gets slower.
- A cheaper first test is the constant scale with a larger dt or recompute_every: A at dt 0.6 takes 45 iterations on states (0 to 1 invalid polygons), though districts then have 80 invalid.
- B3 is only worth it if the pattern is adopted, and only for vertex-heavy inputs at grids up to 512. B4i is not competitive on cost.

## Controls: pattern versus magnitude

The maintainer questioned two things: B1 renormalizes by the grid maximum of |v f| (f up to 50 in sparse cells), so it may be a smaller effective step rather than a pattern effect; and B2's physical step (mean 0.3 to 0.56 cells at states 256 and 512, against 0.09 for A) is simply larger than A's. Controls added (commit bfb4253, `step_scale_mode` values `const_physical`, `gsm_equal_step`, `constant_errprop`, field `step_scale_ref`):

- C1 `const_physical`: B2 with the constant rho_mean instead of rho(x,t) (cap 1 cell). Compare C1 with B2.
- C2 `gsm_equal_step`: B1's factor, renormalized so the mean vertex displacement per step equals A's at the same step (statistic over the vertices, from the unscaled field). Floors 0.02, 0.1 (C2f10) and 0.5 (C2f50). Compare C2 with A.
- C3: A at a larger dt, cap 1 cell. C3m: dt such that A's mean vertex displacement per step over the run matches B2's (measured per case, `scripts/measure_disp.py`, `data/dtmatch.json`): states 128 0.21, 256 0.71, 512 1.2 (run at the allowed maximum 1.0), multires 0.19, horizontal 0.27, tangential 0.52, tilted 0.17, districts 256 0.29, 512 0.85, counties 256 0.71, 512 0.33. C3d06 and C3d10: dt 0.6 and 1.0.
- C4 `constant_errprop`: A's direction and normalization, step = dt_max * clip(score_previous / ref, 0.1, 1) cells, cap 1 cell; C4a/C4b: dt_max 0.6 with ref 3/10; C4c/C4d: dt_max 1.0 with ref 3/10; C4e/C4f: ref 30 (added because the score is below 3 only in the last iterations, so ref 3 and 10 are almost the same as a constant dt_max).

Cost (iterations + recomputes x ratio), invalid polygons and status; refresh on rise off / on where they differ (c converged, s stalled, x iteration limit). Mean error at the stop is 0.2 to 1.9 % for all converged runs (stopping tolerance). All cells in `controls_tables.md` (iterations, recomputes, mean, max, rises).

| case | A | C3m (dt) | C3d06 | C1 | C2 | C4a | C4f | B1 | B2 |
|---|---|---|---|---|---|---|---|---|---|
| states 256 | 257, 0 inv, c | 103 (0.71), 0, c | 198 s / 117 c, 1 | 101, 1, c | 235, 5, c | 198 s / 117 c, 1 | 108, 0, c | 303, 6, c | 82, 6, c |
| states 512 | 742, 0, c | 196 (1.0), 0, c | 299, 0, c | 166, 1, c | 706, 22, c | 269, 0, c | 299, 0, c | 918, 21, c | 135, 6, c |
| multires coarse | 190, 1, s | 222 s / 141 c (0.19), 1 | 152 s / 76 c, 2 / 5 | 152, 3, s | 171, 8, s (f 0.1 / 0.5: 164 / 163, c) | 152 s / 76 c, 2 / 5 | 91 / 83, 5, c | 181, 10, c | 143, 23, c |
| horizontal | 545 / 557, 0, c | 479 / 464 (0.27), 0, c | 440 s / 226 c, 1 | 220, 2, s | 454, 12, c | 367 / 228, 1, c | 324 / 392, 2 / 0, c | 563, 11, c | 350, 9, c |
| tangential | 502 / 492, 1, c | 352 s / 315 c (0.52), 1 / 0 | 286 s / 329 c, 0 / 1 | 524, 1, c | 478, 7, c | 286 s / 464 c, 0 | 432, 4, c | 612, 3, c | 212, 6, c |
| tilted | 387 / 385, 1, c | 438 (0.17), 0, c | 484 s / 332 c, 3 / 1 | 700, 0, c | 438, 2, c | 369 / 337, 3 / 1, c | 543, 3, c | 521, 5, c | 476, 9, c |
| districts 256 | 490 / 486, 23, c | 496 s / 409 c (0.29), 21 / 23 | 589 s / 477 c, 81 / 80 | 279, 75, s | 926, 204, c | 589 s / 477 c, 81 / 79 | 521 c / 445 s, 102 / 79 | 890, 192, c | 368, 175, c |
| districts 512 | 884, 20, c | 324 (0.85), 52, c | 389 / 457, 39 / 37, c | 227 / 251, 87 / 83, c | 1,320, 288, x (f 0.5: 1,281, c) | 391 / 458, 37, c | 297 / 393, 54 / 38, c | 1,320, 271, x | 230, 188, c |
| counties 256 / 512 | all variants fail (stall or iteration limit, 28 to 1,428 invalid) | | | | | | | | |

Refresh-on-rise dependence: with refresh off, every larger constant step (C3d06, C3d10, C3m, C4a, C4c) oscillates with rises of the score (18 to 84 rises below 20 at dt 0.6 on states 128, tilted, districts 256) and often stalls; with refresh on they converge (rises 1 to 13). The dt sweep (states and districts 256, refresh on, `tables.md`): C2 at dt 0.1/0.2/0.4/0.6 takes 213/103/56/38 iterations on states (5 to 8 invalid) and 50 (stalled)/288/121/112 on districts (163 to 203 invalid); C4a and C4b (dt_max = dt) equal A within 1 to 12 % at every dt (states 218/114/63/45; districts 276/152/89/141, invalid 0 to 1 and 10 to 79) because ref 3 and 10 are only reached in the last iterations.

### What the controls separate

- (i) Pattern only. C2 against A at an equal mean step: states 256 235 vs 257 (5 invalid polygons vs 0), states 512 706 vs 742 (22 vs 0), districts 256 926 vs 490 (204 vs 23), districts 512 not converged in 400, tilted 438 vs 387, horizontal 454 vs 545, tangential 478 vs 502. The pattern at an equal step gives at best 5 to 17 % fewer iterations (horizontal), is worse on districts and tilted, and always adds self-intersections. B1's slowness was therefore partly the smaller effective step (cost B1 303 vs C2 235 on states 256, 918 vs 706 on states 512; on districts 256 890 vs 926 they are equal), but the pattern itself does not speed up A. C1 against B2: B2's pattern helps where the flow is distorted: horizontal (C1 stalls at 220, B2 350 converged), tilted (700 vs 476), tangential (524 vs 212), districts 256 (C1 stalls at 279, B2 368), but costs 6 to 9 invalid polygons on states against 1 for C1 and 188 against 87 on districts 512; on states 256 and 512 C1 is not slower than B2 (101 vs 82, 166 vs 135) and has 1 invalid polygon.
- (ii) Larger step only. C3m (A with B2's mean step) takes 103 at states 256 and 196 at states 512 with 0 invalid polygons (A 257 and 742): a larger constant step recovers most of B2's gain on states without self-intersections. Districts 512: 324 vs 884 (52 invalid vs 20), districts 256 (dt 0.29): 409 vs 490 with refresh on (23 invalid); tangential 315 vs 492, horizontal 464 vs 557, tilted 438 vs 385 (worse). With refresh off the larger steps oscillate and several stall; refresh on rise is needed.
- (iii) Error-aware magnitude without pattern. C1 (physical, constant scale) is the cheapest on states (101, 166) and districts 512 (227), with 1 and 87 invalid polygons, but stalls on horizontal, districts 256 and the multires level and is slow on tilted/tangential: the physical magnitude without a pattern is not robust. C4 (error-proportional dt_max) with ref 3 and 10 is practically C3 at dt_max (it differs only in the last iterations); with ref 30 and dt_max 1.0 (C4f) it converges everywhere but counties (states 256 108, 512 299, multires 83 to 91, horizontal 324/392, tangential 432, districts 512 297/393) but not districts 256 with refresh on (stalls, 92 % max error), and is slower than C3m on states and tilted. C4 is not cheaper than a constant dt of the same size in these runs (C4f 108 vs C3d10 92 on states 256 with refresh on); the error-proportional factor is not what makes B2 fast.
- (iv) Pattern plus magnitude (B2) is the lowest cost on states 256 (82) and the only low-cost converged variant on tangential (212), horizontal (350) and districts 256 (368, with refresh off or on), at 6 to 9 invalid polygons on states and 175 to 188 on districts, against 0 to 1 for C3m or C4f on states and 23 to 52 on districts.

### What remains of GSM's advantage

- The pattern alone (C2): nothing. It is a smaller gain than noise on states, a loss on districts and tilted anisotropy, and adds invalid polygons (5 to 22 on states against 0).
- The magnitude: a larger constant step, with refresh on rise, reproduces most of B2's gain on states (C3m 103 vs B2 82 at 256; 196 vs 135 at 512) and districts 512 (324 vs 230) with 0 invalid polygons on states. The magnitude advantage that remains for B2 is on strongly distorted flows: tangential, horizontal and districts 256 (a constant larger step stalls or oscillates there). That part is a combination of pattern and magnitude (C1 fails there, C2 does not help).
- The multires plateau: removed by larger steps with refresh on (C3d06 76 cost, C3m 141, C4a 76, C4f 83 to 91), by a weak pattern (C2 floors 0.1 and 0.5: 164, 163) and by B1/B2, not by the same-size step without it (C3m with refresh off, C1, C2 at floor 0.02 stall). So the plateau does not need GSM; it needs a bigger step or a weak pattern.
- C4 against B2 (invalid polygons, plateau, districts, late spikes): C4f has fewer invalid polygons than B2 on states (0 vs 6) and on districts 512 (54 / 38 vs 188), fixes the multires plateau (83 to 91), converges districts 512 (297 to 393) but not districts 256 with refresh on, and is not faster than C3m. Late spikes: rises below score 20 under C4a/C4c are as many as under C3 at the same dt_max (1 to 13 with refresh on, up to 84 off); only refresh on removes them. Counties: still fail.

Caveats of the controls: one run per cell; C3m for states 512 was capped at dt 1.0 (matching dt 1.2); C4 with ref 3 and 10 is nearly a constant dt_max, so the error-aware magnitude was probed only through ref 30 and dt_max 0.6 and 1.0; the mean displacement per step is measured over each run's own iterations; the dt of C3m is not tuned beyond the match; counties controls ran for the headline variants only.

## Caveats

- Runs stop at score 1, so the physical variants were not checked for accuracy after that point.
- B1 normalizes by the grid maximum of |v f| at each step (outside cells included), not over vertices.
- The dt sweep covered states and districts 256 only, with refresh on.
- The anisotropy runs use the preview's settings with the stall rule on (the adaptive-recompute page used it off, so its iteration counts differ).
- Cap values were not tuned; wall times are one run per cell.

Reproduce: `uv run python make_figures.py` in this directory; `scripts/run_case.py <case> <grid> [variants] [dt]` for the cases; `scripts/bench_precompute.py` for the B1 versus B3 benchmark; `scripts/invalid_reasons.py` for the invalid-polygon reasons.
