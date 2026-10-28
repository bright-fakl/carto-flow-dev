---
pr: 9
title: "isotile: outline option of cover and fill_region (curved by default for curved tilings)"
description: cover and fill_region select tiles by the straight outline, so at margin 0 a curved tiling leaves slivers along the region boundary (15 to 82 percent of the cases, up to 4.4e-2 of the region area). The new option outline selects the polygon; the default None means curved for a tiling with an edge curve and straight otherwise, so curved tilings cover the region completely. Behavior change at the default: 4 of the 9 curved presets return more tiles (puzzle_piece 126 instead of 112 at margin 0.1), and the selection takes 0.5 to 1 s instead of 0.1 s for 10,000 tiles; outline="straight" restores the former result.
kind: pr
topic: symbol
project: isotile
issue: 6
url: https://github.com/bright-fakl/isotile/pull/9
branch: cover-curved-outline
base: main
related: proposal-isotile-adoption
date: 2026-10-28 13:30
before: bright-fakl/isotile main at 392484c
after: cover-curved-outline @ 9040ac7 (4,837 passed, 204 skipped locally on Python 3.10)
inputs: Python 3.10, numpy, scipy, shapely; the 9 curved presets, random valid curved tilings of the 81 types; single runs
---

Isotile issue 6, the open question of section 4.5 and the step 1 report of [the adoption proposal](../proposal-isotile-adoption/index.html): tiles whose curves reach into the region but whose straight outline does not.

## Measurement before the change

Exact, with shapely: the uncovered area is region minus the union of the curved polygons of the returned tiles. A tile is missing when its curved polygon overlaps the region with area above 1e-9 of the tile area and it is not returned. Random regions (lower-left in [-5, 5]^2, width and height in [3, 12], `n_tiles` 20 to 400), 40 cases per preset and 60 over 144 random curved tilings (2 per type, random curves, amplitude up to 0.25).

| tiling | affected at margin 0 | mean / max uncovered fraction | missing tiles, mean / max |
|---|---|---|---|
| scalloped_hexagon | 0.15 | 5.3e-5 / 7.0e-4 | 1.1 / 14 |
| wavy_square | 0.25 | 7.1e-4 / 5.6e-3 | 8.9 / 76 |
| puzzle_piece | 0.30 | 3.8e-4 / 7.7e-3 | 5.9 / 56 |
| arrow_quad | 0.28 | 9.7e-5 / 1.3e-3 | 5.5 / 40 |
| wavy_triangle | 0.33 | 6.1e-4 / 8.7e-3 | 5.0 / 26 |
| interlocking_hexagon | 0.82 | 5.9e-3 / 4.4e-2 | 13.8 / 64 |
| flowers | 0.33 | 8.9e-5 / 1.0e-3 | 0.9 / 5 |
| scalloped_quad | 0.23 | 6.0e-4 / 1.3e-2 | 1.1 / 12 |
| tree | 0.28 | 8.7e-5 / 5.8e-4 | 3.1 / 25 |
| random curved (60 cases) | 0.37 | 3.6e-4 / 1.0e-2 | 3.4 / 58 |

At margin 0.1: 0 of 420 cases affected, uncovered fraction at most 2.5e-12 (rounding). The slivers lie in the margin band, outside the region proper. The fixed case (region (0, 0, 10, 6), `n_tiles=100`, margin 0): wavy_triangle leaves 9.7e-3 of the area uncovered (18 tiles missing), puzzle_piece 9.1e-4 (14), arrow_quad 8.5e-5 (12), flowers 1.9e-4 (2); scalloped_hexagon, wavy_square, scalloped_quad and tree 0.

## Design

`cover(bounds, *, outline="straight")` and `fill_region(..., outline="straight")`; `"curved"` selects every tile whose sampled curved polygon (`TileSet.outlines()` at the default sampling) overlaps the region with area above 1e-9 of the tile area. Steps: the candidate cell range comes from the curved prototile; the bounding box of the convex hull of the curved outline (a few vertices per tile, exact bounding box of the curves) is the prefilter; tiles whose hull is inside the region are kept without clipping; the rest are clipped exactly (the existing vectorized Sutherland-Hodgman, in chunks that bound the memory). Without curves the straight path runs and nothing changes.

