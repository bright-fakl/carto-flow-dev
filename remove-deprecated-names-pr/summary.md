---
pr: 200
title: "Remove the deprecated names (#122)"
description: morph_gdf, multiresolution_morph, Cartogram.latest, CartogramWorkflow.latest and History.latest() are removed in the 3.0.0 line; the deprecation notes that named a placeholder version go with them.
kind: pr
topic: flow
project: carto-flow
url: https://github.com/bright-fakl/carto-flow/pull/200
branch: remove-deprecated-latest
base: main
related: isotile-adoption-pypi-pin-pr
date: 2026-10-30 00:10
before: main at 4699a3b with five deprecated names and `.. deprecated:: 2.1` notes
after: remove-deprecated-latest (CI results on the PR)
inputs: Python 3.13.7, uv 0.8.17; the tests of history, grid spec, stall detection, validity and resolution were run locally.
---
## Change

| Removed | Replacement |
|---|---|
| `morph_gdf` | `create_flow_cartogram` |
| `multiresolution_morph` | `create_flow_cartogram` with `MorphOptions(grid=LadderSpec(...))`; per-level option lists through `CartogramWorkflow.morph_multiresolution` |
| `Cartogram.latest` | `Cartogram.best` (returned state) or `Cartogram.last` (last stored snapshot) |
| `CartogramWorkflow.latest` | `CartogramWorkflow.last` |
| `History.latest()` | `History.last()`, or `History.best()` for the result of the run |

The tests of the deprecation warnings are removed and the tests of `best` and `last` stay. The benchmark that read `workflow.latest` reads `workflow.last`. The Unreleased changelog has a breaking-changes entry.

## Checked

- Local: 207 tests passed and 1 skipped (history, grid spec, stall detection, validity, resolution); ruff and mypy are clean.
- Not run locally: the full suite and the docs build; both run in CI.
