---
pr: 1
title: "isohedral-tiling-ui: CI and golden fixtures"
description: GitHub Actions workflow (ruff and format against the recorded baseline, advisory mypy, pytest on Python 3.10 to 3.13) and golden fixtures of the current GUI (96 preview cases, 45 SVG and GeoJSON exports, snippets and JSON exports of 15 presets and 11 types, 41 loaded design files). PR 1 of the isotile GUI port. Nothing to compare visually; the page gives the written evidence.
kind: pr
topic: symbol
project: isotile
url: https://github.com/bright-fakl/isohedral-tiling-ui/pull/1
branch: ci-golden-fixtures
base: main
related: proposal-isotile-gui, isotile-gui-pr0-pr
date: 2026-10-28 20:00
before: bright-fakl/isohedral-tiling-ui main at eb7b79e (no tests, no CI except the Space sync)
after: ci-golden-fixtures (231 tests pass locally and on Python 3.10 to 3.13 in CI)
inputs: Python 3.12, carto-flow 2.0.0, tactile 0.1.0, numpy 2.5.4, shapely 2.2.0, matplotlib 3.11.2, panel 1.10.0, ruff 0.17.3, mypy 2.4.1; fixtures written once in a scratch venv
---

PR 1 of the port plan of [proposal-isotile-gui](../proposal-isotile-gui/), section 8. It adds a safety net on the current code; the app is not ported.

## CI

`.github/workflows/ci.yml` (push to `main`, pull requests):

| Job | What it does |
|---|---|
| lint | `ruff check` and `ruff format --check` against `ci/lint_baseline.txt` (11 errors, 2 files, the counts of `main`): the job fails if a count grows. `tests/` must be clean. No existing finding is fixed. |
| mypy | runs `mypy` and reports the findings as a warning; the baseline is 495 errors in 11 files. |
| tests | `pytest` on Python 3.10, 3.11, 3.12 and 3.13 (Linux). |

`ci/constraints.txt` pins carto-flow 2.0.0, tactile 0.1.0 and ruff 0.17.3 for the CI install only. `pyproject.toml`, the Dockerfile and the Space sync workflow are unchanged.

## Fixtures

`tests/make_golden.py` ran once against the current GUI and writes `tests/data` (1.0 MB; the fixtures are a migration tool, see below):

| File | Content |
|---|---|
| `golden_preview.npz` | for the 81 types at their defaults and the 15 presets (96 cases), the result of the preview call `generate(bounds=(-1, -0.3, 1, 0.3), n_tiles=100, margin=0.25)`: centroids, areas, rotations, flips of all tiles and three polygons |
| `golden_exports.npz`, `golden_text.json` | SVG and GeoJSON exports of the 15 presets at 50, 100 and 200 tiles, as summaries (header, polygon count, colors, styles, vertex counts, centroids, GeoJSON properties); PNG export sizes; the Python snippet and the export-dialog JSON of the 15 presets and 11 types (every eighth type) |
| `designs/*.json`, `golden_text.json` | 41 design files: the Save Design and the export-dialog form of each preset (30) and 11 edge cases (no parameters, wrong and too many parameters, mode without curve, curve on an I edge, invalid outline, version 1.1, unknown and missing type, not JSON); for each the notification, the state after `LoadSavePanel._on_file_content`, and the preview |

## Tests

`tests/test_golden.py` (226 cases) reproduces each fixture from the current code: tile arrays within 1e-9, exports within 1e-6, text exactly, loaded designs by state. It also checks that the fixture has the 96 cases and that the installed carto-flow and tactile match the versions that wrote it. `tests/test_state_smoke.py` (5 tests) covers `TilingState`: type change, parameter change and reset, preset load, undo and redo.

Recorded behavior of the current loader that PR 2 has to decide on: a parameter list of the wrong length and a list that is too long are refused with a message (the pasted state does not change); a curve on an I edge is dropped silently; a mode on a straight edge is kept; an invalid outline loads.

The fixtures are temporary. PR 2 compares isotile against them, records the intended differences in the tests, replaces them by a smaller set regenerated from the ported code and deletes `make_golden.py`. The strip images were dropped: they are pixel-based and PR 2 changes the aspect colors on purpose.

## Not in this PR

- The staging Space and the Space sync (PR 4; the Space is not touched).
- Ruff and format fixes (11 errors, 2 files): the baseline gate holds them at the current count.
- The golden test for the port (isotile against these fixtures) is PR 2.
- The Playwright and headless Panel layers (PR 3 and later).
