---
issue: 86
title: Border pile-up of dots carried with a flow cartogram: re-evaluation and a distance remap
description: Dots carried along with the flow cartogram are over-represented near region borders also on the current code (border-band z-score +3.8 at the defaults; the exact rasterizer, the adaptive step and recompute_on_rise do not change it). With the field recomputed every iteration it falls with the grid size (+4.0, +2.8, +2.1, +1.3 at 128 to 1024). On a two-region case with a 4:1 contrast the shrinking region is emptied along the border by the same amount at every grid size. A post-morph remap of the distance to the border, built per region from tracer points carried through the same morph, lowers the mean z-score over 8 dot seeds from 4.3 to 1.1 with a median move of 0.7 % of the region width; 50 tracers per region are enough; sectors around the centroid do not help on the states; pooling the regions is worse (2.8).
kind: exploration
topic: flow
status: open
related: exploration-hierarchical-morph, flow-convergence-synthesis
date: 2026-10-13 01:30
before: main @ e78c5a9
after: the same checkout; dots, tracers and the remap run after the morph
inputs: 49 states (bundled) with poverty counts, dot density with n_dots = round(max / 25000), normalization "maximum" (about 1,480 dots per seed), MorphOptions defaults with area_scale 1e-6 and n_iter 400 unless stated; the two-region case is two unit squares with values 1 and 4 and 20,000 uniform dots each, tolerances 0.5 % / 1 %. NUMBA_NUM_THREADS=8.
---

`border_band.py`, `resolution_scan.py`, `two_regions.py`, `distance_remap.py` (writes a cache that `sector_remap.py` reads), `sector_remap.py` and `toy_remap.py` produce the data in `data/`; `make_tables.py` writes `data/tables.md` (every table below) and `make_figures.py` the figures (it reads the cache that `distance_remap.py` writes to `data/states_morph.pkl`, which is not committed). The border-band z-score counts the dots inside a band (6 % of `sqrt(area)` wide) along the border of their own region and compares it with the number expected for uniform dots, as a binomial z-score summed over regions. The z-score of the start geometry is about +0.6; for a uniform sample its standard deviation over seeds is about 1.

## Findings

- **The effect is still there.** At the defaults the z-score is +3.8 (dot seed 7); over 8 seeds it is 4.3 on average (sd 1.1). The center rasterizer (+3.55), `adaptive_dt` off (+3.77) and `recompute_on_rise` do not change it, so #119 and #123 did not affect it.
- **It falls with the grid size** when the field is recomputed every iteration: +4.0, +2.8, +2.1 and +1.3 at grids 128, 256, 512 and 1024. With the default recompute interval it is +2.7 at grid 512.
- **Two regions.** With a 4:1 contrast the dots of the shrinking region are absent from a strip of about 8 % of its width along the shared border at every grid size, and the dots of the growing region pile up there (2.2 to 2.8 times the expected number at grid 128, 1.5 to 2.7 at grid 512 with the field recomputed every iteration). In this case about a third of the dots of the growing region end outside it (10 % inside the other region), so a correction that works on positions inside the region cannot fix them. In the states, all dots stay in their own state.
- **Distance remap.** Tracer points, uniform in each original region, are carried through the same morph. For each region the distribution G of their distance to the morphed border is compared with the distribution F of a uniform sample of the morphed region, and a dot at distance d moves along the direction to its nearest border point to F⁻¹(G(d)). Over 8 dot seeds the mean z-score falls from 4.3 to 1.1 (residual sd 1.3). The median dot moves 0.7 % of `sqrt(area)`, the 95th percentile 2.4 %, the largest 8 %.
- **Pooling the regions is worse**, as expected from the different sizes and distortion profiles: one remap in units of `sqrt(area)` for all regions gives a mean z-score of 2.8.
- **A limited set of reference points is enough**: 50 tracers per region give a mean z-score of 1.14 (2000: 1.10), with a median move of 1.4 % instead of 0.7 %.
- **Sectors around the centroid** (the angular sector of the nearest border point decides which remap applies) do not help on the states (mean z 1.21, 1.18 and 1.71 for 4, 8 and 16 sectors) and get worse with fewer tracers. On the two-region case they bring the shrinking region to 0.8 to 1.1 times the expected number (8 sectors) where a single remap leaves 0.2 to 0.7.
- **Not tested:** a boundary-driven map from the vertex displacements (mean-value coordinates) and a polar map around the centroid. Both give a smooth map but do not give a uniform density without a further correction.

