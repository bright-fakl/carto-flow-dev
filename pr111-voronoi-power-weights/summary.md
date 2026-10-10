---
pr: 111
url: https://github.com/bright-fakl/carto-flow/pull/111
issue: 83
title: Weighted Voronoi cartograms as power diagrams with exact areas
description: With weights, RasterBackend cells are now straight-edged power-diagram cells whose areas match the weight-proportional targets (mean error 72-84 % on main, 0.00-0.04 % now on the 49 states); weighted runs above the new area_error_tol are reported as not converged; the elastic boundary is driven by the advected input density.
branch: feat/voronoi-power-weights
base: main
date: 2026-10-09 03:55
before: main @ 0124245
after: feat/voronoi-power-weights @ 02c94c9
updated: 2026-10-09 15:30
inputs: 49 contiguous US states with population (bundled), 432 congressional districts with population (bundled), lognormal weights (seed 1) on the states; RasterBackend resolution 256, n_iter 300, area_cv_tol 0.05
---

## What changed

- With `weights` and euclidean labeling, `RasterBackend` assigns pixels by the power distance `|x - p_i|^2 - lambda_i` instead of `|x - p_i|^2 / w_i`. Cell borders are straight lines; each cell is the intersection of half-planes (convex before clipping to the boundary).
- During relaxation the offsets integrate the pixel-area deficit toward weight-proportional targets (rate `area_equalizer_rate`, default 0.1). They also leak while the generators are still far from their cell centroids; without that leak the offsets oscillate on inputs with many clustered generators (432 districts).
- The final cells are exact polygons: a damped Newton solve on the exact clipped areas fits the offsets until every cell is within `VoronoiOptions.area_error_tol` (new, default 0.01) of its weight-proportional share of the final boundary area. It starts from the relaxation's offsets and needs 2-5 area evaluations.
- With weights, the elastic boundary is driven by the input density carried along by the boundary flow: one particle per active pixel carries its input region's density (weight divided by region area), moves with the same velocity and step as the boundary vertices, and its grid histogram is the pressure density. The pressure computed from cells (multiplicatively weighted, power or plain) pulled the northeastern states inward, because once every cell is on target no direction remains in the cell densities (see the elastic boundary section).
- Weighted runs whose mean area error exceeds `area_error_tol` are reported as `converged=False` with a `RuntimeWarning` (for example `ExactBackend` and `distance_mode="geodesic"`, which still ignore weights). Unweighted runs are unchanged: positions, cells and metrics hash identically to main on seven unweighted configurations (the elastic one differs from main only by the run-to-run noise that main also shows).

## Before and after

figure: weighted_states.png — The three weighted gallery configurations (fixed boundary, ElasticBoundary(0.05), circular boundary): cells colored by area / target, black dots are the generators. After: all cells white (on target) with straight edges.
figure: weighted_detail.png — Northeast, fixed boundary: curved multiplicatively weighted borders before, straight power-diagram borders after.
figure: weighted_extremes.png — Lognormal weights spanning about 1400x (sigma 1.5) and 15600x (sigma 2).
figure: weighted_districts.png — 432 congressional districts with population weights (about 2x range).

Mean and max are `|area / target - 1|` of the output polygons; k is the slope of log area against log weight (1.0 is proportional); "it" is the number of iterations; times are wall-clock seconds on one machine (the runtime printed on the first "before" panel, 0.0 s, is not reliable; a separate run took 4.2 s).

| case | weight range | mean before | max before | k before | mean after | max after | k after | it before / after | s before / after | converged before / after |
|---|---|---|---|---|---|---|---|---|---|---|
| fixed boundary | 68x | 77.6 % | 552 % | 0.55 | 0.04 % | 0.69 % | 1.00 | 300 / 250 | 4.2 / 2.8 | False / True |
| ElasticBoundary(0.05) | 68x | 72.2 % | 628 % | 0.57 | 0.00 % | 0.002 % | 1.00 | 28 / 222 | 5.6 / 25.8 | True / True |
| gallery: ElasticBoundary(0.02) + adjacency_spring 0.2 | 68x | 71.5 % | 519 % | - | 0.006 % | 0.07 % | 1.00 | - / 100 | 10.6 / 10.4 | - |
| circular boundary | 68x | 84.4 % | 393 % | 0.49 | 0.00 % | 0.003 % | 1.00 | 300 / 65 | 2.7 / 0.6 | False / True |
| lognormal sigma 1.5 | 1399x | 525 % | 15579 % | 0.30 | 0.004 % | 0.09 % | 1.00 | 300 / 131 | 3.7 / 1.5 | False / True |
| lognormal sigma 2 | 15646x | 3946 % | 144566 % | 0.22 | 0.02 % | 0.89 % | 1.00 | 300 / 300 | 2.8 / 2.8 | False / False |
| 432 districts, population | 2x | 49.2 % | 174 % | 2.11 | 0.00 % | 0.05 % | 1.00 | 300 / 185 | 17.9 / 11.0 | False / True |

