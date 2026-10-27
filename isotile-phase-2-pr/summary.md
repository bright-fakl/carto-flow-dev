---
pr: 3
url: https://github.com/bright-fakl/isotile/pull/3
title: "isotile phase 2: edge-curve layer"
description: Phase 2 adds edge curves to isotile: EdgeShape, an idempotent index-based enforce_symmetry, spline and linear interpolation, the curved prototile outline and curved tiles, a certified validity rule (simple closed outline with positive area and a clearance of 1e-6 diameter, exact for the curve and independent of the sampling, 1.3 ms for typical curves), presets, versioned JSON serialization with edge_curve_modes, optional matplotlib helpers, an Edge curves docs page with six figures, and 1,634 more tests; CI is green.
kind: pr
topic: symbol
base: main
branch: phase-2-edge-curves
related: proposal-isohedral-tiling-library, isotile-phase-1-pr
date: 2026-10-27 13:00
before: bright-fakl/isotile main at 75f3ae7 (2,844 tests passed, 78 skipped)
after: branch head 51c41ab (4,478 passed, 186 skipped; not merged)
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
- **Validity.** Certified clearance test in `clearance.py`, see below. `check_prototile` gained `edge_curves` and `edge_curve_modes`; neither it nor `check_curves` takes `n_points`; the constructor, the `parameters` setter, `from_dict` and `load` raise `ValueError` and keep the state.
- **Presets.** The 15 tiling presets of carto-flow with the same names, types, parameters, curves and modes (all valid under the stricter rule); five edge curve presets (`straight`, `bump`, `dent`, `wave`, `s_curve`) that are built for a free edge and projected, valid for all 81 types at amplitude 0.04 (at 0.1 they are invalid for types 36, 38, 86 (`wave`, `s_curve`) and 39 (`bump`, `dent`), re-verified with the certified rule).
- **Serialization.** Format 1.1: `version`, `tiling_type`, `parameters`, `edge_curves`, `edge_curve_modes`, and `frame` when it is not the identity; keys sorted by shape id; reads 1.0 and ignores unknown keys.
- **Plotting.** `plot_prototile` and `plot_tiles`; matplotlib is imported inside the functions (a test checks `import isotile, isotile.plot` leaves it unimported).
- **Docs.** Page Edge curves, three API pages, Concepts section extended, six new figures (`concepts-edges`, `curves-shapes`, `curves-modes`, `curves-prototile`, `curves-tiling`, `curves-invalid`), CHANGELOG. `draw` in `make_doc_figures.py` uses `TileSet.outlines()`; the existing figures are byte-identical.
- **Packaging.** Extra `plot = ["matplotlib>=3.7"]`, `all` includes it, matplotlib in the `dev` group, marker `slow`.

## Validity rule and evidence

A curved prototile is valid iff (a) the straight prototile is valid, (b) its outline is a simple closed curve with positive area, and (c) parts of the outline that are not directly consecutive are at least `1e-6 * diameter` apart (diameter: larger side of the bounding box of the native outline). The first version of the PR tested a polyline through 100 or more samples per curve; that test depends on the sampling and misses features finer than the spacing, so it was replaced.

