---
pr: 128
url: https://github.com/bright-fakl/carto-flow/pull/128
issue: 93
title: Resolution warnings and automatic ladder for the multiresolution morph
description: morph_gdf, multiresolution_morph and the workflow morph methods warn when the grid cannot resolve the smallest target region (fewer than 2.5 cells) or when more than 1 % of the regions are below one cell at the finest grid; the multiresolution methods accept min_resolution="auto" and levels="auto". States and districts choose 128 and converge at the first level without a warning; counties choose 512, run to 2048 and get the warning. Defaults are unchanged.
kind: pr
topic: flow
branch: feat/multires-auto
base: main
date: 2026-10-12 04:10
related: exploration-multires-start, exploration-counties-subcell
before: main @ b5a37be (no check, integer resolutions only)
after: feat/multires-auto @ 08e8486
inputs: states (49) and districts (432) bundled, 3,108 counties (prepared set, ESRI:102008, total_votes, area_scale 1e-6, not bundled); MorphOptions defaults; NUMBA_NUM_THREADS=8. Error columns are the reported errors of the final cartogram.
---

`make_tables.py` regenerates `data/tables.md` (every table below). Counties are read from `COUNTIES_PARQUET` when set. There are no figures: the change adds warnings and an opt-in value; defaults and results of existing calls are unchanged.

The rule: with $r(N)$ the smallest target region in cells at grid $N$, `"auto"` picks the smallest power of two from 64 to 512 with $r(N) \ge 2.5$ (512 if none), and doubles up to 2048; the morph ends at the first converged level. The warning fires (for a ladder at its coarsest and finest grid, for a single-resolution morph at the grid in use, once per call) when $r < 2.5$ at the coarsest grid or when more than 1 % of the regions are below one cell at the finest grid. The measurements behind the thresholds are on `exploration-multires-start`.

## Smallest target region in cells and the automatic ladder

| input | regions | 64 | 128 | 256 | 512 | auto min_resolution | auto levels |
|---|---|---|---|---|---|---|---|
| states | 49 | 0.747 | 3.02 | 12 | 48.2 | 128 | 5 |
| districts | 432 | 0.676 | 2.74 | 10.9 | 43.6 | 128 | 5 |
| counties | 3108 | 0.000175 | 0.000707 | 0.00281 | 0.0113 | 512 | 3 |

## Warnings

| input | min_resolution, levels | warning |
|---|---|---|
| states | 64, 1 | Grid resolution: the smallest target region covers 0.75 cells at the coarsest grid (64); at least 2.5 cells are needed to resolve it (min_resolution=128); 4 of 49 target regions (8 %) are smaller than one cell at the finest grid (64); they cannot be resolved and the morph is unlikely to converge. |
| states | 96, 4 | Grid resolution: the smallest target region covers 1.7 cells at the coarsest grid (96); at least 2.5 cells are needed to resolve it (min_resolution=128). |
| states | 128, 5 | none |
| states | 512, 3 | none |
| districts | 64, 1 | Grid resolution: the smallest target region covers 0.68 cells at the coarsest grid (64); at least 2.5 cells are needed to resolve it (min_resolution=128); 328 of 432 target regions (76 %) are smaller than one cell at the finest grid (64); they cannot be resolved and the morph is unlikely to converge. |
| districts | 96, 4 | Grid resolution: the smallest target region covers 1.5 cells at the coarsest grid (96); at least 2.5 cells are needed to resolve it (min_resolution=128). |
| districts | 128, 5 | none |
| districts | 512, 3 | none |
| counties | 64, 1 | Grid resolution: the smallest target region covers 0.00017 cells at the coarsest grid (64); at least 2.5 cells are needed to resolve it (no grid up to 2048 does); 3027 of 3108 target regions (97 %) are smaller than one cell at the finest grid (64); they cannot be resolved and the morph is unlikely to converge. |
| counties | 96, 4 | Grid resolution: the smallest target region covers 0.0004 cells at the coarsest grid (96); at least 2.5 cells are needed to resolve it (no grid up to 2048 does); 338 of 3108 target regions (11 %) are smaller than one cell at the finest grid (768); they cannot be resolved and the morph is unlikely to converge. |
| counties | 128, 5 | Grid resolution: the smallest target region covers 0.00071 cells at the coarsest grid (128); at least 2.5 cells are needed to resolve it (no grid up to 2048 does). |
| counties | 512, 3 | Grid resolution: the smallest target region covers 0.011 cells at the coarsest grid (512); at least 2.5 cells are needed to resolve it (no grid up to 2048 does). |

## Single-resolution morph (morph_gdf), warning for the grid in use

| input | grid_size | warning |
|---|---|---|
| states | 256 | none |
| states | 512 | none |
| districts | 256 | none |
| districts | 512 | none |
| counties | 256 | Grid resolution: the smallest target region covers 0.0028 cells at the grid (256); at least 2.5 cells are needed to resolve it (no grid up to 2048 does); 2096 of 3108 target regions (67 %) are smaller than one cell at the grid (256); they cannot be resolved and the morph is unlikely to converge. |
| counties | 512 | Grid resolution: the smallest target region covers 0.011 cells at the grid (512); at least 2.5 cells are needed to resolve it (no grid up to 2048 does); 856 of 3108 target regions (28 %) are smaller than one cell at the grid (512); they cannot be resolved and the morph is unlikely to converge. |

## Automatic ladder, default options

| input | levels run (grid, status, iterations) | mean / max error % (reported) | warning |
|---|---|---|---|
| states | 128, converged, 63 | 1.61 / 9.2 | none |
| districts | 128, converged, 123 | 0.77 / 9.1 | none |
| counties | 2048, stalled, 60 | 2.56 / 371.2 | Grid resolution: the smallest target region covers 0.011 cells at the coarsest grid (512); at least 2.5 cells are needed to resolve it (no grid up to 2048 does). |