Default: `outline=None`, which means `"curved"` if the tiling has an edge curve (any entry of `edge_curves`; `with_edge_curves(None)` or no curves gives the straight path) and `"straight"` otherwise. Explicit `"straight"` runs the former code and gives the former tiles; an invalid value raises `ValueError`. It is a new keyword-only argument of `cover` and the last keyword argument of `fill_region`; the diff in `fill_region` is the parameter, one docstring entry and the argument passed to `cover`.

Behavior change at the default, tile counts of `fill_region((0, 0, 10, 6), n_tiles=100, margin=0.1)` before (`"straight"`) and after (default):

| preset | before | after |
|---|---|---|
| scalloped_hexagon | 127 | 127 |
| wavy_square | 112 | 112 |
| puzzle_piece | 112 | 126 |
| arrow_quad | 112 | 124 |
| wavy_triangle | 114 | 132 |
| interlocking_hexagon | 127 | 127 |
| flowers | 121 | 123 |
| scalloped_quad | 145 | 145 |
| tree | 130 | 130 |

At margin 0.1 the extra tiles lie in the margin band only; at margin 0 they fill the slivers inside the region. Tilings without curves are unchanged. No existing test and no documentation figure changed (`make_doc_figures.py --check`: up to date; `cover` and `fill_region` are called only by the docs figures script, the logo script and the benchmark, on tilings without curves or with the figures unchanged).

Cost (`fill_region((0, 0, 100, 100), n_tiles=10000)`, best of 3, one machine; "straight" is the cost of the former default, "curved" the cost of the new default for a curved tiling):

| preset | outline points | straight | curved | tiles (curved) |
|---|---|---|---|---|
| wavy_square | 396 | 88 ms | 738 ms | 10,400 |
| puzzle_piece | 436 | 95 ms | 668 ms | 10,400 |
| scalloped_hexagon | 594 | 115 ms | 976 ms | 10,301 |
| wavy_triangle | 297 | 67 ms | 528 ms | 10,240 |
| flowers | 495 | 105 ms | 820 ms | 10,283 |

The time is the clipping of about 600 boundary tiles (the interior tiles are not clipped); it grows with the perimeter and with the number of outline points, not with the tile count. An earlier version that clipped all candidates ran out of memory at 10,000 tiles.

figure: fig_slivers.png - Region (0, 0, 10, 6), margin 0, `n_tiles=100`; left `outline="straight"`, right `"curved"`. Red: uncovered part of the region, from shapely; left is `outline="straight"` (the former default), right the new default for a curved tiling. Top: wavy_triangle, whole region (9.7e-3 uncovered before, 0 after). Middle: puzzle_piece, zoom on the bottom edge. Bottom: arrow_quad, zoom on the top-left corner (the sliver is 8.5e-5 of the area and is too thin to see; the extra tiles at the top on the right are the tiles that fill it).

## Tests

- `test_curved_outline_covers_the_region_at_margin_zero` (default): uncovered fraction below 1e-9 for 6 curved presets at 6 random regions each.
- `test_straight_outline_leaves_slivers_that_curved_covers`: wavy_triangle, straight above 1e-3, curved below 1e-9, the straight tiles are a subset.
- `test_curved_outline_equals_shapely_overlap_of_the_curved_polygons`: random valid curved tilings of all 81 types, tile set equal to the shapely overlap of the curved polygons of a padded cover.
- `test_outline_modes_agree_without_curves` (81 types, `cover` and `fill_region`), `test_default_outline_is_curved_with_curves_and_straight_without` (81 types), `test_default_on_a_curved_preset_covers_at_margin_zero_and_straight_is_the_former_result` (126 and 112 tiles), `test_invalid_outline`.

Local checks: ruff check, ruff format, mypy, `scripts/make_doc_figures.py --check` (up to date), strict docs build; the full suite and CI are reported in the PR.

## Deviations and open questions

- The curved test is the exact overlap of the sampled polygon, not of the true Bezier curves; the sampling is the one of `outlines()`, so the tiles that the user draws are the tiles that are tested.
- The region of the issue's test idea ("sampled points") is checked exactly instead.
- carto-flow needs no argument for the curved tilings, and passes `outline="straight"` only if it wants the former tile set (it costs 0.5 to 1 s less for 10,000 tiles).

Regenerate the figure from an isotile checkout of the branch: `uv run --with matplotlib python <this directory>/make_figures.py`.
