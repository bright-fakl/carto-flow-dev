---
pr: 8
title: "isohedral-tiling-ui: isotile from PyPI"
description: The dependency changes from the commit-pinned archive URL to isotile>=0.1.0 on PyPI; the direct-reference setting is dropped and the weekly job replaces the PyPI isotile with main after the normal install.
kind: pr
topic: infra
project: isotile
url: https://github.com/bright-fakl/isohedral-tiling-ui/pull/8
branch: isotile-from-pypi
base: main
related: isotile-gui-deployment-pr, isotile-release-0-1-0-pr
date: 2026-10-29 20:00
before: bright-fakl/isohedral-tiling-ui main at ac4d320; isotile pinned to an archive of commit c1535fc
after: isotile-from-pypi (CI green on PR 8; weekly job dispatched on the branch: success)
inputs: isotile 0.1.0 from PyPI, Python 3.10 and 3.12 venvs, Playwright Chromium, ruff 0.17.3
---

App behavior is unchanged. Merging to main triggers the live Space deploy.

## Changes

| File | Change |
|---|---|
| `pyproject.toml` | `isotile>=0.1.0`; `[tool.hatch.metadata] allow-direct-references` removed (no other direct reference) |
| `.github/workflows/weekly-isotile-main.yml` | comments say PyPI release instead of pin; the step installs normally, then `uv pip install --reinstall-package isotile <main archive>` |
| `README.md` | weekly job description |
| `ci/constraints.txt`, `ci.yml`, `Dockerfile` | unchanged: no pin mentioned; `pip install .` resolves isotile from PyPI |

## Verification

| Check | Result |
|---|---|
| `pip install .` in a fresh Python 3.12 venv | isotile 0.1.0 from PyPI (requires numpy>=1.26, scipy>=1.11) |
| uv install with dev group, Python 3.10 (numpy 2.2.6, pandas 2.3.3, panel 1.9.4) | 368 passed, 24 skipped (browser tests) |
| same, Python 3.12 (numpy 2.5.4, pandas 3.1.0, panel 1.10.0) | 368 passed, 24 skipped |
| browser tests, Python 3.12, Chromium | 24 passed in a second run; one earlier run had 2 failures (a color assertion, steelblue vs #d62728), not reproduced |
| ruff 0.17.3 baseline | 3 errors (baseline 3), 0 files to format |
| CI on PR 8 | lint, mypy, tests 3.10 to 3.13, browser, docker pass; live skipped |
| weekly job dispatched on the branch | success |
| installed size, Python 3.12 | 537 MB of site-packages (scipy 109 MB, pandas 81 MB, panel 75 MB, numpy 43 MB, matplotlib 34 MB); scipy comes with isotile |

## Floors

numpy>=2.2, pandas>=2.3, panel>=1.9 are unchanged. The Python 3.10 environment resolved to numpy 2.2.6, pandas 2.3.3 and panel 1.9.4, and the tests pass there, so the floors hold on 3.10. isotile's own floors (numpy>=1.26, scipy>=1.11) are below these.

## Unverified

- The live Space deploy after merge (the Hugging Face build resolves isotile from PyPI).
- A resolution at the exact lowest versions of every direct dependency (the build of an old sdist failed in the sandbox).