"converged False" for sigma 2 means the `area_cv_tol` stopping rule did not fire within 300 iterations; the output areas are within tolerance and no warning is raised.

## Elastic boundary direction

With weights the boundary should move outward near states whose weight share exceeds their area share (NY, NJ, PA, MA, CT, RI) and inward near sparse states (MT, ND, WY). "Rank corr" is the Spearman correlation between log(weight share / area share) and the outward-minus-inward boundary area within 150 km of each of the 34 coastal states; "NE outward" is the same area summed over NY, NJ, PA, MA, CT and RI.

| configuration | main: rank corr / NE outward | branch before the fix: rank corr / NE outward | after the fix: rank corr / NE outward |
|---|---|---|---|
| ElasticBoundary(0.05) | 0.59 / +294k km2 | -0.25 / -269k km2 | 0.54 / +295k km2 |
| ElasticBoundary(0.02) + adjacency_spring 0.2 (gallery) | 0.49 / +286k km2 | 0.02 / -111k km2 | 0.56 / +302k km2 |

Per state after the fix, ElasticBoundary(0.05), outward displacement in km: NY +510, NJ +416, PA +184, MA +457, CT +301, RI +680 (between -430 and -1000 before the fix); MT -696 (main -428), ND -539 (main -345), ID -261, WY -155, SD -138.

figure: elastic_displacement.png — Boundary displacement, main / branch before the fix / after the fix, for both elastic configurations; the northeastern states are highlighted.

The boundary keeps its initial area within 0.4 % (main: +1 %; see the next section). In the ElasticBoundary(0.05) configuration the push is slightly weaker than on main; in the gallery configuration it is stronger. That run takes about 220 iterations before the stopping rule fires (75 before the elastic fixes), about 12.5 s after the speed-up below; the gallery configuration takes about 4 s. The figures were generated at 671f7b0; the speed-up commit does not change results at fixed iteration counts.

## Boundary area

figure: elastic_area.png — Boundary area relative to the original over 300 forced iterations (main, the cell-driven branch, the first particle version, the current version) for both elastic configurations.

The first particle-driven version shrank the boundary by 4 to 5 % and, in long runs, collapsed it. Two causes:

- Mass was lost. Particles that drift just outside the vertex-sampled boundary polygon land on pixels outside the active mask, where the histogram is overwritten with the exterior target. The mass inside the polygon fell to 0.966 of the total at iteration 200 and the boundary area to 0.954; the lower interior density pushed the boundary further inward, which lost more particles. Main does not drift because its cell-based density holds the total weight by construction. The interior histogram is now scaled to hold the total weight, and the exterior reference is the mean over the initial active pixels (total weight / (initial pixel count x pixel area)) instead of total weight / polygon area. This also removes main's systematic +1 % (+2.4 % at resolution 128), which comes from pixel-count versus polygon-area mismatch.
- The boundary collapsed to 0.09 % of its area at iteration 258. In `_deform_boundary`'s slow rebuild path, `make_valid` of a self-intersecting mainland ring returns a GeometryCollection of a MultiPolygon, a MultiLineString and a MultiPoint, and the loop kept only items of type Polygon, so the mainland was dropped. It now keeps every polygonal part. This bug exists on main too and appears only when a ring self-intersects in that way, which long elastic runs make likely.

Boundary area change over 300 forced iterations: ElasticBoundary(0.05): main about +1.0 %, first particle version -4.8 % at iteration 250 and then the collapse, now +0.0 to +0.4 % (final +0.05 %). Gallery configuration: main +1.0 %, first particle version -4.3 %, now -0.1 to +0.4 %.

## Compute cost of the elastic boundary