Algorithm (`clearance.py`). Linear curves are segments, splines are their cubic pieces (Hermite to Bezier), all placed on the edges with reversal. Pairs of pieces that are not directly consecutive: boxes of the control points grown by tol/2 are compared for all pairs at once (numpy); overlapping pairs are subdivided level by level with de Casteljau (the piece with the larger extent is split) until both deviate at most tol/4 from their chords, which are compared as segments. Consecutive pieces get the same test except for the parts that contain the join; pairs whose tangents stay within 135 degrees are graphs over a direction and are accepted at once. Each piece must turn by less than 180 degrees (hodograph cone, subdivided; a vanishing tangent is a cusp), each join (polygon vertices and the closing join included) must turn by less than 180 degrees, and the area (Green's theorem on the Beziers) must be positive.

| Check | Result |
|---|---|
| Accepted random draws, 81 types, amplitudes 0.1 to 2.0 (seed 0, 3 draws each) | 653 accepted, all covered 1500 random points exactly once; 590 rejected (`evidence_fit.py`) |
| Threshold is the clearance (spikes grown until the verdict flips, 3 types, shapely distance of the nearest non-consecutive edges) | 1.000 times `1e-6 * diameter` at the last valid and the first invalid length |
| Sampled polyline test against certified test, 3 x 1620 random outlines (`evidence_checker.py`, seeds 0 to 2) | 2702 valid by the sampled test, GEOS on the samples equal to it everywhere. Certified rejects 9 that the sampled test accepts: 7 with a single piece turning by 180 degrees or more (a hairpin; the polyline is simple), 2 crossings or near-touches finer than the sample spacing. Certified accepts 1 that the sampled test rejects: a polyline crossing at 100 samples in a sharp turn that is gone at 400 samples (sampling artifact) |
| Loop of width 1e-3 of the edge (below the spacing of 0.01) | invisible to the sampled test, rejected by the certified test (test) |
| Placement and reversal against tactile | equal for 81 types |
| Long spike (5 tile sizes) on IH41 | valid, 3000 random points covered once: the length of an excursion is not a criterion |

Timings (`bench_curves.txt`, `bench_curves.py`; milliseconds per call, one machine; "check_curves" is the test on built curves, "check_prototile" includes building them, 6 control points per shape id):

```text
case              type  valid  check_prototile  check_curves
typical           IH28   True          3.66 ms       1.29 ms
near collision    IH28   True         17.08 ms      14.89 ms
just invalid      IH28  False         17.03 ms      14.86 ms
invalid           IH28  False         45.51 ms      43.53 ms
typical            IH4   True          4.53 ms       1.36 ms
near collision     IH4   True         20.99 ms      17.62 ms
just invalid       IH4  False         20.33 ms      17.08 ms
invalid            IH4  False         49.82 ms      46.38 ms
typical           IH41   True          2.86 ms       1.27 ms
near collision    IH41   True         17.34 ms      15.20 ms
just invalid      IH41  False         14.52 ms      12.80 ms
invalid           IH41  False         28.38 ms      26.93 ms
typical           IH66   True          2.86 ms       1.33 ms
near collision    IH66   True         17.21 ms      15.62 ms
just invalid      IH66  False         17.27 ms      15.53 ms
invalid           IH66  False         30.59 ms      28.92 ms
typical           IH13   True          3.47 ms       1.42 ms
near collision    IH13   True         18.03 ms      15.58 ms
just invalid      IH13  False         15.61 ms      13.53 ms
invalid           IH13  False         31.23 ms      28.93 ms
```

Limits: a gap in the certified test is the flatness bound tol/4 per piece, so the verdict is exact for gaps outside 0.5 to 1.5 times the clearance and is the segment distance of the flat pieces in between; only a piece that turns by 180 degrees or more is rejected without being self-intersecting. The covering test is by random points, not by exact overlap areas.

## Tests

4,478 passed and 186 skipped in 190 s (before: 2,844 and 78). New files: `test_edges.py` (57), `test_curves.py`, `test_curve_fit.py` (432), `test_clearance.py` (19: clearance 0.5, 0.9, 1.5 and 2 times 1e-6 for straight and curved walls, scaling, thin loop, fold at a join, loop and cusp in one piece, threshold between edges, independence of `n_points`, agreement with the sampled test and GEOS, preset validity at 0.04 and 0.1), `test_io.py`, `test_presets.py` (60), `test_plot.py`, and a tactile placement test. The skips are the 9 types without a curvable edge in per-type tests and the earlier ones for types without parameters. Hypothesis is not a dependency; the property tests use seeded numpy draws.

## Deviations and open questions

- Not added from the proposal: `prototile_is_valid`, `TileSet.polygons(repair=True)`, the constructor warning (superseded by the decision to raise). `presets.py` holds both the 15 tiling presets (proposal) and the small edge curve presets (task).
- A curve for an `I` shape id raises `ValueError`; carto-flow ignored it.
- U and S curves with first-half points beyond x = 0.5 give other results than carto-flow's rule (by design, decision 5).
- `frame` is written to the dict when it is not the identity (not in the proposal's format).
- `n_points` is removed from the validity functions and stays only an argument of the output methods (`prototile`, `edge_outlines`, `outlines`, `polygons`).
- A single piece that turns by 180 degrees or more is rejected although it can be a simple arc (specified rule); this rejected 7 of 2,702 simple polyline draws.
- Open: whether the hairpin rejection should be relaxed to a clearance test of the sub-pieces of one piece.
