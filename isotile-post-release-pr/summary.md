---
pr: 14
title: "isotile: start 0.1.1.dev0 after the 0.1.0 release"
description: Development version 0.1.1.dev0 in pyproject.toml and uv.lock, an empty Unreleased changelog section, and the first-release link ignores removed.
kind: pr
topic: infra
project: isotile
url: https://github.com/bright-fakl/isotile/pull/14
branch: post-release-0.1.0
base: main
related: isotile-release-0-1-0-pr
date: 2026-10-29 22:00
before: bright-fakl/isotile main at d43e2c3 (tag v0.1.0); version 0.1.0
after: post-release-0.1.0 (all CI checks pass)
inputs: uv 0.8.17, Python 3.13.7 locally; isotile 0.1.0 on PyPI
---
## Change

| File | Change |
|---|---|
| `pyproject.toml`, `uv.lock` | version `0.1.0` becomes `0.1.1.dev0` (patch-level development version; `uv lock --check` passes) |
| `CHANGELOG.md` | empty `## [Unreleased]` section above `## [0.1.0]` |
| `scripts/link_ignore.txt` | removed the PyPI project, TestPyPI, PyPI badge, releases/compare and new docs page patterns; the fonts.gstatic.com preconnect hint stays because it is not a page |
| `docs/development.md` | the description of the ignore file no longer mentions the first release |
| `RELEASING.md` | the example development version is `0.1.1.dev0`; the one-time setup is marked done for 0.1.0 |

## Checked locally

- `mkdocs build -s` passes. `scripts/check_links.py site README.md RELEASING.md CHANGELOG.md --ignore-file scripts/link_ignore.txt`: 44 links checked, 2 skipped, 0 broken.
- The README and the documentation already say `pip install isotile`; no text about an unpublished package remained.

## Not changed

Switching carto-flow and isohedral-tiling-ui to `isotile>=0.1.0` (step 8 of the release checklist) is separate work.
