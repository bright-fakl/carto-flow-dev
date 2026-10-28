---
pr: 197
title: "isotile pin a4625b7: offset in one pass, curved outline for curved tilings"
description: The isotile pin moves to a4625b7 (fill_region offset, outline for cover and fill_region). Tiling.with_offset passes the offset to fill_region (generate of 10,000 hexagons with an offset takes 0.14 s instead of 0.26 s, bit-identical results), and tilings with curved edges select tiles by the curved outline, which adds boundary tiles for some presets without changing any layout (31 layout cases, footprints identical).
kind: pr
topic: symbol
project: carto-flow
url: https://github.com/bright-fakl/carto-flow/pull/197
branch: isotile-pin-bump
base: main
related: proposal-isotile-adoption, isotile-offset-pr, isotile-curved-cover-pr, isotile-adoption-step-3-pr
date: 2026-10-28 15:10
before: main at 0ef643c with isotile 392484c
after: isotile-pin-bump @ f5c3c10 with isotile a4625b7 (2,092 passed, 2 skipped, 4 xfailed locally)
inputs: carto-flow 0ef643c against f5c3c10; isotile 392484c (old pin) against a4625b7; Python 3.10.18, numpy 2.2.6, scipy 1.15.3; bundled census data (49 states, 432 districts, EPSG:102008) and the 10 x 10 grid of step 3; 16-core WSL2 machine. Layout runs are single runs one after the other, mosaic with morph=False. Timings of generate are the best of 7.
---