figure: fig_resolution.png — Border band z-score of the dots on the current code. Left: dot seed 7 for the defaults and single changes (the start geometry is 0.6); the center rasterizer and adaptive_dt off do not change it. Right: with the field recomputed every iteration it falls with the grid size.
figure: fig_two_regions.png — Two squares with values 1 and 4, observed / expected dots by distance to the shared border. The shrinking region A is empty along the border at every grid size; the growing region B has 1.5 to 2.8 times the expected dots there, less with a finer grid and recompute_every 1.
figure: fig_remap_states.png — The distance remap on the states. Left: z-score of the border band for 8 dot seeds (grey lines) and their mean (blue), without correction, with a remap per region and with one pooled remap. Right: mean z-score against the number of tracer points per region, with one and with 8 sectors around the centroid.
figure: fig_remap_toy.png — The remap on the two-region case (grid 256). The shrinking region A moves toward the expected counts, more with 8 sectors; the growing region B is not corrected because a third of its dots lie outside it.
figure: fig_map.png — California and Nevada, dot seed 7. Left and middle: the dots before and after the remap, with the 6 % border band shaded. Right: zoom on the shared border; each arrow goes from the dot carried by the flow to its corrected position.

## Border band z-score on the current code (dot seed 7)

| variant | status | iterations | observed vs expected | z |
|---|---|---|---|---|
| start | - | 0 | 458 vs 447.0 | 0.63 |
| defaults (grid 256, recompute_every 10) | converged | 112 | 500 vs 435.0 | 3.77 |
| grid 512 | converged | 214 | 483 vs 436.3 | 2.71 |
| recompute_every 1 | converged | 106 | 482 vs 439.3 | 2.47 |
| grid 512, recompute_every 1 | converged | 209 | 463 vs 439.9 | 1.33 |
| defaults, density_rasterization center | converged | 113 | 496 vs 434.8 | 3.55 |
| defaults, adaptive_dt off | converged | 112 | 500 vs 435.0 | 3.77 |
| defaults, dt 0.05 | completed | 400 | 481 vs 435.9 | 2.61 |

## Field recomputed every iteration, grid size

| variant | status | iterations | observed vs expected | z |
|---|---|---|---|---|
| grid 128, recompute_every 1 | converged | 55 | 509 vs 439.8 | 4.0 |
| grid 256, recompute_every 1 | converged | 106 | 488 vs 439.3 | 2.81 |
| grid 512, recompute_every 1 | converged | 209 | 477 vs 439.9 | 2.14 |
| grid 1024, recompute_every 1 | completed | 400 | 462 vs 439.8 | 1.28 |

## Two squares (A: value 1, B: value 4), observed / expected dots by distance to the shared border (in sqrt(area))

| variant | region | 0-0.01 | 0.01-0.02 | 0.02-0.04 | 0.04-0.08 | 0.08-0.16 | 0.16-0.32 | 0.32-0.64 | 0.64-1 |
|---|---|---|---|---|---|---|---|---|---|
| grid 128 | A | 0.00 | 0.00 | 0.02 | 0.13 | 0.53 | 1.33 | 1.29 | 0.83 |
| grid 128 | B | 2.25 | 2.50 | 2.51 | 2.84 | 0.79 | 0.90 | 0.92 | 0.84 |
| grid 256 | A | 0.00 | 0.00 | 0.02 | 0.13 | 0.51 | 1.34 | 1.29 | 0.83 |
| grid 256 | B | 1.85 | 2.06 | 2.40 | 2.81 | 0.82 | 0.90 | 0.93 | 0.85 |
| grid 512 | A | 0.00 | 0.00 | 0.02 | 0.12 | 0.48 | 1.34 | 1.30 | 0.83 |
| grid 512 | B | 1.62 | 1.91 | 2.28 | 2.77 | 0.83 | 0.92 | 0.94 | 0.86 |
| grid 512, recompute_every 1 | A | 0.00 | 0.00 | 0.01 | 0.10 | 0.44 | 1.35 | 1.31 | 0.81 |
| grid 512, recompute_every 1 | B | 1.49 | 1.74 | 2.16 | 2.71 | 0.85 | 0.91 | 0.94 | 0.87 |

## Distance remap on the states, 8 dot seeds (z-score of the border band)

