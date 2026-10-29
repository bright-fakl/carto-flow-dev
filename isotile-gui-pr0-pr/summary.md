---
pr: 10
title: "isotile: editor API additions (G-1 to G-6)"
description: with_parameters, InvalidPrototileError with the report, repr as the constructor call, TileSet.to_geojson, no re-validation in with_frame (fill_region of curved presets 3.4 times faster, bit-identical), and the margin default fixed in docs/curves.md. PR 0 of the isotile GUI port. Nothing to compare visually; the page gives the written evidence.
kind: pr
topic: symbol
project: isotile
url: https://github.com/bright-fakl/isotile/pull/10
branch: gui-pr0-additions
base: main
related: proposal-isotile-gui, isotile-offset-pr
date: 2026-10-28 16:00
before: bright-fakl/isotile main at a4625b7
after: gui-pr0-additions (5086 passed, 206 skipped locally)
inputs: Python 3.12, numpy, shapely (tests); best of 15 runs for the timing
---

PR 0 of the GUI port ([proposal-isotile-gui](../proposal-isotile-gui/index.html), section 4): items G-1 to G-6; G-7 is not included.

## Changes

| Item | API | Behavior |
|---|---|---|
| G-1 | `docs/curves.md` | the default `margin` of `fill_region` is 0.0 (the page said 0.1) |
| G-2 | `IsohedralTiling.with_parameters(parameters)` | a new tiling with the same type, curves, modes and frame; the checks of the `parameters` setter; `self` unchanged |
| G-3 | `with_frame`, `rotated`, `scaled`, `fill_region` | the validated curves are copied and `check_prototile` and `check_curves` do not run again |
| G-4 | `repr(tiling)` | `IsohedralTiling(41, parameters=[...], edge_curves={...}, edge_curve_modes={...}, frame=[[...]])`; the last three only when set; `eval` rebuilds an equal tiling |
| G-5 | `InvalidPrototileError(ValueError)`, attribute `report` | raised by the constructor, `with_parameters`, `with_edge_curves` and the setter when the prototile or its outline is invalid; malformed arguments stay plain `ValueError`; messages unchanged |
| G-6 | `TileSet.to_geojson(properties=None, *, curved=True, n_points=None)` | `FeatureCollection` dict, one `Polygon` per tile with `cell`, `aspect`, `color` and the entries of `properties`; closed counterclockwise rings; no shapely |
| G-6 | `TileSet.save_geojson(path, properties=None, *, curved=True, n_points=None)` | writes `to_geojson` as a UTF-8 JSON file; `str` or `Path`; no collection metadata |

## G-3: same results, less time

`fill_region((-2, -2, 2, 2), n_tiles=100, margin=0.1, outline="straight")`, nine presets with edge curves, best of 15 per preset, median over the presets:

| | ms |
|---|---|
| before (a4625b7) | 7.0 |
| after | 2.1 |

Bit-identity: for all 15 presets, rotated by 17 degrees and scaled by 1.3, `fill_region(..., offset=(0.3, 0.2))` with `outline="straight"` and the default gave the same cells, aspects, transforms, vertices, prototile outline, edge transforms, aspects and translations before and after (30 of 30 `numpy.array_equal`). The tests compare `with_frame` with the constructor for all 81 types and all presets, compare the tiling of `fill_region` with the constructor path, and assert that no check runs in `with_frame`, `rotated`, `scaled` and `fill_region`.

## Tests

`tests/test_editor_api.py`: `with_parameters` returns a new tiling, equals the constructor and rejects what the setter rejects, including a curved outline that is invalid at valid straight parameters; `InvalidPrototileError` carries the report of `check_prototile` from every entry point and is a `ValueError`; `repr` round-trips for all types and presets, also with a frame; `to_geojson` parses with `json`, matches `outlines()`, orients reflected tiles counterclockwise, takes extra properties, handles zero tiles, and `save_geojson` read back with `json.load` equals `to_geojson`.

ruff, mypy, the full suite and `scripts/make_doc_figures.py --check` pass.
