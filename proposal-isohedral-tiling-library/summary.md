---
issue: 159
title: Design of the standalone isohedral tiling library (replacing tactile)
description: Scope, package layout, data model, API, lattice adjacency and phasing for the new tiling library. A spike on all 81 types shows that edge and vertex adjacency is a per-type table of (lattice offset, aspect) that does not change with the parameters (offsets of at most 2 lattice steps), and that a table lookup takes 0.02 s for 15,000 tiles against 5.7 s for the geometric method on 5,000 tiles.
kind: proposal
topic: symbol
status: open
related:
date: 2026-10-26 22:00
inputs: tactile 0.1.0 (BSD 3-Clause, Craig S. Kaplan), the 81 types of tactile's tiling_types, straight-edge prototiles, 9x9 to 71x71 lattice patches, parameters perturbed by up to ±0.15 (4 draws per type). Single runs.
---

This page works out the design of issue 159 up to the point where implementation can start. It lists the decisions that are still open at the end (section 9).

## 1. Findings that shape the design

`spike.py` generates a patch of the lattice for each of the 81 types, finds the geometric neighbors of the tile (0, 0, aspect) by counting shared vertices (2 or more: edge, exactly 1: vertex only), and compares the result at the default parameters with four perturbed parameter sets. `spike2.py` collects statistics and timings.

| Finding | Result |
|---|---|
| Types | 81 |
| Tables that change with the parameters | 0 of 81 (default and 4 perturbed draws, ±0.15) |
| Edge neighbors per tile | equal to the number of prototile vertices, for every type and aspect (3 to 6) |
| Largest lattice offset of any neighbor | 2 (edge and vertex neighbors together) |
| Vertex-only neighbors per tile | 0 to 18 (0 for 35 type-aspect pairs, 18 for 18) |
| Aspects per type | 1 (17 types), 2 (27), 3 (6), 4 (20), 6 (8), 8 (2), 12 (1) |
| Free parameters per type | 0 (26 types), 1 (15), 2 (21), 3 (9), 4 (7), 5 (2), 6 (1) |
| Lattice table, 15,123 tiles | 0.02 s |
| Current geometric method, 5,043 tiles | 5.7 s |

Consequences:

- Adjacency of a tiling can be computed from `(t1, t2, aspect)` alone, with a small table per type that is part of the type data. It is independent of the parameters and of the scale, and it can be precomputed once per type and shipped with the data.
- The table is computed with straight edges. Custom edge curves change the shape of the tile boundary but not which tiles touch (all tiles share the same curve on a shared edge), so the table applies unchanged. Whether the tile overlap repair of carto-flow changes the neighbors (open question of the issue) is not yet checked; it needs one test per type with a set of random curves, in phase 3.
- A table lookup over `n` tiles is `O(n * (neighbors per aspect))` with an integer hash of `(t1, t2, aspect)`, so tiles must carry their lattice coordinates through the generation. The current carto-flow tiling drops them (`TileTransform` has center, rotation and flip only), which is why adjacency is currently found geometrically.

## 2. Scope

In the library:

1. The 81 types with their parameters, vertices, edges, edge shapes (I, J, U, S), aspects, translation vectors and the tile-coloring tables.
2. Tile generation in a rectangle or a convex quadrilateral, returning arrays.
3. Adjacency from the lattice (edge, vertex-or-edge, vertex-only, neighbors of a tile); a geometric method for arbitrary polygon sets.
4. Edge curves: storage, symmetry enforcement (U, S, I), interpolation, prototile polygon construction, validity repair.
5. `to_dict` / `from_dict` with the existing parameter format and preset names.
6. Plotting of tiles and the prototile (matplotlib), as an optional extra.

Stays in carto-flow: symbols, sizing of symbols per tile (`tile_size_for_symbol_size`), the layouts, the presets that map to symbol use, and `TilingResult` as an adapter around the library output.

Not in the library: anything that imports `carto_flow`, a GUI (it stays in `isohedral-tiling-ui`), non-isohedral tilings (square, hexagon and the triangle and quadrilateral families stay as carto-flow convenience classes that can be expressed with isohedral types later).

## 3. Package and distribution