| seed | before | per region | pooled | shift per region: median / 95th pct / max (in sqrt(area)) | shift pooled: median / 95th pct / max |
|---|---|---|---|---|---|
| 0 | 3.19 | 0.0 | 1.45 | 0.0068 / 0.0244 / 0.078 | 0.0055 / 0.0066 / 0.007 |
| 1 | 6.14 | 3.71 | 4.81 | 0.0067 / 0.0246 / 0.08 | 0.0054 / 0.0065 / 0.007 |
| 2 | 3.77 | 1.57 | 2.73 | 0.0072 / 0.0241 / 0.078 | 0.0055 / 0.0066 / 0.007 |
| 3 | 5.56 | 2.38 | 4.12 | 0.0069 / 0.0245 / 0.081 | 0.0054 / 0.0065 / 0.007 |
| 4 | 3.48 | 0.23 | 1.68 | 0.0069 / 0.0247 / 0.074 | 0.0055 / 0.0066 / 0.007 |
| 5 | 5.22 | 1.62 | 3.25 | 0.0071 / 0.0241 / 0.079 | 0.0054 / 0.0065 / 0.007 |
| 6 | 3.13 | -0.58 | 1.86 | 0.0072 / 0.0247 / 0.081 | 0.0057 / 0.0066 / 0.007 |
| 7 | 3.77 | 0.06 | 2.15 | 0.007 / 0.0245 / 0.078 | 0.0056 / 0.0066 / 0.007 |

Mean z over the seeds: before 4.28, per region 1.12, pooled 2.76.

## Fewer reference points and sectors around the centroid (states, 8 seeds; z before: mean 4.28)

| sectors | tracers per region | z mean | z sd | z max | shift median | shift 95th pct |
|---|---|---|---|---|---|---|
| 1 | 2000 | 1.1 | 1.34 | 3.65 | 0.0072 | 0.0247 |
| 1 | 500 | 1.18 | 1.26 | 3.59 | 0.0072 | 0.0294 |
| 1 | 200 | 1.15 | 1.51 | 4.35 | 0.0098 | 0.0339 |
| 1 | 100 | 0.97 | 1.48 | 4.0 | 0.0131 | 0.0463 |
| 1 | 50 | 1.14 | 1.39 | 3.48 | 0.0139 | 0.0499 |
| 4 | 2000 | 1.21 | 1.19 | 3.42 | 0.0076 | 0.0381 |
| 8 | 2000 | 1.18 | 1.28 | 3.71 | 0.0083 | 0.0381 |
| 16 | 2000 | 1.71 | 1.01 | 3.54 | 0.0086 | 0.0389 |
| 8 | 500 | 1.63 | 1.15 | 4.06 | 0.011 | 0.0454 |
| 8 | 200 | 2.07 | 1.12 | 3.77 | 0.0153 | 0.0589 |

## Two squares after the remap (grid 256), observed / expected by distance to the shared border

| sectors | when | region | 0-0.01 | 0.01-0.02 | 0.02-0.04 | 0.04-0.08 | 0.08-0.16 | 0.16-0.32 | 0.32-0.64 | 0.64-1 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | before | A | 0.00 | 0.00 | 0.02 | 0.12 | 0.51 | 1.33 | 1.30 | 0.83 |
| 1 | before | B | 1.90 | 2.03 | 2.41 | 2.76 | 0.83 | 0.90 | 0.94 | 0.86 |
| 1 | after | A | 0.43 | 0.22 | 0.45 | 0.74 | 0.95 | 0.94 | 1.01 | 1.37 |
| 1 | after | B | 1.85 | 2.10 | 2.46 | 2.81 | 0.80 | 0.91 | 0.93 | 0.85 |
| 4 | before | A | 0.00 | 0.00 | 0.02 | 0.12 | 0.50 | 1.33 | 1.30 | 0.83 |
| 4 | before | B | 1.85 | 2.07 | 2.35 | 2.82 | 0.81 | 0.91 | 0.93 | 0.86 |
| 4 | after | A | 0.70 | 1.00 | 0.70 | 0.98 | 0.91 | 0.85 | 1.03 | 1.24 |
| 4 | after | B | 1.79 | 1.88 | 2.42 | 2.80 | 0.79 | 0.91 | 0.94 | 0.86 |
| 8 | before | A | 0.00 | 0.00 | 0.02 | 0.13 | 0.50 | 1.33 | 1.30 | 0.83 |
| 8 | before | B | 1.83 | 2.05 | 2.38 | 2.80 | 0.82 | 0.90 | 0.93 | 0.86 |
| 8 | after | A | 1.11 | 0.77 | 1.12 | 0.79 | 0.83 | 0.85 | 1.08 | 1.16 |
| 8 | after | B | 1.89 | 1.92 | 2.34 | 2.79 | 0.87 | 0.90 | 0.93 | 0.86 |
| 16 | before | A | 0.00 | 0.00 | 0.02 | 0.12 | 0.50 | 1.33 | 1.30 | 0.83 |
| 16 | before | B | 1.77 | 2.03 | 2.38 | 2.75 | 0.82 | 0.91 | 0.94 | 0.86 |
| 16 | after | A | 1.14 | 0.82 | 0.87 | 0.91 | 0.84 | 0.84 | 1.10 | 1.13 |
| 16 | after | B | 1.92 | 2.27 | 2.27 | 2.78 | 0.86 | 0.87 | 0.94 | 0.86 |
