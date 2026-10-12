---
pr: 130
url: https://github.com/bright-fakl/carto-flow/pull/130
issue: 116
title: create_flow_cartogram as the single entry point; GridSpec and LadderSpec in MorphOptions.grid
description: One entry point, create_flow_cartogram, replaces morph_gdf and multiresolution_morph (both deprecated). MorphOptions.grid takes an int or tuple, GridSpec(size, margin, square), LadderSpec(min_resolution, levels, margin, square), "auto" or a prebuilt Grid, and replaces grid_size (deprecated alias); a ladder runs from coarse to fine and ends at the first converged level, in create_flow_cartogram and CartogramWorkflow.morph. Voronoi premorph and the mosaic layout accept a ladder through their MorphOptions. Results of existing calls do not change.
kind: pr
topic: flow
branch: feat/create-flow-cartogram
base: main
date: 2026-10-12 08:30
related: pr128-multires-auto-resolution, exploration-multires-start
before: main @ c080423
after: feat/create-flow-cartogram @ 7afb2e0
inputs: states (49) and districts (432), bundled; MorphOptions defaults; NUMBA_NUM_THREADS=8. Errors are the reported errors of the final cartogram. The difference column is the largest absolute difference of any geometry bound between the two calls.
---

`make_tables.py` regenerates `data/tables.md`. There are no figures: the change is an API change and the table shows that the new calls return the results of the deprecated ones.

| input | call | result | largest bounds difference to the deprecated call |
|---|---|---|---|
| states | `morph_gdf` (deprecated) | converged, 112 it, grid 256, mean 0.204 / max 0.79 % | |
| states | `create_flow_cartogram` | converged, 112 it, grid 256, mean 0.204 / max 0.79 % | 0 |
| states | `multiresolution_morph(min_resolution=128, levels=4)` (deprecated) | converged, 63 it, grid 128, mean 1.607 / max 9.18 % | |
| states | `create_flow_cartogram` with `LadderSpec(128, 4)` | converged, 63 it, grid 128, mean 1.607 / max 9.18 % | 0 |
| states | `create_flow_cartogram` with `grid="auto"` | converged, 63 it, grid 128, mean 1.607 / max 9.18 % | |
| districts | `morph_gdf` (deprecated) | converged, 145 it, grid 256, mean 1.417 / max 9.76 % | |
| districts | `create_flow_cartogram` | converged, 145 it, grid 256, mean 1.417 / max 9.76 % | 0 |
| districts | `multiresolution_morph(min_resolution=128, levels=4)` (deprecated) | converged, 123 it, grid 128, mean 0.769 / max 9.05 % | |
| districts | `create_flow_cartogram` with `LadderSpec(128, 4)` | converged, 123 it, grid 128, mean 0.769 / max 9.05 % | 0 |
| districts | `create_flow_cartogram` with `grid="auto"` | converged, 123 it, grid 128, mean 0.769 / max 9.05 % | |
