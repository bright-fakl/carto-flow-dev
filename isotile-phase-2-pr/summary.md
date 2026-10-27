---
pr: 3
url: https://github.com/bright-fakl/isotile/pull/3
title: "isotile phase 2: edge-curve layer"
description: Phase 2 adds edge curves to isotile: EdgeShape, an idempotent index-based enforce_symmetry, spline and linear interpolation, the curved prototile outline and curved tiles, a validity rule (the outline must be a simple closed curve with positive area, decided by evidence on all 81 types), presets, versioned JSON serialization with edge_curve_modes, optional matplotlib helpers, an Edge curves docs page with six figures, and 1,615 more tests; CI is green.
kind: pr
topic: symbol
base: main
branch: phase-2-edge-curves
related: proposal-isohedral-tiling-library, isotile-phase-1-pr
date: 2026-10-27 13:00
before: bright-fakl/isotile main at 75f3ae7 (2,844 tests passed, 78 skipped)
after: branch head 2346f97 (4,459 passed, 186 skipped; not merged)
inputs: tactile 0.1.0, Python 3.10.18 locally, numpy 2.2.6, scipy 1.15.3, shapely 2.1.2 (test only), matplotlib (docs group and tests); CI on Linux (3.10 to 3.13), macOS and Windows. Random draws seeded; single runs.
---

`fig.py <output dir>` draws figures 1 to 3. `evidence_fit.py` (validity against tiling, 5 amplitudes x 81 types x 3 draws) and `evidence_checker.py` (the polyline test against GEOS `is_valid`) are the exploration runs behind the numbers; run them from this directory with `uv run --project /home/fakl/isotile-phase2 python evidence_fit.py 0`.

figure: fig1_presets.png — Six of the 15 tiling presets with curved edges, tiles colored by the coloring of the type.

figure: fig2_validity.png — Draws of random curves of growing amplitude (up to 2 times the edge length) for all 81 types: how many the validity test accepts (green) and rejects (red). Every accepted draw (663) covered a region exactly once; none was valid without tiling.

figure: fig3_cases.png — Three outlines of IH41 with a curve on shape id 0: a spike five times the tile size (valid, and it tiles), a spike with parallel sides that touch the side of the opposite edge (invalid, `bad_edges = (0, 2)`), and a crossing bow (invalid).

figure: shot_curves_light.png and shot_curves_dark.png — Screenshots of the new Edge curves page (headless Chromium, 1300 px wide). shot_concepts_light.png and shot_concepts_dark.png — the Concepts page with the new edge shapes figure at the end of the section "The straight prototile and edge shapes".

## What changed

