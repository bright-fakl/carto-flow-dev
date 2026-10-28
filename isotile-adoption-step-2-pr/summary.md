---
pr: 193
title: "isotile adoption step 2: sparse tile adjacency in TilingResult"
description: TilingResult.adjacency and vertex_adjacency become boolean scipy csr_array taken from isotile, and the grid placement and the mosaic calibration read neighbor index lists instead of rows of a dense matrix. The assignments of 17 grid and mosaic layout cases on the states and the districts equal those of step 1 exactly; the two matrices of 10,301 hexagon tiles take 0.67 MB instead of 212 MB; the layouts are not slower.
kind: pr
topic: symbol
project: carto-flow
url: https://github.com/bright-fakl/carto-flow/pull/193
issue: 159
branch: isotile-adoption-step-2
base: main
related: proposal-isotile-adoption, isotile-adoption-step-1-pr
date: 2026-10-28 11:02
before: main at 4140204 (step 1, dense adjacency)
after: isotile-adoption-step-2 @ dee3dc7 (1,826 passed, 2 skipped, 4 xfailed locally)
inputs: carto-flow 4140204 against dee3dc7, same isotile pin (392484c); Python 3.10.18, numpy 2.2.6, scipy 1.15.3, bundled census data (49 states, 432 districts); 16-core WSL2 machine. Old and new ran one after the other with nothing else running, each case best of 3 (memory: one run per process). Mosaic runs use morph=False.
---

Step 2 of [proposal-isotile-adoption](../proposal-isotile-adoption/index.html) (sections 4.1, 7 and 8.2). The change does not alter results, so the page has no before and after figures; the evidence is the exact comparison of the assignments, the memory and the wall times.

## What changed

- `TilingResult.adjacency` and `vertex_adjacency` are `scipy.sparse.csr_array` of dtype bool, symmetric, with sorted column indices (`generate` calls `sort_indices`). They are `TileSet.adjacency(adjacency_type)` and `TileSet.adjacency("vertex-only")` without a conversion. `compute_adjacency=False` gives `csr_array((n, n), dtype=bool)`. `rotate` passes the matrices on.
- Serialization: `SymbolCartogram.save` never wrote the adjacency, and `load` created a dense all-`False` matrix. `load` now creates an empty `csr_array`; `vertex_adjacency` stays `None`. The format does not change, so files written by step 1 and by earlier versions load (the golden file `saved_cartogram.json` is one of them). No format bump is needed.
- `layouts/mosaic/_calibration.py`: `adj_list` is built from `indptr` and `indices` (`indices.tolist()` sliced per row). The elements are Python `int`; they were `numpy.int64`. `_assignment.py` and `mosaic/__init__.py` use them in `nb in valid_set`, `tile_to_local[nb]`, set comprehensions and `for nb in adj_list[t]`; ints and numpy integers hash and compare equal, so nothing there changes.
- `layouts/grid/_placement.py`: `_canonical` copies a matrix (accepts a sparse or a dense matrix, drops stored zeros, sorts the indices) and `_lists` turns it into one list of neighbor indices per row. Each helper builds the lists once per call: `fill_internal_holes` (flood fill, hole components, shift-chain BFS, mean neighbor distance, neighbor counts from `np.diff(indptr)`), `_fix_island_assignments`, `_bfs_distance_matrix`, `bfs_expand_assignments` and `assign_to_grid_hungarian` (column lists of the CSC form for the penalty masks, row lists for the reverse penalty). Two element-wise lookups in `_fix_island_assignments`, `tile_adjacency[it, mt]` over all pairs of island tiles and main-cluster tiles, became membership tests of neighbor lists in the main cluster (same truth value; a pair scan over a sparse matrix would be slow). `GridBasedLayout` (`layouts/grid/__init__.py`) only passes the fields on and needed no change. The region adjacency (`LayoutData.adjacency`, `compute_adjacency` of `symbol_cartogram.adjacency`) is a different matrix; it stays dense and `compute_adjacency` keeps its semantics.
- Other consumers searched with `grep` over `src`, `tests`, `docs`, `benchmarks`: no other use of the tile matrices in the flow, centroid and packing layouts or in plotting. The notebook `docs/how-to/choose-grid-or-mosaic-layout.ipynb` read the matrix with `np.flatnonzero(adjacency[i])` and `np.ix_`; both now use the index slice and `adjacency[a][:, b].nnz`.
- Docs: `docs/explanations/tiling-system.md` (field types, row slice, empty matrices, loaded results), docstrings of `TilingResult`, `generate` and the placement helpers, and a `CHANGELOG.md` entry under the 3.0.0 breaking changes that lists the operations that stop working (`adjacency.any()`, `len`, `numpy.where(adjacency[t])`, `numpy.array_equal`, a column as boolean mask).

## Tests

| | Count |
|---|---|
| Full suite | 1,826 passed, 2 skipped, 4 xfailed (1,806 passed before) |
| migrated to sparse | `TestFillInternalHoles` (both tests build a sparse matrix from a neighbor dict), `test_tilings.py` (neighbor counts from `indptr`, symmetry, `vertex_adjacency` equality, empty placeholders, direct `TilingResult` construction), `test_symbol_cartogram_mosaic.py` (enclosed cells, placeholder, `adj_list` against the matrix, which also asserts that the elements are Python ints), golden tests (the fields are no longer converted) |
| new | `TestSparseAdjacency` (type, dtype, shape, sorted indices and symmetry for square, hexagon, triangle, parallelogram and `scalloped_hexagon`; neighbors as row slice; empty matrices; `rotate`; storage proportional to the tile count), `TestSparsePlacementHelpers` (BFS distances and BFS expansion on a path graph with unsorted indices and stored zeros) |

