---
pr: 58
title: Add the 2.0.0 changelog and migration guide, bump to 2.0.0
description: Documentation-only change plus a version bump. No figures - nothing in the rendered output of an existing page changes; review the two new pages in the built site.
url: https://github.com/bright-fakl/carto-flow/pull/58
branch: docs/changelog-2.0
base: main
date: 2026-09-24 21:26
before: origin/main @ 5020fe5
after: docs/changelog-2.0 @ 165efe3
inputs: none (no computation)
---

# PR58 - 2.0.0 changelog, migration guide, version bump

No figures. This PR adds `CHANGELOG.md`, `docs/migrating-to-2.0.md`,
`docs/changelog.md` (a one-line snippet include), two nav entries, a README
section and the version bump. No code path changes, so no before/after result
differs.

## What to review

Serve the docs and read the two new pages:

```
cd /home/fakl/carto-flow && uv run mkdocs serve
```

Then open <http://127.0.0.1:8000/carto-flow/changelog/> and
<http://127.0.0.1:8000/carto-flow/migrating-to-2.0/>.

## Files

| File | Change |
| --- | --- |
| `CHANGELOG.md` | New. Keep a Changelog format, starts at 2.0.0. |
| `docs/changelog.md` | New. `--8<-- "CHANGELOG.md"`. |
| `docs/migrating-to-2.0.md` | New. One section per break, old and new call. |
| `mkdocs.yml` | `pymdownx.snippets` (`base_path: ['.']`, `check_paths: true`); two nav entries after Reference; `extra.version` 2.0.0. |
| `README.md` | Changelog section linking both. |
| `pyproject.toml`, `src/carto_flow/__init__.py`, `uv.lock` | 1.1.2 -> 2.0.0. |

## Verification

- `uv run mkdocs build -s` passes from a cleared `docs/generated/` and `site/`
  (392 s, 26/26 gallery files).
- `site/changelog/index.html` contains the 2.0.0 body text, the grouped
  sections and working PR links; the snippet include is not producing an empty
  page.
- Both pages appear in the built nav, and the cross-links resolve to
  `../migrating-to-2.0/` and `../changelog/`.
- `make check` passes (pre-commit, mypy on 80 source files, deptry).
- `uv run python -m pytest`: 711 passed.

## Notes on the content

- Every breaking change was checked against the code on `main` rather than taken
  from the PR titles. Four breaks not on the original list were found: the
  `value_column` -> `size` rename, the `preset_*` -> named-function replacement,
  `SymbolCartogram.metrics` -> `placement_metrics` with `simulation_history`
  removed, and the bundled datasets moving from GeoJSON to GeoParquet.
- `MosaicLayout` does not exist in 1.1.2, so the mosaic option changes (#40,
  #43, #46, #47, #48, #56) break only code written against an unreleased `main`.
  Both pages say so instead of presenting them as 1.x -> 2.0 breaks.
- The version string lives in three files, not two: `pyproject.toml`,
  `src/carto_flow/__init__.py` and `mkdocs.yml` (`extra.version`).
  `scripts/bump_version.py` already updates all three.
