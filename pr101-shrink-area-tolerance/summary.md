---
pr: 101
url: https://github.com/bright-fakl/carto-flow/pull/101
issue: 74
title: Converge proportional shrink on the area residual
description: shrink() now bounds the relative area error of the shrunken core by tol (default 0.01); before, tol applied to the buffer distance and small targets missed by up to 72%.
branch: fix/shrink-area-tolerance
base: main
date: 2026-10-08 16:53
updated: 2026-10-08 18:07
before: main
after: fix/shrink-area-tolerance @ bead3dc
inputs: states (bundled), each shrunk to its population density relative to the densest state (DC kept whole)
---

# Shrink area tolerance

`proportional_cartogram.shrink` used `tol` as the root-finder tolerance on the
buffer distance. For small target fractions the area is very sensitive to that
distance, so the core could miss its area target without a warning. The solve
now runs on the relative area residual and stops as soon as
`abs(area / target - 1) < tol`, so `tol` sets both the achieved area error and
the speed. The default is `0.01`.

Each state is shrunk to its density ratio relative to the densest state (the
non-contiguous cartogram construction in issue #74). DC is excluded from the
measurements. `make_figures.py` regenerates every figure from a carto-flow
checkout.

- `area_error_per_state.png`: area error of every shrunken core, main (left)
  and fix at the default tol (right), states sorted by target fraction. Same
  x range on both.
- `map.png`: the shrunken cores over the original states, main and fix.
- `tol_sweep.png`: maximum area error and runtime for main and for several `tol`.
- `isotropic.png`: the `isotropic` option, described below.

| State (target) | main | fix (tol=0.01) |
|---|---|---|
| SD (1.0%) | -23.9% | -0.222% |
| MT (0.63%) | -71.7% | -0.447% |
| ID (1.8%) | -12.3% | -0.240% |
| NM (1.5%) | +17.7% | -0.049% |
| OH (24.7%) | -0.7% | -0.689% |
| PA (24.7%) | -1.1% | +0.007% |

At the default tol the largest absolute error over the 50 states is 0.874%
(mean 0.252%), against 71.7% (mean 6.043%) on main. Main exceeds 1% error for
33 states and 0.1% for 44; the fix exceeds 1% for none and 0.1% for 29.
OH is unchanged because main already lies within the default tolerance there.

## Effect of tol

Area error over the 50 states and runtime for all of them (median of 3 runs).
Runtimes were measured while other jobs shared the machine and differ by about
10% between runs, so differences between neighboring rows are within noise.

| version | max error | mean error | time (s) |
|---|---|---|---|
| main | 71.700% | 6.043% | 7.1 |
| fix tol=0.05 | 4.792% | 1.496% | 6.4 |
| fix tol=0.01 (default) | 0.874% | 0.252% | 5.6 |
| fix tol=1e-3 | 0.094% | 0.016% | 6.3 |
| fix tol=1e-4 | 0.008% | 0.001% | 6.7 |

Runtime is about the same as main for every tol; the differences are within
the run-to-run noise.

## Isotropic erosion

`shrink(geom, f, isotropic=True)` maps the geometry by the inverse square root
of its area covariance about its centroid, runs the same area-residual solve,
and maps the core back. The shell is still the original minus the core, so the
outer boundary is unchanged. The default is `False` and leaves results as
above.

`isotropic.png` shows WY, CO, TN, FL, NM and OK at fraction 0.05 with the real
`shrink()`: plain erosion (top), `isotropic=True` (middle) and plain scaling of
the geometry about its centroid (bottom). Titles give the core's aspect ratio
(long over short side of the minimum rotated rectangle) against the original.
Scaling leaves the geometry for FL (marked OUTSIDE).

| state | original | plain erosion | isotropic | scaling | scaling inside |
|---|---|---|---|---|---|
| WY | 1.2 | 1.8 | 1.2 | 1.2 | yes |
| CO | 1.2 | 2.3 | 1.3 | 1.2 | yes |
| TN | 3.7 | 14.2 | 3.3 | 3.7 | yes |
| FL | 1.9 | 8.8 | 6.7 | 1.9 | no |
| NM | 1.2 | 1.5 | 1.0 | 1.2 | yes |
| OK | 1.9 | 2.7 | 1.2 | 1.9 | yes |

Isotropic erosion keeps the core close to the original proportions for WY, CO,
TN, NM and OK. FL, which is curved and concave, still gives a thin core (6.7
against 8.8 for plain erosion).

Runtime of `shrink` on all 50 states (density fractions as above, default
tol, median of 3): 5.8 s with `isotropic=False`, 6.1 s with `isotropic=True`.
