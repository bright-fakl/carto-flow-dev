---
pr: 102
url: https://github.com/bright-fakl/carto-flow/pull/102
issue: 72
title: Fix MosaicLayout symbol size for non-hexagon tilings
description: Mosaic symbols are now drawn at the tile's size for every tiling, so they no longer overlap; HexagonTiling output is unchanged. Left is main, right is the fix.
branch: fix/mosaic-symbol-size
base: main
date: 2026-10-08 16:54
before: main
after: fix/mosaic-symbol-size @ 400d72f
inputs: US states (bundled census; tile_count = round(Population / 2e6), min 1), congressional districts grouped by state (bundled), spacing=0.0, morph=False
---

`MosaicLayout` set `base_size` to the tiling's `tile_size`, which is only the
symbol size for `HexagonTiling`. It now uses
`Tiling.symbol_size_for_tile_size(tile_size)`, the inverse of
`tile_size_for_symbol_size`. `HexagonTiling` output is bit-identical (max
coordinate difference 0.0 in all three modes).

Overlapping symbol pairs (pairwise intersection area above 1e-6 of the mean
symbol area):

| Tiling | one tile/region before | after | `tile_count` before | after | `group_by` before | after |
|---|---|---|---|---|---|---|
| HexagonTiling | 0 | 0 | 0 | 0 | 0 | 0 |
| SquareTiling | 152 | 0 | 577 | 0 | 1571 | 0 |
| TriangleTiling.equilateral | 216 | 0 | 845 | 0 | not run | not run |
| QuadrilateralTiling.rhombus | 148 | 0 | 573 | 0 | not run | not run |
| Isohedral scalloped_hexagon | 213 | 0 | 830 | 0 | 2312 | 0 |
| Isohedral wavy_square | 149 | 0 | 578 | 0 | not run | not run |

Each figure shows main on the left and the fix on the right. `group_by`
figures use congressional districts grouped by state.

figure: one_tile_SquareTiling.png — one tile per region, SquareTiling
figure: one_tile_TriangleTiling_equilateral.png — one tile per region, TriangleTiling.equilateral()
figure: one_tile_QuadrilateralTiling_rhombus.png — one tile per region, QuadrilateralTiling.rhombus()
figure: one_tile_Isohedral_scalloped_hexagon.png — one tile per region, IsohedralTiling scalloped_hexagon
figure: one_tile_Isohedral_wavy_square.png — one tile per region, IsohedralTiling wavy_square
figure: one_tile_HexagonTiling.png — one tile per region, HexagonTiling (unchanged)
figure: tile_count_SquareTiling.png — tile_count, SquareTiling
figure: tile_count_TriangleTiling_equilateral.png — tile_count, TriangleTiling.equilateral()
figure: tile_count_QuadrilateralTiling_rhombus.png — tile_count, QuadrilateralTiling.rhombus()
figure: tile_count_Isohedral_scalloped_hexagon.png — tile_count, IsohedralTiling scalloped_hexagon
figure: tile_count_Isohedral_wavy_square.png — tile_count, IsohedralTiling wavy_square
figure: tile_count_HexagonTiling.png — tile_count, HexagonTiling (unchanged)
figure: group_by_SquareTiling.png — group_by on congressional districts, SquareTiling
figure: group_by_Isohedral_scalloped_hexagon.png — group_by on congressional districts, IsohedralTiling scalloped_hexagon
figure: group_by_HexagonTiling.png — group_by on congressional districts, HexagonTiling (unchanged)
