---
issue: 159
title: Design of the standalone isohedral tiling library (replacing tactile)
description: Prototype of the core (81 types, fill, lattice adjacency; 1,143 tests pass against tactile and against geometric adjacency), the mapping of square, hexagon, triangle and quadrilateral tilings to types IH76, IH20, IH84 and IH46 (all 19 named carto-flow cases reproduced, any triangle and simple quadrilateral expressible), the finding that valid custom curves never change the lattice neighbors (243 of 243 trials) while carto-flow's tolerance and its validity repair do, and the specification of the remaining work.
kind: proposal
topic: symbol
status: open
related:
date: 2026-10-26 23:48
inputs: tactile 0.1.0 (BSD 3-Clause, Craig S. Kaplan), the 81 types, parameters = defaults plus uniform noise of 0.05 to 0.3 (valid draws only), carto-flow main at 408284b, isohedral-tiling-ui (read only), Python 3.12, numpy 2.3.3, scipy 1.16.2, shapely 2.1.2 (GEOS 3.13.1). Single runs; benchmark timings on a 16-core WSL2 machine with other jobs running.
---

This page continues the design of issue 159. The first version (earlier today) fixed the scope and showed by a spike that adjacency is a per-type table. This version adds a working prototype of the core, the mapping of carto-flow's four convenience tilings onto isohedral types, a test of the open question about custom edge curves and the validity repair, and the specification of the work that remains. Section 10 lists the decisions that are still open; section 9 lists what was not verified.

Files in this directory:

