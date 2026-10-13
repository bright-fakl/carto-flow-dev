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

| sectors | dots outside their region | when | region | share of the region's dots inside it | 0-0.01 | 0.01-0.02 | 0.02-0.04 | 0.04-0.08 | 0.08-0.16 | 0.16-0.32 | 0.32-0.64 | 0.64-1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | left alone | before | A | - | 0.00 | 0.00 | 0.02 | 0.12 | 0.51 | 1.33 | 1.30 | 0.83 |
| 1 | left alone | before | B | - | 1.90 | 2.03 | 2.41 | 2.76 | 0.83 | 0.90 | 0.94 | 0.86 |
| 1 | left alone | after | A | 1.000 | 0.43 | 0.22 | 0.45 | 0.74 | 0.95 | 0.94 | 1.01 | 1.37 |
| 1 | left alone | after | B | 0.666 | 1.85 | 2.10 | 2.46 | 2.81 | 0.80 | 0.91 | 0.93 | 0.85 |
| 8 | left alone | before | A | - | 0.00 | 0.00 | 0.02 | 0.12 | 0.50 | 1.33 | 1.30 | 0.83 |
| 8 | left alone | before | B | - | 1.85 | 2.07 | 2.35 | 2.82 | 0.81 | 0.91 | 0.93 | 0.86 |
| 8 | left alone | after | A | 1.000 | 1.07 | 0.74 | 1.14 | 0.82 | 0.83 | 0.85 | 1.08 | 1.15 |
| 8 | left alone | after | B | 0.666 | 1.95 | 1.73 | 2.37 | 2.81 | 0.85 | 0.88 | 0.94 | 0.86 |
| 1 | pulled back | before | A | - | 0.00 | 0.00 | 0.02 | 0.13 | 0.50 | 1.33 | 1.30 | 0.83 |
| 1 | pulled back | before | B | - | 1.83 | 2.05 | 2.38 | 2.80 | 0.82 | 0.90 | 0.93 | 0.86 |
| 1 | pulled back | after | A | 1.000 | 0.44 | 0.21 | 0.46 | 0.68 | 0.96 | 0.93 | 1.02 | 1.37 |
| 1 | pulled back | after | B | 1.000 | 0.18 | 1.94 | 2.48 | 1.72 | 1.17 | 1.06 | 0.94 | 0.93 |
| 8 | pulled back | before | A | - | 0.00 | 0.00 | 0.02 | 0.12 | 0.50 | 1.33 | 1.30 | 0.83 |
| 8 | pulled back | before | B | - | 1.77 | 2.03 | 2.38 | 2.75 | 0.82 | 0.91 | 0.94 | 0.86 |
| 8 | pulled back | after | A | 1.000 | 1.08 | 0.87 | 1.10 | 0.75 | 0.84 | 0.85 | 1.08 | 1.16 |
| 8 | pulled back | after | B | 1.000 | 1.38 | 1.33 | 2.46 | 1.50 | 1.22 | 1.03 | 0.94 | 0.92 |

## Original map and the flow, z-score of the border band per dot seed

| seed | original map | carried by the flow |
|---|---|---|
| 0 | -0.11 | 3.19 |
| 1 | 2.31 | 6.14 |
| 2 | 0.98 | 3.77 |
| 3 | 0.98 | 5.56 |
| 4 | -0.29 | 3.48 |
| 5 | 1.15 | 5.22 |
| 6 | -0.58 | 3.13 |
| 7 | 0.63 | 3.77 |
| mean | 0.63 | 4.28 |

## Reference-point warp (thin-plate spline through boundary vertices and carried interior points), 8 seeds