- **Modules** `edges.py` (`EdgeShape`, `enforce_symmetry`, `is_symmetric`, `interpolate`), `curves.py` (outline, `EdgeInfo`, simplicity test, native edge transforms moved out of `tiling.py`), `presets.py`, `io.py`, `plot.py`.
- **`IsohedralTiling`** takes `edge_curves` (shape id to control points) and `edge_curve_modes`; new members `edge_curves`, `edge_curve_modes`, `edges`, `with_edge_curves`, `edge_outlines()`, `prototile(normalized, curved=True, n_points=None)`, `to_dict`, `from_dict`, `save`, `load`, `from_preset`. `with_frame`, `rotated` and `scaled` keep the curves. `TileSet.outlines()` and `polygons(curved=True)`; `vertices()` stays straight.
- **Symmetry.** Index pairing: point k with m - 1 - k; U maps (x, y) to (1 - x, y), S to (1 - x, -y); the middle point of an odd count moves onto the axis or the center. Idempotence holds bit for bit (tests with 50 random curves each for m = 2 to 40, with x not monotonic). A curve that is already symmetric is returned unchanged for every input, so the old special case is not needed.
- **Interpolation.** Parametric natural cubic spline on the chord-length parameter (scipy `CubicSpline`), `max(100, 10 m)` samples; the samples keep the symmetry; coincident consecutive points count once; `linear` returns the control points.
- **Validity.** See below. `check_prototile` gained `edge_curves` and `edge_curve_modes`; the constructor and the `parameters` setter raise `ValueError` and keep the state.
- **Presets.** The 15 tiling presets of carto-flow with the same names, types, parameters, curves and modes (all valid under the stricter rule); five edge curve presets (`straight`, `bump`, `dent`, `wave`, `s_curve`) that are built for a free edge and projected, valid for all 81 types at amplitude 0.04 (at 0.1 they are invalid for types 36, 38, 39 and 86 in some presets).
- **Serialization.** Format 1.1: `version`, `tiling_type`, `parameters`, `edge_curves`, `edge_curve_modes`, and `frame` when it is not the identity; keys sorted by shape id; reads 1.0 and ignores unknown keys.
- **Plotting.** `plot_prototile` and `plot_tiles`; matplotlib is imported inside the functions (a test checks `import isotile, isotile.plot` leaves it unimported).
- **Docs.** Page Edge curves, three API pages, Concepts section extended, six new figures (`concepts-edges`, `curves-shapes`, `curves-modes`, `curves-prototile`, `curves-tiling`, `curves-invalid`), CHANGELOG. `draw` in `make_doc_figures.py` uses `TileSet.outlines()`; the existing figures are byte-identical.
- **Packaging.** Extra `plot = ["matplotlib>=3.7"]`, `all` includes it, matplotlib in the `dev` group, marker `slow`.

## Validity rule and evidence

A curved prototile is valid iff its outline is a simple closed curve with positive area (and the straight prototile is valid). The edge constraints make the copies fit along shared edges.

| Check | Result |
|---|---|
| Random valid draws (amplitude 0.1 to 2.0 times the edge length, 81 types x 3, random parameters within 0.1) | 663 accepted draws, all covered 1500 random points of a region exactly once (0 gaps, 0 overlaps); 552 draws rejected |
| Tests, 72 types with a curvable edge | covering once with and without reflecting frames; area of every curved tile equals the straight area to 1e-9; neighbors share exactly the polyline of one edge; shared-point adjacency of curved outlines equals the lattice table (edge and vertex-only) |
| Polyline test against GEOS `is_valid` | 1,620 random outlines (906 valid), 0 disagreements |
| Placement and reversal against tactile | equal for 81 types (linear mode, tolerance 1e-12) |
| Long spike (5 tile sizes) on IH41 | valid, and 3000 random points are covered once: the length of an excursion is not a criterion |

Limits: simplicity is judged on the polyline of the samples, so it depends on the mode and the sampling; the covering test is by random points, not by exact overlap areas; two curves that come closer than 1e-9 of the outline extent without touching count as touching.

## Tests

4,459 passed and 186 skipped in 150 s (before: 2,844 and 78). New files: `test_edges.py` (57), `test_curves.py`, `test_curve_fit.py` (432), `test_io.py`, `test_presets.py` (60), `test_plot.py`, and a tactile placement test. The skips are the 9 types without a curvable edge in per-type tests and the earlier ones for types without parameters. Hypothesis is not a dependency; the property tests use seeded numpy draws.

## Deviations and open questions

- Not added from the proposal: `prototile_is_valid`, `TileSet.polygons(repair=True)`, the constructor warning (superseded by the decision to raise). `presets.py` holds both the 15 tiling presets (proposal) and the small edge curve presets (task).
- A curve for an `I` shape id raises `ValueError`; carto-flow ignored it.
- U and S curves with first-half points beyond x = 0.5 give other results than carto-flow's rule (by design, decision 5).
- `frame` is written to the dict when it is not the identity (not in the proposal's format).
- Open: whether `n_points` should become a property of the tiling instead of an argument of the outline methods; whether `check_prototile` should also test the straight prototile for tilings whose straight polygon is invalid but whose curved outline is simple (it does not; both are required).
