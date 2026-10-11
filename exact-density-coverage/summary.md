---
pr: 119
url: https://github.com/bright-fakl/carto-flow/pull/119
issue: 95, 109
title: Exact area-weighted density rasterization (density_rasterization="exact")
description: Each grid cell takes the area it covers of each region instead of the region at its center. Regions smaller than a cell take part, the coarse multiresolution level no longer plateaus, and rasterization is faster or equal from grid 256 up; accuracy at the stopping point is comparable, and far past convergence center sampling gets lower because its field goes exactly uniform. The default stays center.
kind: pr
topic: flow
branch: feat/exact-density-coverage
base: docs/changelog-voronoi
date: 2026-10-11 16:00
related: exploration-area-coverage, flow-convergence-synthesis
before: main @ 4ae2ea1 (center sampling only)
after: feat/exact-density-coverage @ 5488a95
inputs: US states (49 incl. DC) and congressional districts (432), bundled; MorphOptions defaults except where stated (grid 256, dt 0.2, recompute_on_rise 0.01, stall rule on); NUMBA_NUM_THREADS=8. True error is the output area against the population share of the total output area.
---

The prototype and its first measurements are on [exploration-area-coverage](../exploration-area-coverage/index.html); this page measures the code of the PR. `make_figures.py` regenerates every figure and `data/tables.md`. Counties are not bundled and are not run here; the exploration page found them unchanged.

## What changes in the density field

figure: coverage_density.png — The initial density field around Washington DC at grids 128 and 256. DC covers 0.04 cells at grid 128 and 0.15 at 256 and contains no cell center at either, so center sampling does not see it; exact coverage puts its density (the bright cell at 256) where it is. The right column is exact minus center.

## Multiresolution

figure: coverage_multires.png — Score of a multiresolution morph from grid 128 (3 levels, 300 iterations per level, stall rule on), levels concatenated. Center sampling plateaus at 13.6 on the coarse level until the stall rule fires; exact coverage converges at once.

| input | rasterization | level | grid | status | iterations |
|---|---|---|---|---|---|
| states | center | 1 | 128 | stalled | 100 |
| states | center | 2 | 256 | converged | 34 |
| states | center | total | - | converged | 134 (true max error 5.63 %) |
| states | exact | 1 | 128 | converged | 63 |
| states | exact | total | - | converged | 63 (true max error 9.15 %) |
| districts | center | 1 | 128 | converged | 231 |
| districts | center | total | - | converged | 231 (true max error 8.72 %) |
| districts | exact | 1 | 128 | converged | 123 |
| districts | exact | total | - | converged | 123 (true max error 8.31 %) |

## Convergence and accuracy at the stopping point

figure: coverage_traces.png — Score against iteration at the default tolerances: the same path with a steeper end for exact coverage.
figure: coverage_maps.png — States at grid 256: area error per region (left, center; middle, exact) and the two outlines (right). The maps are nearly identical; the largest center error is Wyoming.

| input | grid | rasterization | status | iterations | reported max error % | true max error % | true mean error % | seconds |
|---|---|---|---|---|---|---|---|---|
| states | 128 | center | converged | 63 | 8.30 | 7.75 | 1.193 | 0.3 |
| states | 128 | exact | converged | 62 | 9.66 | 8.87 | 1.297 | 0.2 |
| states | 256 | center | converged | 113 | 4.38 | 4.36 | 0.313 | 0.6 |
| states | 256 | exact | converged | 112 | 0.79 | 0.78 | 0.203 | 0.2 |
| districts | 256 | center | converged | 150 | 8.00 | 8.05 | 1.065 | 0.7 |
| districts | 256 | exact | converged | 145 | 9.76 | 9.76 | 1.415 | 0.5 |

Different tolerances (the stopping point moves, and so do the errors at it):