49 states, population weights, resolution 256, NUMBA_NUM_THREADS=8, numba warm, wall time of `create_voronoi_cartogram`. "Before" is 671f7b0, "after" is 02c94c9 (vectorized ring advection and rebuild, `make_valid` only on invalid rings, union only of overlapping parts, sliver-hole check only on parts with holes, single-threaded FFT plan).

| run | before | after |
|---|---|---|
| ElasticBoundary(0.05), 100 iterations | 10.6 s | 4.9 s |
| gallery (ElasticBoundary(0.02) + spring 0.2), 100 iterations | 10.0 s | 4.0 s |
| gallery, 300 iterations | 29.6 s | 13.7 s |
| ElasticBoundary(0.05), to convergence (area_cv_tol 0.05) | 18.4 s (183 it) | 12.5 s (222 it) |
| fixed boundary, 100 iterations | 1.1 s | 1.2 s |

At fixed iteration counts the results are unchanged: final boundaries identical (symmetric difference 0), generators within 2e-15 cell radii, weighted cells within 1e-12 of their area. The iteration count at convergence differs between runs because of the existing run-to-run noise of the elastic kernels. Remaining cost per elastic iteration (about 37 ms): the overlap query of the boundary parts, `make_valid` of the self-intersecting mainland ring, the union of overlapping parts and the generator clamp.

The multithreaded FFTW plan used before took about 100 ms per velocity solve on this 256 x 164 grid (2 ms single-threaded); the flow cartogram chooses its own FFT thread count and is not affected. The first call in a fresh environment compiles the numba displacement kernels, which are cached (`cache=True`); the FFT velocity solve itself uses no numba.

## Cell checks (after)

Measured on every configuration above plus resolution 128 and 512, `AdhesiveBoundary(0.3)`, the main gallery example (ElasticBoundary(0.02), adjacency_spring 0.2) and districts with lognormal sigma 1.5 weights:

- Every vertex of cell i is at least as close to generator i in power distance as to any other generator (largest violation 1e-14 of the squared cell radius; 3e-8 where two generators coincided and were moved apart by 1e-9 of the extent).
- Cells that do not touch the boundary are convex (area equals convex-hull area to 1e-15).
- `shapely.coverage_is_valid` holds (no gaps or overlaps), the cell areas sum to the boundary area, no cell is empty.
- A convex cell clipped to the non-convex US outline can split into parts across a bay or lake: 0-6 of 49 state cells have a second part larger than 1 % of the cell (main: 0-6); 14 of 432 district cells (main: 24).

## Where it degrades

- Lognormal sigma 2 on the states (15646x): areas are exact, but the smallest cell (a target of a few pixels at resolution 256) ends with its generator 6 cell radii from its centroid (8 at resolution 512); visible as small slivers in weighted_extremes.png. The accuracy gate does not flag this, because areas are correct.
- Districts with lognormal sigma 1.5 weights (432 cells, many targets below one pixel at resolution 256): areas are exact (mean 0.006 %), but the median generator sits 0.4 cell radii from its centroid (max 11.5), and 34 cells have a second part.
- When the exact solve cannot reach the tolerance (forced in the tests by limiting it to zero Newton steps), the run is reported as not converged with a warning that gives mean and max error.

## Tests

`tests/test_voronoi_cartogram.py::TestWeightedPowerCells` (11 tests, about 25 s together, all fail on main; the elastic-direction test also fails on the branch before the fix): 1 % mean error on the states with population weights (union and circle boundary) plus the power-cell, convexity and coverage checks; ElasticBoundary(0.05); weights spanning 1399x; custom `area_error_tol`; reporting of a failed solve; ExactBackend and geodesic labeling with weights reported as not converged; no gate for unweighted runs; option validation. The new elastic test checks (49 states, ElasticBoundary(0.05), resolution 128, 60 iterations) that the boundary moves outward next to NY, NJ, MA, CT and RI and inward next to MT, ND and WY, that the coastal rank correlation exceeds 0.5, that the mean area error is at most 1 %, and that the final boundary area is within 2 % of the original. The voronoi test file (65 tests) and the full suite (804 tests) pass; pre-commit and mypy pass.

Regenerate the figures with `uv run python make_figures.py` from a carto-flow checkout of the branch (it exports main @ 0124245 with `git archive` for the "before" half; set `BEFORE_REF` to override).