- Name: to be decided (section 9). Working name `isotile` (the import name and the PyPI name must both be free; checked at decision time).
- Repository: new, `src/` layout, MIT license for the new code, `NOTICE` file with the BSD 3-Clause notice of Craig S. Kaplan (the type data is derived from Tactile, tactile-js, and the BSD license requires that the copyright notice and the disclaimer stay with the data and any code derived from it).
- Dependencies: `numpy` (core); `shapely` (geometric adjacency, polygon construction); `scipy` (spline interpolation of edge curves); `matplotlib` as an optional extra.
- Python: same range as carto-flow.
- Versioning: independent; carto-flow pins `>=` the first release.

## 4. Package layout

```
isotile/
  __init__.py        public API
  types.py           TilingType (frozen dataclass), registry, lookup by number
  data/              types.npz  (coefficients), adjacency.npz (lattice tables), LICENSE-tactile
  _build_data.py     regenerates data/ from tactile and from the lattice spike (dev only)
  tiling.py          IsohedralTiling
  lattice.py         tile generation, TileSet
  adjacency.py       lattice and geometric adjacency
  edges.py           EdgeShape, EdgeCurve, symmetry enforcement, interpolation
  prototile.py       prototile polygon from vertices and curves, validity repair
  presets.py         named tilings (parameter format unchanged)
  plot.py            matplotlib helpers (optional)
```

## 5. Data model

```python
class EdgeShape(enum.Enum):  I = "I"; J = "J"; U = "U"; S = "S"   # values equal tactile's names

@dataclass(frozen=True)
class TilingType:
    number: int                    # 1..93 (81 valid)
    n_params: int
    n_vertices: int
    n_aspects: int
    edge_shapes: tuple[EdgeShape, ...]      # per distinct edge shape
    edge_shape_ids: np.ndarray     # (n_vertices,) int
    edge_orientations: np.ndarray  # (n_vertices, 2) int
    default_params: np.ndarray     # (n_params,)
    vertex_coeffs: np.ndarray      # (n_vertices, 2, n_params + 1)
    aspect_coeffs: np.ndarray      # (n_aspects, 2, 3, n_params + 1)
    translation_coeffs: np.ndarray # (2, 2, n_params + 1)
    coloring: np.ndarray
    adjacency: AdjacencyTable      # edge, vertex-only; offsets (da, db, aspect')
```

Vertices, aspect matrices and translation vectors are `coeffs @ [*params, 1]` (one `einsum` each), so a parameter change is three small matrix products. `IsohedralTiling` holds the type, the parameter array and the derived arrays (`vertices` (n, 2), `aspects` (a, 2, 3), `t1`, `t2`, `edge_transforms` (n, 2, 3)); setting `parameters` validates the length and recomputes. Parameters are accepted as any array-like and stored as `float64`.

The coefficient tables are copied from tactile's `tiling_data.py` into `types.npz` by a build script that is part of the repository, so the provenance is reproducible and the BSD notice sits next to the file.

## 6. API sketch

```python
tiling = IsohedralTiling(7)                    # defaults
tiling = IsohedralTiling(7, parameters=[0.3, 0.5])
tiling.type, tiling.parameters, tiling.vertices, tiling.aspects, tiling.t1, tiling.t2

tiles = tiling.fill(bounds=(x0, y0, x1, y1))   # TileSet
tiles.lattice        # (n, 3) int: t1, t2, aspect
tiles.transforms     # (n, 2, 3) affine matrices
tiles.polygons()     # list of shapely Polygons (uses curves if set)
tiles.centroids      # (n, 2)

adj = tiles.adjacency("edge")                  # scipy.sparse CSR (n, n), bool
adj = tiles.adjacency("vertex")                # edge or vertex
adj = tiles.adjacency("vertex-only")
tiles.neighbors(i, "edge")                     # indices
tiles.adjacency("edge", method="geometric")    # needed only for foreign polygon sets

tiling.set_edge_curve(shape_id, points, ...)   # enforces I/J/U/S symmetry
tiling.to_dict(); IsohedralTiling.from_dict(d)
```

Choices:

- Adjacency returns a sparse boolean matrix by default (dense `(n, n)` arrays do not scale to the 10,000-tile layouts); `.toarray()` gives the dense form that carto-flow uses now.
- `fill` takes an explicit lattice range or bounds; unlike tactile's scanline generator it returns deduplicated arrays, so the 8-line deduplication loop and the center perturbation hack in `IsohedralTiling.generate` go away.
- Tile identity is the lattice triple. Tiles at the edge of the bounds keep their triple, so adjacency across the boundary is silently dropped, not guessed.