| input | grid | tolerances | center: status, iterations, true max, true mean | exact: status, iterations, true max, true mean |
|---|---|---|---|---|
| states | 256 | 0.02 / 0.04 | converged, 115, 0.62, 0.071 | converged, 112, 0.78, 0.203 |
| states | 256 | 0.01 / 0.02 | converged, 115, 0.62, 0.071 | converged, 112, 0.78, 0.203 |
| states | 256 | 0.005 / 0.01 | converged, 115, 0.62, 0.071 | converged, 112, 0.78, 0.203 |
| states | 256 | 0.002 / 0.004 | converged, 161, 0.37, 0.073 | converged, 148, 0.39, 0.129 |
| states | 512 | 0.02 / 0.04 | converged, 215, 1.43, 0.186 | converged, 215, 3.32, 0.237 |
| states | 512 | 0.01 / 0.02 | converged, 215, 1.43, 0.186 | converged, 219, 0.68, 0.113 |
| states | 512 | 0.005 / 0.01 | converged, 217, 0.53, 0.067 | converged, 219, 0.68, 0.113 |
| states | 512 | 0.002 / 0.004 | converged, 219, 0.30, 0.054 | converged, 243, 0.38, 0.099 |
| districts | 256 | 0.02 / 0.04 | converged, 153, 3.64, 0.355 | converged, 151, 3.76, 0.571 |
| districts | 256 | 0.01 / 0.02 | converged, 155, 1.88, 0.252 | converged, 154, 1.50, 0.173 |
| districts | 256 | 0.005 / 0.01 | converged, 163, 0.90, 0.165 | converged, 156, 0.73, 0.132 |
| districts | 256 | 0.002 / 0.004 | converged, 235, 0.39, 0.074 | stalled, 220, 0.49, 0.109 |

At matching tolerances the iteration counts are within 10 %, with one exception: the districts at 0.2 %/0.4 % stall at 220 iterations for exact coverage (true maximum error 0.49 %) where center converges at 235. The true errors at the stopping point are mixed: lower for exact on the states at grid 256 with default tolerances, the states at 512 at 1 % and the districts at 1 %, higher on the mean for the states at 256.

## Far past convergence

figure: coverage_accuracy.png — True maximum area error against iteration with tolerances that cannot be reached (stall rule off, 300 iterations). Center sampling keeps improving; exact coverage plateaus.

| input | grid | rasterization | lowest true max error % | at iteration | true max error % at iteration 291 | true mean error % at iteration 291 |
|---|---|---|---|---|---|---|
| states | 256 | center | 0.04 | 291 | 0.04 | 0.015 |
| states | 256 | exact | 1.32 | 291 | 1.32 | 0.544 |
| states | 512 | center | 0.03 | 241 | 0.06 | 0.016 |
| states | 512 | exact | 0.33 | 261 | 0.35 | 0.093 |
| districts | 256 | center | 0.17 | 291 | 0.17 | 0.033 |
| districts | 256 | exact | 1.53 | 291 | 1.53 | 0.407 |

With center sampling the density field becomes exactly uniform once the rasterized regions match their targets, the velocity is zero, and the run freezes at a small true error. With exact coverage the residual never vanishes, and the normalized step (the fastest point moves `dt` cells) keeps moving the borders; the late-phase oscillation of #94. A smaller step near convergence is the lever for that, not the rasterizer. At realistic tolerances (above) both stop long before this matters. This is the reason the default stays `"center"`.

## Cost of one rasterization

Minimum of three calls, in milliseconds:

| input | grid | center ms | exact ms |
|---|---|---|---|
| states | 128 | 2.0 | 2.4 |
| states | 256 | 3.0 | 2.4 |
| states | 512 | 7.1 | 4.5 |
| states | 1024 | 23.0 | 12.8 |
| districts | 128 | 14.9 | 11.4 |
| districts | 256 | 18.7 | 8.3 |
| districts | 512 | 23.2 | 10.6 |
| districts | 1024 | 40.9 | 19.8 |

## Not changed

The counties plateau (targets far below one cell), the sawtooth, and the border drift of #86 are unaffected; see the exploration page.