`ruff check`, `ruff format`, `mypy` and `deptry src` pass.

## Identity of the layouts

[identity_check.py](identity_check.py) runs 17 cases with the sources of step 1 (an archive of the tree at 4140204 on `PYTHONPATH`) and with this branch, stores for every case the tile index of every item (`assignments`), the region of every item (`source_indices`) and the lattice size, and compares them with `np.array_equal` (no tolerance). Cases: the 9 grid and mosaic cases of the states of step 1 (hexagon, square, triangle, quadrilateral and `scalloped_hexagon` grid; hexagon, square, triangle and `scalloped_hexagon` mosaic), the states grid with a tile count column (hexagon, square: the `bfs_expand_assignments` path), the districts grid (hexagon, square) and the districts mosaic grouped by state (hexagon, square, triangle, `scalloped_hexagon`). The grid cases run with the defaults, so `fill_holes`, `fix_islands`, `neighbor_weight` and `topology_weight` are all active. [identity_and_timing.txt](identity_and_timing.txt): all 17 are identical, including the lattice sizes. An earlier single run of all cases gave the same result. [run_measurements.sh](run_measurements.sh) is the timed run.

## Memory at 10,000 tiles

[memory_check.py](memory_check.py), one process per version and tiling, [memory_output.txt](memory_output.txt). `generate` with adjacency, region (0, 0, 100, 100), about 10,000 tiles:

| tiling | tiles | `adjacency` + `vertex_adjacency` dense | sparse | `tracemalloc` peak of `generate` dense / sparse | peak RSS growth of `generate` dense / sparse |
|---|---|---|---|---|---|
| hexagon | 10,301 | 212.2 MB | 0.67 MB | 216.8 / 91.1 MB | 98.4 / 96.2 MB |
| square | 10,000 | 200.0 MB | 0.87 MB | 204.8 / 57.9 MB | 96.6 / 63.4 MB |

The memory held by the result drops by a factor of 230 to 320. The peak RSS growth of the hexagon run is the same for both versions; it is set by other allocations of `generate` (the polygons and isotile's intermediate arrays) and the cause of the equal value was not investigated further. The `tracemalloc` peak counts every allocation and shows the matrices.

## Wall time

Best of 3, old and new one after the other with nothing else running ([timing_old.txt](timing_old.txt), [timing_new.txt](timing_new.txt), table from [identity_and_timing.txt](identity_and_timing.txt)). All old runs came first and all new runs second, so a slow drift of the machine does not cancel; single runs of the same cases earlier in the session, with the test suite running, differed by up to 20 percent in both directions.

| case | items | lattice tiles | identical | old (s) | new (s) | new / old |
|---|---|---|---|---|---|---|
| states grid hexagon | 49 | 149 | yes | 1.64 | 1.59 | 0.97 |
| states grid square | 49 | 160 | yes | 1.74 | 1.67 | 0.96 |
| states grid triangle | 49 | 168 | yes | 1.84 | 1.73 | 0.94 |
| states grid quadrilateral | 49 | 180 | yes | 0.79 | 0.73 | 0.92 |
| states grid scalloped_hexagon | 49 | 179 | yes | 1.97 | 1.86 | 0.95 |
| states grid hexagon, tile count | 154 | 427 | yes | 4.52 | 4.14 | 0.91 |
| states grid square, tile count | 154 | 468 | yes | 4.93 | 4.46 | 0.90 |
| states mosaic hexagon | 154 | 447 | yes | 1.86 | 1.82 | 0.98 |
| states mosaic square | 154 | 520 | yes | 0.93 | 0.91 | 0.98 |
| states mosaic triangle | 154 | 490 | yes | 0.96 | 0.94 | 0.98 |
| states mosaic scalloped_hexagon | 154 | 533 | yes | 1.45 | 1.38 | 0.96 |
| districts grid hexagon | 432 | 1159 | yes | 116.44 | 109.38 | 0.94 |
| districts grid square | 432 | 1320 | yes | 128.31 | 124.36 | 0.97 |
| districts mosaic hexagon | 432 | 1163 | yes | 6.64 | 6.56 | 0.99 |
| districts mosaic square | 432 | 1260 | yes | 5.20 | 5.11 | 0.98 |
| districts mosaic triangle | 432 | 1316 | yes | 3.17 | 3.20 | 1.01 |
| districts mosaic scalloped_hexagon | 432 | 1283 | yes | 4.98 | 4.90 | 0.98 |

No case is slower by more than 1 percent and most are 2 to 10 percent faster (the neighbor loops read Python lists instead of calling `np.where` on a row per node; not profiled per function). The districts grid takes about two minutes in both versions; the time is in the orientation cost of `assign_to_grid_hungarian` (a Python loop of n x n x m), not in the adjacency.

## Deviations from the page

- Serialization needed no decision: the adjacency was never in the file.
- The page expected about 60 changed lines in 3 files; the change in `src` is larger (about 100 lines in 4 files plus the notebook) because the placement helpers build neighbor lists once per call (`_canonical`, `_lists`) and accept stored zeros and unsorted indices.
- The identity check has 17 cases: it adds the states grid with a tile count column and omits the districts grid with triangles (two minutes per run).
- The Python in this environment is 3.10 (step 1 used 3.12); both versions of every comparison ran on it.

## Open questions

1. `compute_adjacency` keeps its signature; with sparse matrices the argument saves little (the lattice lookup costs milliseconds at 10,000 tiles). Deprecate it in 3.0.0, or keep it for the calibration trials only?
2. The placement helpers accept a dense matrix because `csr_array(dense)` converts it; the public type is sparse. Mention it on the migration page (step 4), or make the helpers reject dense input?