## 7. Lattice adjacency algorithm

1. Build a key per tile: `(t1 - t1_min) * W + (t2 - t2_min)` and multiply by `n_aspects`, plus the aspect.
2. For each aspect `a` and each table row `(da, db, a')`, take the tiles of aspect `a`, compute the key of `(t1 + da, t2 + db, a')` and look it up with `np.searchsorted` on the sorted key array (or a dense lookup grid, when the patch is compact).
3. Emit `(i, j)` pairs for found keys, build the CSR matrix, symmetrize.

The table of a type is computed once by `_build_data.py` with the same procedure as `spike.py` (shared-vertex counts on a 9x9 patch), stored as integer arrays, and a test regenerates it for every type and compares it with a fresh geometric computation at randomized parameters. Types with parameter values where the topology degenerates (a vertex coincides with another) are rejected by `parameters` validation (the valid ranges are not part of tactile's data; the validation checks for non-zero edge lengths and a simple prototile polygon).

## 8. Migration and phasing

The earlier draft estimated ten weeks. The work is smaller because the adjacency design is now proven and the data exists; the larger part is carto-flow and UI integration.

| Phase | Content | Result |
|---|---|---|
| 1 | Repo, data build script, `TilingType`, vertices/aspects/transforms vectorized, equivalence tests against tactile for all 81 types (vertices, edges, aspects, fill) | library reproduces tactile |
| 2 | `fill`, `TileSet`, lattice adjacency, geometric adjacency, adjacency equivalence tests (lattice against geometric on every type and random parameters) | adjacency table verified |
| 3 | Edge curves: symmetry enforcement, interpolation, prototile construction, validity repair (moved from carto-flow with their tests); serialization and presets | feature parity with `symbol_cartogram/tiling.py` for `IsohedralTiling` |
| 4 | carto-flow adopts the library: `IsohedralTiling` and layouts use `TileSet.adjacency`; `tactile` dependency removed; all symbol cartogram tests pass; timings of the mosaic and grid layouts | PR in carto-flow |
| 5 | `isohedral-tiling-ui` adopts the library; symmetry enforcement and spline code removed from the UI | PR in the UI repo |
| 6 | Docs, benchmark page, first PyPI release | release |

carto-flow's public `IsohedralTiling`, `TilingResult`, presets, `plot_tile` and `plot_prototile` are public API. If their shape changes, the release that ships it is a major version; the plan keeps the names and moves the implementation, so phase 4 can be a minor release if `TilingResult` and the class names stay.

## 9. Decisions

Decided on 2026-10-26: the name is `isotile` (no project of that name on PyPI; GitHub has unrelated repositories named `Isotile`, `isotiler` and `isotile-contracts`, none a tiling library; recheck before the first release), the repository is `bright-fakl/isotile` (separate), the license combination is MIT code plus a `NOTICE` with Kaplan's BSD 3-Clause.

### Square, hexagon, triangle and quadrilateral tilings

These are isohedral tilings (every tiling by one of the four is a member of the 81 types; checked in tactile's data: types 41 to 76 include regular quadrilaterals with 0 to 4 parameters, types 1 to 20 regular hexagons, types 83 to 93 regular triangles; the 3-gon and 4-gon types number 16 and 37). The carto-flow classes were written for speed and for symbol-specific behavior. Speed is no longer a reason once adjacency comes from the lattice table. What remains is carto-flow-specific: `canonical_symbol`, `tile_size_for_symbol_size`, `from_polygon` and the pointy/flat orientation.

Proposal: one implementation in the library, and the four families become named constructors of `IsohedralTiling` (`IsohedralTiling.square()`, `.hexagon(pointy_top=True)`, `.triangle(...)`, `.quadrilateral(...)`) that choose a type and parameters, and carto-flow keeps its four classes as thin subclasses or wrappers adding the symbol behavior. Before the hand-written generators are removed, phase 4 tests that the library output matches them (tile polygons, centers, adjacency) for the presets in use, and checks that every shape the classes accept (any triangle, any simple quadrilateral) maps to a type with enough parameters; the mapping from `from_polygon` input to type and parameters is the part to verify, not assume.

### Still open

1. **Dense or sparse** adjacency in `TilingResult` (sparse in the library; carto-flow can densify at the boundary).
2. **Creating the repository** `bright-fakl/isotile` and starting phase 1.