| File | Content |
|---|---|
| [spike.py](spike.py), [spike2.py](spike2.py) | first spike: adjacency table independent of parameters, timing |
| [bright-fakl/isotile @ 097ae26](https://github.com/bright-fakl/isotile/tree/097ae26) | package `isotile_proto` (core), `tests/`, `bench.py`; the prototype now lives in this repository, local clone `/home/fakl/isotile` |
| [bench_output.txt](bench_output.txt) | output of `bench.py` |
| [mapping_evidence.py](mapping_evidence.py), [mapping_evidence.txt](mapping_evidence.txt) | carto-flow's four tiling families against the prototype (section 3) |
| [curve_adjacency.py](curve_adjacency.py), [curve_adjacency.txt](curve_adjacency.txt) | custom edge curves and validity repair against the lattice table, 81 types (section 4) |
| [symmetry_compare.py](symmetry_compare.py), [symmetry_compare.txt](symmetry_compare.txt) | carto-flow's and the UI's symmetry and spline code compared (section 8.1) |

Commands (run from this directory; the package needs only numpy and scipy, the tests also tactile, the evidence scripts carto-flow):

```
cd /home/fakl/isotile && uv run --project /home/fakl/carto-flow python -m pytest
PYTHONPATH=/home/fakl/isotile uv run --project /home/fakl/carto-flow python mapping_evidence.py
PYTHONPATH=/home/fakl/isotile uv run --project /home/fakl/carto-flow python curve_adjacency.py
PYTHONPATH=prototype uv run --project /home/fakl/carto-flow python /home/fakl/isotile/bench.py 1000 10000
```

## 1. Results in short

| Question | Result |
|---|---|
| Does the prototype reproduce tactile? | Yes for all 81 types: vertices, aspects, translation vectors, edge transforms, edge reversals, edge shapes and colorings at the defaults and at random parameters. `fill` returns the same tiles in the same order as tactile's scanline fill, minus repeats (tactile repeated tiles in 39 of 486 random regions). |
| Is the lattice adjacency table correct? | Yes: it equals shared-vertex counting on a patch for all 81 types, at the defaults and at three perturbation sizes (0.05, 0.15, 0.3). The tables have 2,452 rows in total; the largest lattice offset is 2. |
| Test result | 1,143 passed, 78 skipped (the 26 types without parameters have nothing to perturb, 3 sizes each), 0 failed; 20 s. |
| Do square, hexagon, triangle and quadrilateral tilings map to types? | Yes: IH76 (IH41 when curves are wanted), IH20 (IH10), IH84, IH46, each with an affine frame. All 19 named cases of carto-flow are reproduced (tile polygons to 2e-11 of the tile size, adjacency, rotation and flip). Any triangle and any simple quadrilateral is expressible (300 random shapes each, 0 failures). |
| Do custom curves change the lattice neighbors? | Not when the prototile polygon is simple: 0 differences in 243 of 243 trials, all 81 types. They do when it self-intersects and carto-flow repairs it with `make_valid`: 164 of 213 trials differ. |
| Is carto-flow's geometric adjacency of curved tiles correct? | No: with its tolerance of 0.01 times the tile size it reports vertex-only contacts as edge contacts in 57 of 243 trials (33 types). The lattice table does not have this error. |
| Speed | Lattice adjacency of 10,300 tiles takes 0.0055 s; carto-flow's geometric method takes 3.1 s for 11,019 tiles (about 530 times per tile). Section 6. |

## 2. Findings that shape the design

`spike.py` and `spike2.py` (first version of this page) generate a patch for each of the 81 types, find the neighbors of the tile `(0, 0, aspect)` by counting shared vertices (2 or more: edge, exactly 1: vertex only) and compare the result at the default parameters with four perturbed parameter sets. The prototype recomputes the table with its own code (`_build_data.py`) and its tests re-verify it. The figures below come from the stored table:

| Finding | Result |
|---|---|
| Types | 81 |
| Tables that change with the parameters | 0 of 81 (spike: 4 draws of up to 0.15; prototype tests: 3 sizes, up to 3 draws each) |
| Edge neighbors per tile | equal to the number of prototile vertices, for every type and aspect (3 to 6) |
| Largest lattice offset of any neighbor | 2 |
| Vertex-only neighbors per tile | 0 (35 type-aspect pairs) to 18 (18 pairs) |
| Aspects per type | 1 (17 types), 2 (27), 3 (6), 4 (20), 6 (8), 8 (2), 12 (1) |
| Free parameters per type | 0 (26 types), 1 (15), 2 (21), 3 (9), 4 (7), 5 (2), 6 (1) |

Consequences:

- Adjacency of a tiling is computed from `(t1, t2, aspect)` alone with a table that is part of the type data. It does not depend on the parameters, the scale or the position of the tiling.
- Tiles must carry their lattice coordinates through the generation. The current carto-flow tiling drops them (`TileTransform` has center, rotation and flip only), which is why adjacency is found geometrically today.
- The tactile data has no valid parameter ranges. The prototype accepts any finite parameters for which the prototile is a simple polygon (non-zero edge lengths, non-zero area, no crossing or touching non-adjacent edges) and rejects the rest with `ValueError`, keeping the previous state.

## 3. Square, hexagon, triangle and quadrilateral tilings as isohedral types

Evidence: [mapping_evidence.txt](mapping_evidence.txt). The named constructors are in `isotile_proto/families.py` in the repository. For each carto-flow case, `generate(bounds=(-1, -1, 1, 1), tile_size=s, margin=0.1)` was compared with the library tiling that has the same prototile: tile polygons (largest vertex distance of matched tiles, relative to the tile size), edge and vertex-only adjacency over the matched tiles, rotation and flip of each tile, tile counts and coverage of the region. Overlay operations of shapely were avoided for polygon comparison because GEOS 3.13.1 returns a wrong intersection area for two polygons whose shared vertex differs by 1e-17 (seen in a first version of this script).

### Mapping

| carto-flow | Type | Parameters | Frame (affine map applied to the type's native geometry) |
|---|---|---|---|
| `SquareTiling` | IH76 (all edges I, 1 aspect); IH41 at its defaults (0.231, 0.5) is the same unit square with two J edges | none | scale by the side length, translate |
| `HexagonTiling(pointy_top=True)` | IH20 (I edges); IH10 (J), IH11 (S) and IH18 (U) have the same hexagon | none | scale by the circumradius, rotate by 30 degrees (the types are flat-top: a vertex at angle 0) |
| `HexagonTiling(pointy_top=False)` | the same | none | scale only |
| `TriangleTiling` (`equilateral`, `right_isosceles`, `right`, `isosceles`, `from_polygon`) | IH84 (three S edges, 2 aspects related by a 180 degree rotation about an edge midpoint) | 2: the apex is `(5 p0 - 2, 3.9 p1 + 0.1)` over the base `(0, 0)-(1, 0)`; solved by linear least squares | the similarity (rotation, scale, translation, no reflection) that maps the native base onto the longest edge of the requested triangle |
| `QuadrilateralTiling` (`parallelogram`, `rectangle`, `rhombus`, `trapezoid`, `from_polygon`) | IH46 (four S edges, 2 aspects) | 4: vertex 2 is `(5 p0 - 1.5, 3.9 p1 + 0.1)`, vertex 3 is `(5 p2 - 2.5, 5 p3 - 1.5)`; solved the same way | the same similarity |

An arbitrary triangle or simple quadrilateral needs no further type: the 180 degree rotation about every edge midpoint is the symmetry of IH84 and IH46, the tiling of a polygon by such rotations is unique, and the parameters only choose the shape. A clockwise input is handled by reversing the vertex order. With the longest edge as the base, the parameters stay small (largest absolute value 0.6 for triangles and 0.7 for quadrilaterals in 300 random shapes each).

Square and hexagon have no free shape, so IH76 and IH20 (straight edges) or IH41 and IH10 (curves possible) are used. IH10 and IH20 have the same hexagon but different second translation vectors, so their lattice coordinates differ; saved tilings must keep their own type number.

### Evidence

| Check | Result |
|---|---|
| 19 named cases: square, hexagon (both flag values, each compared with the pointy-top library hexagon, see item 3), 7 triangles, 9 quadrilaterals including a non-convex one and a clockwise triangle | tile polygons equal (largest vertex distance 1e-14 of the tile size; 2e-11 for the hexagon because tactile's hexagon coefficients have 12 digits); edge and vertex-only adjacency equal over all matched tiles (0 differing pairs); rotation and flip equal for every matched tile; tile area equals the requested area (ratio 1) |
| Random shapes against carto-flow (60 triangles, 60 simple quadrilaterals, `tile_size` 0.25) | 0 carto-flow tiles without a library match, 0 adjacency differences, 0 rotation or flip differences, largest vertex distance 4.5e-14 |
| Expressibility (300 random triangles, 300 random simple quadrilaterals, vertices uniform in [-1, 1]^2) | 0 construction failures; the prototile equals the requested polygon (vertex distance 5e-15); lattice adjacency equals geometric adjacency on a patch for every shape |
| `IsohedralTiling.generate` against the library's `fill` with the same native bounds, all 81 types at the defaults | same tile count, same tiles in the same order, same edge and vertex-only adjacency for 81 of 81 |
| A self-intersecting quadrilateral `(0,0) (2,1) (1,0) (0,3)` | the library rejects it (`ValueError`); carto-flow accepts it and returns 110 tiles, all invalid polygons |

### Mismatches found

1. **Tile selection at the boundary differs by class, and carto-flow returns more tiles than meet the region.** With the same bounds, carto-flow returns up to 29 percent more tiles than meet the padded region: square 144 against 144, unit rectangle 169 against 169, hexagon 195 against 175, triangles 4 to 20 percent more, other quadrilaterals 6 to 29 percent more. The library's `cover` returns exactly the tiles whose bounding box meets the region. Each class's rule can be reproduced with a filter on the tile centroids (square: lower-left corner in `[min, max)`; hexagon: center in `[min, max + step)`; triangle and quadrilateral: centroid within one tile size of the padded region): the filter on top of `cover` gave carto-flow's exact tile set in 19 of 19 named cases, 51 of 60 random triangles and 57 of 60 random quadrilaterals. The remaining shapes are those where carto-flow has holes (item 4).
2. **The position of the lattice differs by class.** Square: the first tile has its lower-left corner at `(min_x, min_y)` of the padded region. Hexagon: the first tile center is `(min_x, min_y)`. Triangle and quadrilateral: the centroid of the first tile is the origin, independent of the bounds. `IsohedralTiling`: the native origin is the center of the padded region. The wrappers set the frame so that the same tiles are produced; the library has no preferred position.
3. **`HexagonTiling(pointy_top=False)` generates pointy-top tiles.** `generate` never reads the flag (the first tile has the same bounds for both values in the output), only `canonical_symbol` does, so tiles and symbols disagree today. The library's `hexagon(pointy_top=False)` is flat-top (width 0.2400, height 0.2078 at circumradius 0.12; pointy-top: 0.2078 by 0.2400). Adopting the library changes the output for users who pass `pointy_top=False`.
4. **`TriangleTiling` and `QuadrilateralTiling` leave holes for elongated shapes.** The lattice index range `ceil(max_extent / |vec|) + 2` and the centroid filter drop tiles that overlap the region. Of 60 random triangles, 45 had a sampled hole in the padded region (11 with more than 1 percent of the region uncovered, worst 32 percent); of 60 random quadrilaterals, 39 (4 with more than 1 percent, worst 38 percent); 760 and 462 region tiles were missing. The 19 named cases show no sampled hole, but one tile of the clockwise scalene triangle that overlaps the region by 0.4 percent of its area is missing. The library's `cover` has no hole in the 19 named cases (sampled coverage 1, no overlap); it covers by construction (lattice range from the prototile extent), but that was not tested on the random shapes.
5. **Size normalization differs by class**, which the wrappers keep: `tile_size` is the side (square), the circumradius (hexagon, area `3 sqrt(3) / 2 * tile_size^2`) and `sqrt(area)` (triangle, quadrilateral, isohedral).
6. **Not compared:** the starting vertex and winding of each tile polygon (the library's prototile is counterclockwise and starts at the type's first vertex; carto-flow keeps the input order). Code that indexes polygon vertices by position, and `n_base_vertices`, need a look when the wrappers are written.

The adjacency convention is the same: `adjacency` is edge-only with `TileAdjacencyType.EDGE` and edge-or-vertex with `VERTEX`, `vertex_adjacency` is vertex-only. The hexagon has 6 edge neighbors and no vertex-only neighbors, the square 4 and 4.

## 4. Do custom edge curves or the validity repair change the lattice neighbors?

Evidence: [curve_adjacency.txt](curve_adjacency.txt). For each of the 81 types, carto-flow's `IsohedralTiling` was built with parameters = defaults plus uniform(-0.08, 0.08) and random curves on every J, U and S shape (1 to 4 control points, spline interpolation, `generate` with about 40 requested tiles and `margin=0`). Tiles were identified by recording the `(t1, t2, aspect)` of tactile's fill and replaying carto-flow's filter, so the lattice table applies to exactly the tiles carto-flow returned. The table adjacency was compared with (a) carto-flow's own result (tolerance 0.01 times the tile size) and (b) the shared-vertex count of the same polygons with a tolerance of 1e-7 times the tile size. Three regimes, three trials per type each:

- `valid`: amplitude reduced (start 0.25 of the edge length, factor 0.6) until the prototile polygon is simple, so no repair happens. The 9 types with only I edges (20, 32, 37, 40, 72, 76, 77, 82, 93) are controls without curves.
- `repair`: amplitude increased (start 0.25, factor 1.5) until the prototile self-intersects; carto-flow warns, applies `make_valid` and keeps the largest part.
- `extreme`: amplitude 1.5 times the edge length.

| Regime | Types | Trials (aligned) | Tiles | Repaired tiles | Trials that differ from the lattice table, carto-flow tolerance | Same, tight tolerance |
|---|---|---|---|---|---|---|
| valid | 81 | 243 | 29,162 | 0 | 57 | 0 |
| repair | 72 | 213 | 25,508 | 26,618 | 163 | 164 |
| extreme | 72 | 211 | 25,164 | 22,064 | 164 | 161 |

The repaired-tile count can exceed the tile count because tiles are repaired before carto-flow's area filter and deduplication drop some. Three and five trials in the last two rows could not be aligned to carto-flow's tile order and are excluded.

Results:

1. **Valid curves do not change the neighbors.** With exact vertex matching, the geometric adjacency of the curved tiles equals the straight-edge lattice table in 243 of 243 trials, for all 72 types that have a J, U or S edge and the 9 controls. All tiles share the same curve on a shared edge, and the test confirms this for splines.
2. **carto-flow's geometric method is wrong for curved tiles at its tolerance.** In 57 of 243 valid trials (33 types, listed in the output) it turns vertex-only contacts into edge contacts: in each of these trials, the pairs that are vertex-only in the table appear as edge pairs and no pair is lost. With a tolerance of 1e-7 the difference disappears, so the cause is the tolerance against the 100 sample points per curve, not the topology. `TilingResult.adjacency` of a curved isohedral tiling therefore has too many edge pairs today (the grid layout passes this matrix on); the lattice table removes this.
3. **The validity repair does change the neighbors.** For self-intersecting prototiles, 164 of 213 trials (77 percent) differ from the table even with the tight tolerance. Tiles lose edge contacts (the shared curve is no longer on the kept part) and some edge pairs become vertex-only. The table then describes the intended tiling, not the repaired polygons. In 542 (repair) and 590 (extreme) tiles the centroid of carto-flow's repaired polygon differs from the one recomputed from the same construction; the likely cause is that `make_valid` selects the other of two equal-area parts when floating-point rounding differs, which would make the repaired result unstable under tiny coordinate changes (not isolated).

Conclusion: the lattice table is correct for every tiling whose prototile is simple, with or without curves. For a self-intersecting prototile there is no tiling in the geometric sense; the library should detect this (`prototile_is_valid`), and the policy (warn and repair as now, or raise) is a decision (section 10).

Not tested: the `linear` curve mode (control points used without interpolation), curves with more than 4 control points, amplitudes other than the stepwise search above, more than 3 trials per type and regime, parameters further than 0.08 from the defaults, and the effect of the false edge pairs on the results of the layouts.

## 5. Prototype of the core

Repository [bright-fakl/isotile](https://github.com/bright-fakl/isotile/tree/097ae26) (commit 097ae26): about 700 lines of code in `isotile_proto/` and 235 in `tests/`. The package imports only numpy and scipy; ruff with carto-flow's rule set passes.

| File | Content |
|---|---|
| `isotile_proto/types.py` | `TilingType` (frozen dataclass of arrays), `get_type`, `tiling_types`, loader of `data/types.npz` |
| `isotile_proto/tiling.py` | `IsohedralTiling`, `TileSet`, the vectorized port of tactile's scanline fill, `cover` |
| `isotile_proto/adjacency.py` | `lattice_adjacency` (table lookup) and `geometric_adjacency` (shared vertices, vectorized) |
| `isotile_proto/families.py` | `square`, `hexagon`, `triangle`, `quadrilateral` (section 3) |
| `isotile_proto/_build_data.py` | exports the 81 types from tactile into `data/types.npz` and computes the adjacency tables with the prototype's own code; its header carries the BSD 3-Clause notice of Craig S. Kaplan, `data/LICENSE-tactile` sits next to the data |
| `tests/test_equivalence.py` (732 tests), `tests/test_adjacency.py` (489) | see below |
| `bench.py` | benchmark (section 6) |

### What it does

- Vertices, aspect matrices and translation vectors are `coeffs @ [*params, 1]`; edge transforms are tactile's `matchSeg` times the orientation matrix, for all edges at once. Parameters are an array-like stored as `float64`, validated on assignment (length, finiteness, simple prototile); the previous state is kept when validation fails.
- `frame` (optional (2, 3) affine map) maps the vertices, translation vectors and edge transforms and conjugates the aspects, so one type serves all scales, rotations and positions. The four families use it.
- `fill(bounds)` reproduces tactile's scanline fill (including its treatment of the lower and upper edge and the extra top row) in numpy and returns the first occurrence of each tile in tactile's order. `cover(bounds)` returns all tiles whose bounding box meets the rectangle. `tiles(lattice)` builds tiles from given lattice coordinates.
- `TileSet` has `lattice` (n, 3), `transforms` (n, 2, 3), `vertices()` (n, nv, 2), `centroids`, `colors()` (tactile's `get_color`), `adjacency(kind)` and `neighbors(i, kind)`.
- Adjacency: key `((t1 - t1_min) * W + (t2 - t2_min)) * n_aspects + aspect` per tile, one `np.searchsorted` per table row, result a scipy `csr_array` of bool. The table has the rows `(aspect, d_t1, d_t2, neighbor_aspect, kind)` per type (kind 0: edge, 1: vertex only). `geometric_adjacency(polygons, tol)` merges vertices within `tol` with a KD-tree and counts shared vertices through a sparse incidence product.

### Tests

| Test | Cases |
|---|---|
| Vertices, aspects, t1, t2, edge transforms and edge reversals against tactile | 81 types at the defaults; 5 random draws within 0.15 of the defaults per type with parameters |
| Edge shapes, shape ids, type numbers, counts of vertices, aspects and parameters | 81 types |
| `fill` against tactile (same tiles, same order, same transforms) | 81 types × 3 seeds × (defaults and one random draw) = 486 regions; tactile had repeats in 39 of them |
| `fill` has no repeats; `cover` equals the tiles of a larger `cover` that meet the rectangle (a consistency check only; independent evidence for `cover` is the comparison with carto-flow in section 3) | 81 types each |
| Tile colors against `get_color` | 81 types, 81 cells × aspects |
| Lattice adjacency (edge, vertex-only, vertex) equals geometric adjacency on a patch of 150 to 400 tiles | 81 types at the defaults; perturbation sizes 0.05, 0.15, 0.3 with up to 3 draws each for the 55 types with parameters (78 skipped cases are the 26 types without parameters) |
| Edge neighbor count equals the vertex count for interior tiles; table offsets at most 2; adjacency symmetric | 81 types |
| Parameter and type validation, square and hexagon neighbor counts, `neighbors`, `kind` validation | 6 tests |

Result: 1,143 passed, 78 skipped, 0 failed in 20 s.

## 6. Benchmark

`bench.py` in the repository, output in [bench_output.txt](bench_output.txt): tiles of one type (IH7 hexagon, IH46 quadrilateral, IH84 triangle) in a square region of about 1,000 and 10,000 tiles. Library times are the best of 3 runs (2 for the geometric method), carto-flow times one run. "carto-flow generate" is `IsohedralTiling.generate(compute_adjacency=False)` (shapely polygons and the pairwise deduplication); "carto-flow geometric adjacency" is `_compute_adjacency_matrices` on its polygons. carto-flow's `n_tiles` yields 6 to 30 percent more tiles than the library's region, so the speedups are per tile.

| Type | Tiles (library) | Tiles (carto-flow) | Library: tiles and vertex arrays | Library: lattice adjacency | Library: geometric adjacency | carto-flow: `generate` | carto-flow: geometric adjacency | Speedup per tile: lattice | Speedup per tile: library geometric |
|---|---|---|---|---|---|---|---|---|---|
| IH7 | 1,068 | 1,290 | 0.0054 s | 0.0015 s | 0.0087 s | 4.7 s | 0.31 s | 171x | 30x |
| IH7 | 10,300 | 11,019 | 0.0509 s | 0.0055 s | 0.0734 s | 590.9 s | 3.10 s | 527x | 39x |
| IH46 | 1,024 | 1,332 | 0.0039 s | 0.0012 s | 0.0077 s | 5.4 s | 0.44 s | 282x | 44x |
| IH46 | 10,151 | 10,920 | 0.0316 s | 0.0036 s | 0.0588 s | 388.8 s | 3.67 s | 948x | 58x |
| IH84 | 1,118 | 1,374 | 0.0038 s | 0.0009 s | 0.0087 s | 6.0 s | 0.46 s | 416x | 43x |
| IH84 | 10,108 | 10,686 | 0.0254 s | 0.0028 s | 0.0522 s | 344.2 s | 3.79 s | 1280x | 69x |

The lattice lookup is 170 to 1,300 times faster than carto-flow's geometric adjacency per tile and grows linearly (0.0009 to 0.0055 s for 1,000 to 10,000 tiles). The vectorized geometric method in the library (for polygon sets that are not a tiling) is 30 to 70 times faster. carto-flow's `generate` takes 340 to 590 s for 10,000 tiles against 5 to 6 s for 1,000: more than linear growth, consistent with the quadratic deduplication loop (not profiled separately). The library's tiles and vertex arrays take 0.025 to 0.05 s for 10,000 tiles. The timings were taken with other jobs running on the machine.

## 7. Scope and layout

In the library:

1. The 81 types with parameters, vertices, edges, edge shapes (I, J, U, S), aspects, translation vectors, colorings and the lattice adjacency tables.
2. Tile generation in a rectangle (`fill`, `cover`) and from lattice coordinates; named constructors for the square, hexagon, triangle and quadrilateral tilings (module functions in the prototype, classmethods `IsohedralTiling.square(...)` etc. in the library); an affine frame.
3. Adjacency from the lattice (edge, vertex, vertex-only, neighbors of a tile) and a geometric method for arbitrary polygon sets.
4. Edge curves: storage, symmetry, interpolation, prototile outline, validity detection and repair (section 8.1).
5. `to_dict` / `from_dict` / `save` / `load` in the existing parameter format, preset names, `type_info`, `find_types`.
6. Plotting of tiles and prototiles (matplotlib extra).

Not in the library: anything that imports `carto_flow`; a GUI; symbols and symbol sizing.

Modules (written in the prototype: `types`, `tiling`, `adjacency`, `families`, `_build_data`):

```
isotile/
  __init__.py     public API
  types.py        TilingType, get_type, tiling_types, find_types, info()
  tiling.py       IsohedralTiling, TileSet, fill, cover
  adjacency.py    lattice_adjacency, geometric_adjacency
  families.py     square, hexagon, triangle, quadrilateral
  edges.py        EdgeShape, enforce_symmetry, is_symmetric, interpolate      (phase 2)
  curves.py       prototile outline, edge outlines, validity check and repair  (phase 2)
  presets.py      the 15 presets                                               (phase 2)
  io.py           to_dict / from_dict / save / load                            (phase 2)
  plot.py         matplotlib helpers (extra)                                   (phase 2)
  data/           types.npz (81 types with adjacency tables), LICENSE-tactile
  _build_data.py  regenerates data/ from tactile (development only)
```

## 8. What remains (not implemented)

### 8.1 Edge-curve layer

Move into the library from `symbol_cartogram/tiling.py` (line numbers at carto-flow 408284b):

| carto-flow | Library | Public API |
|---|---|---|
| `IsohedralTiling.__init__` (1576): type, parameters, `edge_curves`, `edge_curve_modes`, unit-area normalization | `IsohedralTiling.__init__` without the normalization | `IsohedralTiling(tiling_type, parameters=None, *, edge_curves=None, edge_curve_modes=None, frame=None)`; `edge_curves` maps a shape id to (m, 2) points from (0, 0) to (1, 0); mode `"spline"` (default) or `"linear"` per shape id |
| `_enforce_edge_symmetry` (1622) | `isotile.edges.enforce_symmetry` | `enforce_symmetry(points, shape) -> ndarray (m, 2)` and `is_symmetric(points, shape, tol=1e-9) -> bool`. I returns the segment, J the input; S and U keep the first half by x and mirror it (carto-flow's tests `test_edge_curves_s_symmetry` and `_u_symmetry` require that raw curves are symmetrized); a curve that already has the symmetry of its shape is kept unchanged (see below) |
| `_interpolate_curve` (1707) and UI `utils/spline_cache.py` | `isotile.edges.interpolate` | `interpolate(points, mode="spline", n_points=None) -> ndarray`; parametric natural cubic spline on the chord-length parameter; `n_points` defaults to `max(100, 10 * len(points))` (the UI's rule; carto-flow uses 100) |
| `_build_prototile` (1668) | `IsohedralTiling.prototile` | `prototile(curved=True) -> ndarray (m, 2)`, the closed outline without the repeated first point; uses `edge_transforms`, `edge_reversed` and the shape ids |
| per-edge curve drawing in UI `prototile_editor._update_edge_curves` (911 to 955) | `IsohedralTiling.edge_outlines` | `edge_outlines(curved=True) -> list[ndarray]`, one polyline per edge in world coordinates; `edges: list[EdgeInfo]` with shape id, shape and reversal |
| the self-intersection warning in `__init__` (1606) | `IsohedralTiling.prototile_is_valid` | `prototile_is_valid -> bool`; the constructor warns as today |
| the repair block in `generate` (2715 to 2729): `make_valid`, keep the largest part, drop non-polygons and areas below 1e-12 | `TileSet.polygons` | `polygons(curved=True, repair=True) -> list[shapely.Polygon]` (shapely extra), plus `TileSet.repaired` and a `kept` mask. The deduplication loop (2755 to 2770) is not needed because `fill` has no repeats |
| `available_types` (1800), `find_types` (1807) | `isotile.tiling_types`, `isotile.find_types` | `find_types(*, num_vertices=None, num_parameters=None, max_parameters=None, num_aspects=None, has_reflections=None, edge_types=None, all_edges=None, has_customizable_edges=None) -> list[int]`, same filters; computed from `TilingType` without constructing tactile objects |
| `_PRESETS` (1899 to 2126), `from_preset`, `list_presets` | `isotile.presets` | the 15 presets with the same names, type numbers, parameters, curves and modes; `IsohedralTiling.from_preset(name, **overrides)`, `list_presets() -> dict[str, str]` |
| `to_dict`, `from_dict`, `save`, `load` (2169 to 2252) | `isotile.io` and the same methods | `to_dict()` adds `edge_curve_modes` and writes version `"1.1"`; `from_dict` reads 1.0 (no modes) and the UI's files (extra keys `description` and `metadata` ignored) |
| `type_info` (2254), `describe` (2377), `_EDGE_DESCRIPTIONS` | `TilingType.info()`, `IsohedralTiling.info()`, `describe()` | same dict keys; `parameters[i]["affected_vertices"]` computed exactly from `vertex_coeffs[:, :, i]` instead of finite differences |
| `plot_prototile` (2443) and the plotting part of `plot_tile` | `isotile.plot` | `plot_prototile(tiling, ax=None, show_labels=True)`, `plot_tiles(tiles, ax=None, color="coloring")` |

Stays in carto-flow: `Tiling`, `TilingResult`, `TileTransform`, `TileAdjacencyType`, `resolve_tiling` and the registry, `_apply_margin`, `_resolve_generate_args`, `canonical_tile`, `canonical_symbol`, `tile_size_for_symbol_size`, `symbol_size_for_tile_size`, `from_polygon`, `TilingResult.plot`, `plot_tile`, `rotate`, `_plot_polygon_tile`, the symbols (`IsohedralTileSymbol` uses `IsohedralTiling.canonical_tile`) and the four tiling classes as wrappers (8.2).

Stays in `isohedral-tiling-ui`: `get_curve_preset` and `list_curve_presets` (17 curve shapes for the editor), the interactive node rules of `enforce_curve_symmetry`, all Panel and Bokeh code, the history and state. Removed from the UI: `utils/spline_cache.py` (a 3-line `lru_cache` wrapper over `isotile.edges.interpolate` remains), `symmetry.interpolate_curve` (unused), every access to `tiling._ih`.

Two inconsistencies between carto-flow and the UI that the library has to settle ([symmetry_compare.txt](symmetry_compare.txt)):

- **Symmetry rule.** carto-flow takes the first half as the points with `x <= 0.5` and mirrors them; the UI takes it by index and inserts the midpoint `(0.5, 0)` for S edges. On random raw curves with increasing x they gave the same point list in 0 of 400 cases for S and 0 of 400 for U (the two rules expect different inputs: the UI stores the full symmetric curve). For a curve as the UI stores it with a first-half control point beyond `x = 0.5`, `[(0,0), (0.2,0.1), (0.7,0.15), (0.5,0), (0.3,-0.15), (0.8,-0.1), (1,0)]`, carto-flow's rule returns a different 8-point curve. Rule for the library: keep a curve that already has the symmetry of its shape unchanged, otherwise symmetrize by x as carto-flow does.
- **Spline.** Both use a parametric natural cubic spline; carto-flow outputs 100 points, the UI `max(100, 10 n)`. The outputs agree at the common parameters for 5 control points; for 20 control points the counts differ (100 and 200).

Also: carto-flow's `to_dict` drops `edge_curve_modes`. The UI's file has them, but the UI's loader passes `edge_curves` to the constructor without the modes, so a loaded design with `linear` shapes is drawn with splines.

### 8.2 Migration of carto-flow

1. `symbol_cartogram/tiling.py` keeps the public names and signatures: `Tiling`, `SquareTiling`, `HexagonTiling`, `TriangleTiling`, `QuadrilateralTiling`, `IsohedralTiling`, `TilingResult`, `TileTransform`, `TileAdjacencyType`, `resolve_tiling`.
2. The classes become wrappers around `isotile.IsohedralTiling`. Each `generate` builds the frame (scale from `tile_size`, the class's anchor, section 3 item 2), calls `cover` or `fill`, applies the class's current selection filter (section 3 item 1) and converts to `TilingResult`. `IsohedralTiling.generate` uses `fill` with the current native bounds (identical for 81 of 81 types, section 3).
3. `TilingResult` stays a dataclass with the same fields (`polygons`, `transforms`, `adjacency`, `vertex_adjacency`, `tile_size`, `inscribed_radius`, `canonical_tile`, `n_base_vertices`). Added: `lattice` (n, 3) or `None`, and `tile_set`. `adjacency` is densified with `.toarray()` in the first PR; a dense boolean matrix of 10,000 tiles is 100 MB (200 MB with the vertex matrix), so sparse storage is a follow-up (section 10). `TileTransform` values come from the transform arrays with the same formulas (determinant for the flip, `atan2` for the rotation; equal for all matched tiles in section 3).
4. Removed: `_compute_adjacency_from_lattice` and its `_naive` twin, `_compute_adjacency_matrices`, `_compute_adjacency_geometric`, the quadratic deduplication, and the `tactile` dependency in `pyproject.toml` (replaced by `isotile`).
5. Tests that must keep passing: `tests/test_tilings.py` (102 tests, including `TestIsohedralEdgeCurves`, `TestIsohedralPresets`, `TestIsohedralTypeInfo`) and `tests/test_tiling_cartogram.py` (38), then `test_symbol_cartogram_baseline.py`, `_coverage.py`, `_mosaic.py` (except the tests of the removed private lattice helper), `_zero_size.py`, `test_symbol_plot_vocabulary.py`, `test_symbol_style.py`, `test_integration.py` and `test_magnitude_scales.py`. Before the old generators are deleted, a golden test compares old and new `generate` output (polygons, order, adjacency, transforms) for the 15 presets and the four families; it is removed after the PR.
6. Behavior changes, either kept out of the first PR or listed in the changelog: flat-top hexagons for `pointy_top=False`; no holes for elongated triangles and quadrilaterals; correct (smaller) edge adjacency for curved isohedral tilings; the spline point count above 10 control points. If the first PR reproduces the old tile sets, only the adjacency of curved tilings changes.
7. Release: a minor release if the old tile sets are kept (names and signatures unchanged).

### 8.3 `isohedral-tiling-ui`

- Files that import `carto_flow` or `tactile` or use `tiling._ih`: `state.py`, `components/load_save.py`, `components/gallery.py`, `components/type_selector.py`, `components/preview_strip.py`, `components/prototile_editor.py`, `components/curve_editor.py`, `utils/symmetry.py`.
- Replace `tiling._ih.vertices`, `_ih.shapes`, `_ih.parameters` (`prototile_editor.py` 573, 911 to 955, 1032; `type_selector.py` 140; `state.py` 103 to 298) with `vertices`, `edge_outlines`, `parameters`; the preview and exports call `TileSet.polygons` instead of carto-flow's `generate`.
- Use the library's `info()` for the parameter table, `from_preset` and `to_dict` / `from_dict` for presets, load and save, with the `edge_curve_modes` fix.
- The UI's dependency on `carto-flow>=1.1.1` is then only needed for the Python snippet it generates; whether to keep it is the maintainer's choice.

### 8.4 Package metadata

- Repository `bright-fakl/isotile`, `src/` layout, hatchling (as carto-flow and the UI), `py.typed`, version `0.1.0`.
- `pyproject.toml`: `requires-python = ">=3.10,<4.0"` (as carto-flow); dependencies `numpy>=1.26` and `scipy>=1.11` (both untested below the versions in the front matter); extras `shapely` (`shapely>=2.0`, polygons and repair), `plot` (`matplotlib>=3.7`), `all`; dependency group `dev` with pytest, pytest-cov, ruff, mypy, `tactile` (equivalence tests only), shapely, matplotlib, mkdocs-material, mkdocstrings. License MIT for the code; `LICENSE` and `NOTICE` (Kaplan's BSD 3-Clause notice) in the sdist and wheel; `data/*.npz` and `data/LICENSE-tactile` included.
- CI (GitHub Actions, as carto-flow's `main.yml`): ruff, mypy, pytest with coverage on Python 3.10 to 3.13 on Linux and on 3.12 on macOS and Windows; one job installs tactile and runs the equivalence tests; one job runs `_build_data.py --check`, which regenerates the data file and fails on any difference.
- Docs: mkdocs-material and mkdocstrings on GitHub Pages, with a quickstart, a catalog of the 81 types (plots generated at build time), the adjacency algorithm with the benchmark, edge curves, migration notes from tactile and the API reference.
- Release: tag `v0.1.0`, PyPI trusted publishing as in carto-flow's `pypi-publish.yml` and `RELEASING.md`; recheck that the name is free before the first upload; 1.0 after carto-flow and the UI have shipped on it.

### 8.5 Phases and estimate

The earlier estimate was ten weeks. The prototype covers the core of phases 1 and 2 of that plan (data, vectorized geometry, fill, adjacency, equivalence and adjacency tests), and the four families are a few lines each. The estimates are working days for one developer and were not measured:

| Phase | Content | Days |
|---|---|---|
| 0 (done) | prototype of the core (imported into `bright-fakl/isotile`), mapping, curve test (this page) | |
| 1 | create the repository, move the prototype, packaging and CI, NOTICE, `info()`, `find_types`, public frame and named constructors, typing | 3 |
| 2 | edge-curve layer: `edges`, `curves`, prototile outline, validity and repair, presets, serialization, plotting; tests moved from carto-flow | 4 |
| 3 | carto-flow adoption: wrappers, `TilingResult` adapter, golden comparison, tactile removal, changelog | 5 |
| 4 | `isohedral-tiling-ui` adoption | 2 |
| 5 | docs, benchmark page, release `0.1.0` | 3 |
| | total | 17 |

## 9. What was not verified

- No carto-flow result (symbol cartograms, mosaic layouts) was produced with the new tilings; only tilings, polygons, adjacency and transforms were compared.
- Everything ran on Python 3.12 with numpy 2.3.3, scipy 1.16.2 and shapely 2.1.2 on one Linux machine. The stated minimum versions, Python 3.10, 3.11 and 3.13, macOS and Windows are untested.
- Parameters were drawn within 0.3 of the defaults (0.08 in the curve test). The adjacency table was not tested at extreme valid parameters (very thin tiles) or with parameters from the UI's slider ranges.
- `fill` was compared with tactile on axis-aligned rectangles only. Tactile's quadrilateral regions, and lattices aligned with the region (tactile divides by zero there; the prototype returns a result), were not tested; no such case occurred in the 486 regions.
- `HexagonTiling`, `TriangleTiling` and `QuadrilateralTiling` were compared with `tile_size` 0.12 to 0.25 and one region; the starting vertex and winding of polygons were not compared (section 3 item 6).
- Whether the holes in carto-flow's triangle and quadrilateral tilings (section 3 item 4) affect existing notebooks or tests was not checked, and `cover` was not tested for holes on the random shapes.
- The curve test used 3 trials per type and regime and random polylines. The `repair` and `extreme` figures say how often repair changes the neighbors, not how large the changes are. The cause of the 57 false edge contacts was identified by the tolerance experiment, not by tracing single pairs.
- Timings are single runs (library: best of 3) with other jobs on the machine.
- `_build_data.py --check`, `info()`, presets, serialization, plotting and the edge-curve layer are specified, not written.

## 10. Decisions

Decided on 2026-10-26 (unchanged): the name is `isotile` (no project of that name on PyPI; GitHub has unrelated repositories named `Isotile`, `isotiler` and `isotile-contracts`, none a tiling library; recheck before the first release), the repository is `bright-fakl/isotile` (separate), MIT code plus a `NOTICE` with Kaplan's BSD 3-Clause, adjacency as scipy sparse boolean matrices (carto-flow densifies at its boundary), the library never depends on carto-flow, and tiling type numbers, preset names and the parameter format stay. Square, hexagon, triangle and quadrilateral tilings are one implementation in the library with named constructors, and carto-flow keeps thin wrappers; section 3 shows that this reproduces all current cases.

Still open for the maintainer:

1. **Tile selection in the wrappers.** Reproduce each class's current boundary rule (same tile sets and order, section 3 item 1; recommended for the first adoption PR), or switch all classes to the library's `cover` (up to 29 percent fewer boundary tiles; changes the meaning of `n_tiles` and the cartogram outputs).
2. **Holes in `TriangleTiling` and `QuadrilateralTiling`** (section 3 item 4): fix them in the adoption PR as a separate commit, or keep the old tile sets until a later release. Fixing changes outputs for elongated shapes.
3. **`HexagonTiling(pointy_top=False)`**: produce flat-top tiles (the evident meaning of the flag; a behavior change) or keep pointy tiles and document that the flag only affects the symbol.
4. **Invalid prototile (self-intersecting curves).** Today carto-flow warns and repairs with `make_valid`, and the neighbors change in 77 percent of the trials (section 4). Options: keep this, raise `ValueError`, or warn and return the unrepaired outline with `prototile_is_valid = False`.
5. **Symmetry rule and serialization.** Adopt "keep a curve that is already symmetric, otherwise symmetrize by x", the UI's spline point count, and `edge_curve_modes` in `to_dict` (version 1.1). Files written by carto-flow change only by an added key.
6. **Dense or sparse adjacency in `TilingResult`**: dense in the first PR (100 MB per matrix at 10,000 tiles) and sparse later, or sparse at once (changes the type of two public fields).
7. **Public frame.** `IsohedralTiling(..., frame=...)` as public API (as in the prototype), or only through the named constructors.
8. **Parameter ranges.** The tactile data has none, and the library validates only that the prototile is a simple polygon. Whether to ship recommended ranges for editors (the UI needs them) and how to derive them.
9. **Creating the repository** `bright-fakl/isotile` and starting phase 1.

## 11. Review of 2026-10-27: names, what stays in carto-flow, recommendations

### Names for the lattice quantities

tactile calls the two translation vectors `t1` and `t2` and the tile coordinates `(t1, t2, aspect)`. A cell is the parallelogram spanned by the two translation vectors; it holds `n_aspects` tiles (the copies of the fundamental domain), so a tile is identified by its cell and its aspect. Proposed names:

| tactile / prototype | Library | Meaning |
|---|---|---|
| `t1`, `t2` (vectors) | `translation_u`, `translation_v` on the type and the tiling; `translations` as an (2, 2) array, row k is vector k | the two lattice translation vectors |
| `(t1, t2, aspect)` as an (n, 3) array `lattice` | `TileSet.cell` (n, 2) int, columns `u` and `v`, and `TileSet.aspect` (n,) int | the cell of a tile and its aspect within the cell |
| `d_t1`, `d_t2` in the adjacency table | `d_cell_u`, `d_cell_v`, `neighbor_aspect` | offset of the neighbor's cell |
| `fill`, `cover`, `tiles(lattice)` | `fill`, `cover`, `tiles(cell, aspect)` | unchanged except for the arguments |

`u` and `v` are used instead of `x` and `y` because the lattice is oblique. The wording "aspect" is the established term (Grünbaum and Shephard, Kaplan) and stays. The rename is done in phase 1, before the first release, with a note in the migration guide for tactile users.

### What stays in carto-flow, and what the GUI needs

The GUI (`isohedral-tiling-ui`) uses these carto-flow pieces today: `IsohedralTiling.generate(bounds, n_tiles, margin, compute_adjacency=False)` for every preview (`preview_strip.py` 311, 491, 526, 572), the polygons of its result, `_ih.vertices`, `_ih.shapes` and `_ih.parameters` (private tactile access), and the text of a Python snippet that calls carto-flow (`preview_strip.py` 431 to 446). It does not use `TilingResult.plot`, `plot_tile`, `canonical_symbol`, `tile_size_for_symbol_size`, `from_polygon`, `rotate` or `resolve_tiling`.

Consequences for the list in 8.1 "Stays in carto-flow":

- **Moves into the library (the GUI needs it):** generation from a tile count, a bounding box and a margin (`_resolve_generate_args`, `_apply_margin`, the rule `tile_size = sqrt(area / n_tiles)`, the scaling by the native area of the straight prototile). Proposed API: `IsohedralTiling.fill_region(bounds, *, n_tiles=None, tile_size=None, margin=0.0) -> TileSet`, with the frame computed inside. The unit-area normalization of the prototile (`canonical_tile` at unit area) and the inscribed radius of a tile are properties of the tiling and move with it (`prototile(normalized=True)`, `inscribed_radius`). `from_polygon` of the four families (the triangle and quadrilateral fit) and `rotate` are constructors and frame operations of the library.
- **Stays in carto-flow (not needed by the GUI):** the symbols (`canonical_symbol`, `tile_size_for_symbol_size`, `symbol_size_for_tile_size`, `IsohedralTileSymbol`), `TilingResult` (including `plot`, `plot_tile`, the PlotStyle use), `TileTransform` (center, rotation in degrees, flip as the symbol layouts use them), `TileAdjacencyType` replaced by the library's adjacency kinds, and the registry `resolve_tiling` (string names for the layouts).
- **The GUI stops depending on carto-flow for tiling:** previews call `fill_region` and `TileSet.polygons`; the Python snippet it generates is documentation text and needs no import. The dependency on `carto-flow` can be dropped or become optional.

### Recommendations for the open decisions (no workarounds)

The principle is that the library defines each concept once, exactly, and carto-flow and the GUI use it; behavior that exists only to reproduce a quirk of the old code is not carried over. The plan already allows breaking the old tiling classes (issue 159), and carto-flow 2.0 is the release that carries it.

1. **Tile selection: one rule, `cover`.** A tile belongs to the tiling of a region if it meets the region. The wrappers do not reproduce each class's centroid-based boundary filter. `n_tiles` keeps its meaning (the target count sets the tile size from the region's area), and the number of boundary tiles changes by up to 29 percent. Changelog entry.
2. **Holes in triangle and quadrilateral tilings: nothing separate to decide.** They come from the old per-class selection, and `cover` has none by construction.
3. **`pointy_top=False`: flat-top tiles.** The flag has one evident meaning. The library constructor takes the orientation as a rotation of the frame.
4. **Invalid prototile: the constructor raises `ValueError`, and a pure function `check_prototile(...)` reports the problem.** A self-intersecting prototile is not a tiling (tiles overlap), and repairing it with `make_valid` changes the neighbors in 77 percent of the trials, so no silent repair. An editor that must draw a state in progress calls the check function (it returns the offending edges) and does not construct a tiling. This is the same rule the prototype already applies to parameters (reject, keep the previous state).
5. **Symmetry: define it exactly, make enforcement the idempotent projection onto it, and parametrize by index, not by x.** S: the curve is invariant under the point reflection through (0.5, 0) with reversed order; U: under the mirror x -> 1 - x with reversed order. `enforce_symmetry` keeps the first half by position along the curve (a curve is not a function of x) and generates the second half, and applying it twice gives the same result. This is the UI's rule; "keep an already symmetric curve" then holds for all inputs and needs no special case. carto-flow's two symmetry tests are rewritten against the definition, with property tests (symmetry, idempotence, endpoints). `edge_curve_modes` is part of the serialized data (format version bump); the number of spline points is a rendering parameter (`max(100, 10 n)` by default), not data.
6. **Adjacency in `TilingResult`: sparse.** A dense matrix of 10,000 tiles is 100 MB and carries no information the sparse form lacks; densifying at the boundary only postpones the change. The two public fields change type (a breaking change, taken in 2.0); the layouts that use them (mosaic, grid) are adapted to scipy.sparse, which graph algorithms use natively.
7. **Frame: public.** It is the single mechanism for scale, rotation and position that the named constructors, `fill_region` and the GUI all need; hiding it forces carto-flow onto private API.
8. **Parameter ranges: the library provides an exact validity predicate and build-time safe intervals.** The valid parameter set of a type is the set where the prototile is a simple polygon; `check_prototile` is its exact test. For slider ranges, `_build_data.py` computes, per type and parameter, the maximal interval around the default that stays valid with the other parameters at their defaults, stores it in the data file and documents it as a one-parameter slice (not the full region). The editor combines both: slider limits from the slices, live validity from the predicate.
9. **Repository: done (`bright-fakl/isotile`).** Phase 1 starts with the renames above.