Follows [isotile-offset-pr](../isotile-offset-pr/index.html) (isotile PR 8, [isotile#7](https://github.com/bright-fakl/isotile/issues/7)) and [isotile-curved-cover-pr](../isotile-curved-cover-pr/index.html) (isotile PR 9, [isotile#6](https://github.com/bright-fakl/isotile/issues/6)) for the adoption in [proposal-isotile-adoption](../proposal-isotile-adoption/index.html). Both isotile changes are in `a4625b7`.

## What changed

- `pyproject.toml` and `uv.lock`: the rev of isotile (`uv.lock` edited by hand; `uv lock --locked` and `uv sync --frozen` pass). The wheel-smoke-test step reads the rev from `pyproject.toml` and is unchanged. No other file mentions the old rev.
- `Tiling.with_offset`: `_IsotileTiling.generate` calls `fill_region(..., offset=self._offset)`. The second pass (`with_frame` and a second `cover`) is deleted.
- Tilings with curved edges: isotile's `outline=None` now selects tiles by the curved outline for a tiling with at least one edge curve. carto-flow takes the default. The module docstring, `Tiling.generate`, `docs/explanations/tiling-system.md` and the changelog (breaking changes of 3.0.0) state it.
- Tests: `tests/test_tilings_golden.py` no longer exempts the curved presets (every tile of the former implementation is returned for all 15 presets and 81 types, and every tile it did not return overlaps the region), `test_curved_presets_select_tiles_by_the_curved_outline` (9 presets) and `test_curved_outline_adds_tiles_at_the_boundary` (112 to 126 tiles); `tests/test_tiling_lattice_options.py` compares `generate` with an offset to `fill_region(offset=...)` (tile cells, aspects and transforms equal). The golden fixtures need no change: they hold the tiles of the former class that overlap the region, and the new tile sets contain all of them.

## Offset in one pass: identity and time

[tiling_identity.py](tiling_identity.py): 26 tilings (square, hexagon pointy and flat, two triangles, two quadrilaterals, 15 presets, types 1, 7, 41, 93) x 2 regions (one at the origin, one 8e6 away) x 3 sizes (`n_tiles` 100 and 37, `tile_size`) x 2 margins x 2 rotations x 6 offsets = 3,744 cases. Per case the polygon coordinates, tile transforms, edge and vertex-only adjacency, tile size and inscribed radius are compared exactly. Runs: A = main with isotile 392484c, B = main with a4625b7, C = this branch with a4625b7.

| comparison | result | file |
|---|---|---|
| B against C (the offset refactor alone) | 3,744 of 3,744 identical | [tiling_identity_B_vs_C.txt](tiling_identity_B_vs_C.txt) |
| A against C, 17 non-curved tilings (square, hexagon, triangles, quadrilaterals, 6 straight presets, 4 types) | all 144 cases of each identical | [tiling_identity_A_vs_C.txt](tiling_identity_A_vs_C.txt) |
| A against C, 9 curved presets | 30 to 129 of 144 cases differ per preset (more tiles at the boundary), see the next section | same file |

Layout level: [offset_compare.py](offset_compare.py) on the offset cases of the [step 3 experiments](../isotile-adoption-step-3-pr/experiments.py) (grid and mosaic of the states with hexagon and square, offsets (0, 0), (0.25, 0.25), (0.5, 0.5), and the mosaic with rotation 30 centered and moved): assignments, regions, tile polygons and tile size identical in all 14 cases, main with the old pin against the branch ([offset_identity_output.txt](offset_identity_output.txt)). The tests of `tests/test_tiling_lattice_options.py` pass.

Time of `generate`, 9,919 to 9,960 hexagons, region (0, 0, 100, 60), margin 0.1, best of 7, two rounds ([time_generate.py](time_generate.py), [timing.txt](timing.txt)):

| | no offset | offset (0.3, 0.6) |
|---|---|---|
| main, isotile 392484c | 0.138 and 0.144 s | 0.252 and 0.260 s |
| main, isotile a4625b7 | 0.142 and 0.146 s | 0.256 and 0.280 s |
| branch, isotile a4625b7 | 0.139 and 0.143 s | 0.139 and 0.142 s |

The second pass cost 0.11 to 0.14 s; with the offset in `fill_region` the time equals the time without an offset.

## Curved tilings: tile sets

Default outline now curved (isotile#6). For `fill_region((0, 0, 10, 6), n_tiles=100, margin=0.1)`, tiles before (straight outline) and now: `puzzle_piece` 112 and 126, `arrow_quad` 112 and 124, `wavy_triangle` 114 and 132, `flowers` 121 and 123.

figure: fig_curved_tilings.png — The four presets, straight-outline tiles (left, the former selection) and curved-outline tiles (right); orange tiles are selected only by the curved outline, the red rectangle is the region with margin ([make_tiling_figure.py](make_tiling_figure.py)).

Across the 3,744 tiling cases the tile totals of A and C differ for 9 curved presets only (for example `interlocking_hexagon` 13,779 to 14,964, `puzzle_piece` 13,530 to 14,114, `wavy_triangle` 14,206 to 14,753); all other tilings have the same totals ([tiling_identity_A_vs_C.txt](tiling_identity_A_vs_C.txt)).

## Curved tilings: layouts

[layout_cases.py](layout_cases.py) (the script of step 1, extended): the 15 cases of the step 1 and step 3 pages and 16 new ones, `puzzle_piece`, `wavy_triangle`, `flowers`, `arrow_quad` on the states and the districts, grid and mosaic (districts grouped by state), `morph=False`, [layouts_oldpin.log](layouts_oldpin.log) (main, 392484c), [layouts_newpin.log](layouts_newpin.log) (main, a4625b7), [layouts_branch.log](layouts_branch.log). Acceptance rule of step 1: the mean distance may change by the larger of 25 percent of the old value and, for the states grid layouts, the range of the same metric over six lattice offsets of the same tiling (old and new pin together: [phase_oldpin.log](phase_oldpin.log), [phase_newpin.log](phase_newpin.log)). Unassigned core tiles are given for the mosaic cases; the split regions column is the number of regions with more than one edge-connected block of tiles (mosaic: the layout's own count of non-contiguous regions).

Results:

- Main with the new pin against the branch: assignments identical in all 31 cases ([layout_B_vs_branch.md](layout_B_vs_branch.md)): the offset refactor changes nothing at layout level.
- Main with the old pin against the branch ([layout_table.md](layout_table.md)): the 15 cases of the earlier pages, including the `scalloped_hexagon` cases, have identical assignments. Of the 16 new cases 11 have identical assignments; 5 have more lattice tiles (states grid `puzzle_piece` 160 to 188, `flowers` 165 to 171, `arrow_quad` 160 to 174; states mosaic `wavy_triangle` 490 to 524; districts mosaic `wavy_triangle` 1,210 to 1,264) so that the tile indices differ. In all 31 cases every region gets the same tile polygons ([footprints.py](footprints.py), [footprints_table.md](footprints_table.md)): the additional tiles lie in the margin band and no region uses them. The mean distance, split regions and unassigned core tiles are equal in every case (change 0 percent, all within the tolerance).
- Wall times, single runs, the same within the noise of the machine (states mosaic 1.0 to 2.3 s, districts mosaic 3.5 to 7.0 s, grid 0.3 to 2.7 s); the largest differences are 1.1 s (districts `scalloped_hexagon`, 5.2 and 6.3 s) and 0.7 s (states mosaic `wavy_triangle`, 2.3 and 3.0 s).

Lattice-phase range of the states grid layouts with the curved presets (mean distance over six offsets, both pins): 0.73 to 1.16 for all presets, except `tree` at offset (0.9, 0.1): 1.68 with the new pin and 1.10 with the old pin (the tile set differs). This does not enter the layouts above, which use the default offset.

No layout changes, so no side-by-side layout figures; the only visible change is the tile set of `generate` (figure above). `morph=True` layouts are not compared (flow morph has numba noise of 1e-16).

Decision: the default is accepted. Passing `outline="straight"` in the calls of carto-flow would keep `n_tiles` of `generate` equal to main for the curved presets (112 instead of 126 for `puzzle_piece`) and changes no layout either; it was not implemented because nothing needs it.

## Checks

2,092 passed, 2 skipped, 4 xfailed (full suite); `ruff check`, `ruff format`, `mypy src`, `deptry src` pass.
