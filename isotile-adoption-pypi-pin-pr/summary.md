---
pr: 199
title: "isotile from PyPI (>=0.1.0) instead of the git commit pin"
description: carto-flow depends on isotile>=0.1.0 from PyPI; the [tool.uv.sources] git pin, its hand-edited uv.lock entry and the rev lookup of the wheel-smoke-test job are replaced by the registry entry. The full suite gives the same result as with the pin (2,092 passed, 2 skipped, 4 xfailed).
kind: pr
topic: symbol
project: carto-flow
url: https://github.com/bright-fakl/carto-flow/pull/199
branch: isotile-from-pypi
base: main
related: isotile-adoption-pin-bump-pr
date: 2026-10-29 23:30
before: main at f746bc1 with isotile a4625b7 (git pin)
after: isotile-from-pypi with isotile 0.1.0 from PyPI (2,092 passed, 2 skipped, 4 xfailed locally)
inputs: Python 3.13.7, uv 0.8.17; isotile 0.1.0 sdist and wheel from the PyPI JSON of the release.
---

Follows [isotile-adoption-pin-bump-pr](../isotile-adoption-pin-bump-pr/index.html). isotile 0.1.0 includes isotile PR 10 (`with_frame` no longer re-validates, repr, `InvalidPrototileError` subclasses `ValueError`).

## What changed

- `pyproject.toml`: `isotile>=0.1.0`; the `[tool.uv.sources]` table is removed. There was no `allow-direct-references`.
- `uv.lock`: the git entry of isotile is replaced by the registry entry (version 0.1.0, sdist and wheel URL, hash and size) by hand; 11 lines change. `uv lock --upgrade-package isotile` with uv 0.8.17 rewrites about 4,400 lines, so it was not used. `uv lock --check`, `uv lock --locked` and `uv sync --frozen` pass and the environment imports isotile 0.1.0.
- `.github/workflows/main.yml`: the wheel-smoke-test job installs the wheel alone; the lookup of the pinned rev and the extra `isotile @ git+...` requirement are removed. No other workflow, docs requirement, README or CONTRIBUTING mentions the pin.
- CHANGELOG: no entry. The Unreleased notes already name isotile as the dependency and nothing user-visible changes.

## Checks

- Full test suite: 2,092 passed, 2 skipped, 4 xfailed, the same as with the a4625b7 pin (the golden tiling tests and the layout tests are part of it).
- `ruff check`, `ruff format --check` and `mypy` are clean.
- carto-flow does not reference `InvalidPrototileError` or an isotile repr. `symbol_cartogram/tiling.py` catches `ValueError`, which `InvalidPrototileError` now subclasses.
- Not checked: the footprint and layout comparison of the pin-bump page was not rerun against 0.1.0; only the test suite covers it.