| boundary vertices | interior points | z mean (sd) | dots inside their region | shift against the flow: median / 95th pct | carried tracers against the warp: median / 95th pct |
|---|---|---|---|---|---|
| 8 | 0 | 1.13 (1.24) | 0.9391 | 0.0254 / 0.1256 | 0.026 / 0.125 |
| 16 | 0 | 0.86 (1.43) | 0.9778 | 0.0156 / 0.0661 | 0.0162 / 0.0726 |
| 32 | 0 | 1.89 (1.27) | 0.9927 | 0.0115 / 0.0566 | 0.0122 / 0.0598 |
| 64 | 0 | 2.44 (1.25) | 0.9963 | 0.0102 / 0.0512 | 0.0105 / 0.0563 |
| 128 | 0 | 2.87 (1.2) | 0.9992 | 0.0096 / 0.0491 | 0.0099 / 0.058 |
| 32 | 1 | 1.81 (1.32) | 0.9922 | 0.0083 / 0.0457 | 0.0083 / 0.0448 |
| 64 | 1 | 2.31 (1.25) | 0.9963 | 0.0072 / 0.0391 | 0.0071 / 0.0382 |
| 64 | 5 | 2.35 (1.27) | 0.9964 | 0.0067 / 0.0369 | 0.0066 / 0.0352 |
| 128 | 5 | 2.81 (1.23) | 0.9993 | 0.0063 / 0.0348 | 0.0061 / 0.0346 |

## Pooled distance profile on the states, observed / expected (mean over 8 seeds)

| dots | 0-0.01 | 0.01-0.02 | 0.02-0.04 | 0.04-0.06 | 0.06-0.1 | 0.1-0.2 | 0.2-0.4 | 0.4-0.6 |
|---|---|---|---|---|---|---|---|---|
| original | 1.03 | 1.04 | 1.00 | 1.03 | 1.00 | 0.99 | 0.97 | 1.18 |
| flow | 1.40 | 1.27 | 1.10 | 1.02 | 0.96 | 0.93 | 0.90 | 0.88 |
| distance remap | 1.06 | 1.04 | 1.01 | 1.04 | 0.99 | 0.98 | 0.99 | 0.98 |
| warp (16 boundary vertices) | 0.77 | 0.93 | 1.01 | 1.05 | 1.03 | 0.98 | 0.96 | 0.82 |
| warp (64 boundary vertices, 1 interior point) | 1.07 | 1.16 | 1.08 | 1.03 | 1.01 | 0.96 | 0.92 | 0.72 |

## Velocity field against the distance to the border (median over the regions, states)

Divergence relative to its value deep inside the region (1 = uniform scaling), and normal velocity (outward) divided by divergence x sqrt(area); the disk with uniform scaling gives 0.282 at the border and falls with slope -0.5.

| grid | field | quantity | 0-0.01 | 0.01-0.02 | 0.02-0.04 | 0.04-0.06 | 0.06-0.1 | 0.1-0.15 | 0.15-0.2 | 0.2-0.3 | 0.3-0.4 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| grid 128 | first | divergence | 0.83 | 0.81 | 0.86 | 0.88 | 0.91 | 0.96 | 0.99 | 1.00 | 1.00 |
| grid 128 | first | normal velocity | 0.22 | 0.16 | 0.19 | 0.17 | 0.17 | 0.15 | 0.13 | 0.10 | 0.05 |
| grid 128 | last | divergence | 0.79 | 0.84 | 0.86 | 0.91 | 0.90 | 0.97 | 0.99 | 1.00 | 1.01 |
| grid 128 | last | normal velocity | 0.16 | 0.18 | 0.18 | 0.17 | 0.15 | 0.13 | 0.12 | 0.06 | 0.04 |
| grid 256 | first | divergence | 0.79 | 0.79 | 0.84 | 0.91 | 0.97 | 1.00 | 1.00 | 1.00 | 1.00 |
| grid 256 | first | normal velocity | 0.20 | 0.19 | 0.18 | 0.17 | 0.15 | 0.15 | 0.10 | 0.10 | 0.04 |
| grid 256 | last | divergence | 0.68 | 0.78 | 0.85 | 0.91 | 0.95 | 0.99 | 1.00 | 1.00 | 1.00 |
| grid 256 | last | normal velocity | 0.17 | 0.16 | 0.17 | 0.15 | 0.15 | 0.12 | 0.10 | 0.06 | 0.02 |
| grid 512 | first | divergence | 0.80 | 0.85 | 0.91 | 0.99 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| grid 512 | first | normal velocity | 0.16 | 0.20 | 0.17 | 0.17 | 0.15 | 0.15 | 0.12 | 0.07 | 0.05 |
| grid 512 | last | divergence | 0.66 | 0.78 | 0.88 | 0.97 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| grid 512 | last | normal velocity | 0.17 | 0.15 | 0.17 | 0.16 | 0.12 | 0.12 | 0.11 | 0.05 | 0.05 |

