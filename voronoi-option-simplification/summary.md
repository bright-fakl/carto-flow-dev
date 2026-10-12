---
pr: 126
url: https://github.com/bright-fakl/carto-flow/pull/126
issue: 109
title: Voronoi option simplification: internal tuning settings deprecated, behavioral tests for the regular options
description: Nine tuning settings (the relaxation schedule, the power-diagram offset rate and ramp, the output resolution, the cell smoothing, three elastic-boundary settings, adj_min_shared_length) warn when set to a non-default value and will stop being accepted in the next major release; AdhesiveBoundary and ElasticBoundary.adhesion_strength are deprecated; fix_topology with weights warns. Defaults and results are unchanged. 23 new tests cover the deprecations and the effect of the regular options (adjacency_spring 0.66 to 0.83, intra_group_spring 3 to 0 discontiguous groups).
kind: pr
topic: voronoi
branch: feat/voronoi-option-simplification
base: main
date: 2026-10-11 23:51
related: exploration-voronoi-options, exploration-voronoi-followup
before: main @ 2a03f40
after: feat/voronoi-option-simplification @ 31303c7
inputs: US states (49 incl. DC), bundled; RasterBackend at the resolutions stated; NUMBA_NUM_THREADS=8.
---

`option_effects.py` regenerates `data/tables.md` (the numbers in the section "Effect of the regular options").

The proposal on [exploration-voronoi-options](../exploration-voronoi-options/index.html) (with the change that advanced options stay regular options) is implemented as deprecations: nothing is removed, defaults and results are unchanged, and passing a non-default value of an internal setting works but warns.

## What changes

| setting | treatment |
|---|---|
| `RasterBackend.relaxation`, `ExactBackend.relaxation` | internal: a non-default value warns |
| `RasterBackend.area_equalizer_rate`, `weight_ramp_iters`, `output_resolution`, `cell_smoothing_px` | internal: a non-default value warns |
| `ElasticBoundary.step_scale`, `density_smooth`, `min_boundary_points` | internal: a non-default value warns |
| `VoronoiOptions.adj_min_shared_length` | internal: a non-default value warns |
| `AdhesiveBoundary`, `ElasticBoundary.adhesion_strength` | deprecated: use warns; removed in the next major release |
| `fix_topology` with `weights` | stays a regular option; a warning says it makes the run much slower and can move generators away from their weighted positions |
| `weights`, `premorph`, `boundary`, `group_by`, `backend`, `options`, `resolution`, `generator_anchor`, `distance_mode`, `adjacency_spring`, `intra_group_spring`, `ElasticBoundary.strength`, `n_iter`, `tol`, `area_cv_tol`, `area_error_tol`, `simplify_tol`, `prescale_components` | regular options, documented |

The warnings say "next major release", not a version number (#122). The documentation lists the internal and deprecated settings in one section of the algorithm page, drops them from the parameter tables and the how-to notebooks (the AdhesiveBoundary section, the relaxation-schedule section, the adhesion and equalizer arguments of the topology example), and gives the effect of each regular option (`adjacency_spring` has little effect with `premorph`; `ElasticBoundary(strength)` 0.02 to 0.05 gives a smooth outline). The `"circle"` boundary is described as it is built: centered at the mean of the convex hull vertices with the radius that encloses the union, not the minimum enclosing circle.

## Effect of the regular options

The behavioral tests (`tests/test_voronoi_options.py`) assert these directions on the 49 states:

## adjacency_spring (resolution 150, 60 iterations, no weights)

| adjacency_spring | fraction of input-adjacent pairs that stay adjacent |
|---|---|
| 0.0 | 0.661 |
| 0.1 | 0.697 |
| 0.3 | 0.725 |
| 0.6 | 0.826 |

## intra_group_spring with group_by (resolution 100, adjacency_spring 0.1, 60 iterations)

| group_by | intra_group_spring | discontiguous groups |
|---|---|---|
| Division | None | 3 |
| Division | 0.5 | 0 |
| Division | 1.0 | 0 |

## ElasticBoundary strength (resolution 120, 40 iterations)

| strength | area of the cell union / area of the input union |
|---|---|
| 0.0 | 1.000 |
| 0.05 | 1.025 |
| 0.3 | 1.010 |

## boundary (resolution 100, 20 iterations)

| boundary | union area / input union area | roundness 4 pi A / P^2 | share of the input covered |
|---|---|---|---|
| union | 1.00 | 0.07 | 1.000 |
| bbox | 1.69 | 0.76 | 1.000 |
| convex_hull | 1.35 | 0.83 | 1.000 |
| circle | 3.17 | 1.00 | 1.000 |

## simplify_tol (resolution 120, 10 iterations)

| simplify_tol (m) | vertices of the cell union |
|---|---|
| None | 14572 |
| 20000.0 | 3589 |
| 100000.0 | 3419 |

- **adjacency_spring** raises the share of input-adjacent pairs that stay adjacent from 0.66 to 0.83 (the test asserts a gain above 0.05 at 0.6).
- **intra_group_spring** with \`group_by\` removes the discontiguous groups (3 to 0 for the census divisions).
- **ElasticBoundary** deforms the outline (the union area changes by 2.5 % at strength 0.05; 0 keeps the area exactly).
- **boundary** sets the outline: the bbox, the convex hull and the circle all cover the input and are much rounder than the union (roundness 0.76, 0.83, 1.00 against 0.07).
- **simplify_tol** cuts the outline vertices (14,572 to 3,419 at 100 km).

## Evidence that nothing else changed

- All 99 existing and new Voronoi tests pass with \`DeprecationWarning\` from \`carto_flow\` turned into an error, so no internal path passes a deprecated value; the full suite passes (926 tests).
- The three how-to notebooks that were edited execute without errors and without deprecation warnings.
- The code paths are untouched: only warnings, documentation and tests were added, so results are identical.

## Not included

- Removing the settings (next major release).
- Basing \`metrics["converged"]\` on the output area error and the generator displacement instead of the raster area CV (listed as a guard in the proposal) is a behavior change and is left for a separate change.
- A warning for \`n_iter\` below what fixed and elastic weighted runs need (the proposal suggested raising the default or documenting 300 with \`area_cv_tol\` 0.05).