## Dot density predicted from the velocity field along the dot paths, against the observed one (states, grid 256, 8 seeds)

The step of every iteration is fitted from the displacements of the dots; the residual of the fit is 0.0000 (median) and 0.0000 (95th percentile). Predicted: harmonic mean of exp(-log J) times the area ratio over the dots in the bin.

| regions | | 0-0.01 | 0.01-0.02 | 0.02-0.04 | 0.04-0.06 | 0.06-0.1 | 0.1-0.2 | 0.2-0.4 | 0.4-0.6 |
|---|---|---|---|---|---|---|---|---|---|
| expanding | observed | 1.53 | 1.37 | 1.16 | 1.01 | 0.93 | 0.90 | 0.88 | 0.94 |
| expanding | predicted | 1.59 | 1.39 | 1.19 | 1.06 | 0.97 | 0.92 | 0.90 | 0.90 |
| shrinking | observed | 1.00 | 0.96 | 0.91 | 1.04 | 1.07 | 1.00 | 0.98 | 0.65 |
| shrinking | predicted | 1.11 | 1.02 | 1.00 | 1.03 | 0.99 | 1.00 | 0.98 | 0.97 |

## Remap from the velocity field (no tracers), z-score of the border band

| seed | before | after | shift: median / 95th pct (in sqrt(area)) |
|---|---|---|---|
| 0 | 3.19 | 0.0 | 0.0062 / 0.0251 |
| 1 | 6.14 | 3.07 | 0.0073 / 0.0275 |
| 2 | 3.77 | 1.28 | 0.0072 / 0.0296 |
| 3 | 5.56 | 1.91 | 0.007 / 0.0284 |
| 4 | 3.48 | -0.46 | 0.0071 / 0.0292 |
| 5 | 5.22 | 0.87 | 0.0074 / 0.0317 |
| 6 | 3.13 | -1.1 | 0.0066 / 0.0316 |
| 7 | 3.77 | -0.35 | 0.0079 / 0.0284 |
| mean | 4.28 | 0.65 | |

## Without snapshots: the area scaling summed in place, and the first velocity field only (states, grid 256, 8 seeds)

`inplace`: log J summed during the morph (no `save_internals`, no `snapshot_every`); F of the remap from 400 sample points per region. `first field only`: the divergence profile of the first velocity field per region and the area ratio of the region, no sum along the paths (F from polygon buffers).

| seed | before | in place (sampled F) | first field only |
|---|---|---|---|
| 0 | 3.19 | 0.12 | 2.38 |
| 1 | 6.14 | 3.48 | 5.56 |
| 2 | 3.77 | 1.28 | 3.36 |
| 3 | 5.56 | 1.33 | 4.87 |
| 4 | 3.48 | -0.87 | 2.61 |
| 5 | 5.22 | 0.64 | 3.54 |
| 6 | 3.13 | -0.4 | 2.2 |
| 7 | 3.77 | -0.23 | 2.55 |
| mean | 4.28 | 0.67 | 3.38 |

## Cost of the correction (states, one dot seed with 1480 dots, grid 256, 112 iterations)

Morph time without the sum in place: 0.31, 0.214, 0.218 s (3 runs after a warm-up); with the sum in place in a Python wrapper: 0.236, 0.235, 0.232 s, of which 0.0141, 0.0136, 0.0136 s in the sum itself. Memory: one float per dot, and the divergence of the current field (one grid) while it is in use.

| remap | seconds | z after (before: 3.19) | median shift (x sqrt(area)) |
|---|---|---|---|
| 26 distance points, polygon buffers | 14.8 | 0.12 | 0.006 |
| first order, no buffers | 0.04 | 1.51 | 0.0009 |
| 200 sample points per region | 0.13 | 0.35 | 0.0073 |
| 400 sample points per region | 0.17 | 0.52 | 0.0067 |
| 1000 sample points per region | 0.36 | 0.06 | 0.0061 |
