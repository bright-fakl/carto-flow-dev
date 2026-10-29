---
pr: 13
title: "isotile: release 0.1.0"
description: Version 0.1.0 in pyproject.toml and uv.lock and the dated 0.1.0 changelog heading; merging does not publish, the release is created afterwards with gh release create.
kind: pr
topic: infra
project: isotile
url: https://github.com/bright-fakl/isotile/pull/13
branch: release-0.1.0
base: main
related: isotile-release-readiness, isotile-release-infra-pr, isotile-release-docs-pr
date: 2026-10-29 21:00
before: bright-fakl/isotile main at 3392394; version 0.1.0.dev0; changelog heading "0.1.0 - Unreleased"
after: release-0.1.0 (CI results below)
inputs: uv 0.8.17, Python 3.13.7 locally; TestPyPI dry run of 0.1.0.dev0 passed on main at 3392394 (build, publish-testpypi); pypi.org returned 404 for isotile on 2026-10-29
---
## Change

| File | Change |
|---|---|
| `pyproject.toml` | `version = "0.1.0.dev0"` becomes `"0.1.0"` |
| `uv.lock` | the project entry becomes `0.1.0` (`uv lock`) |
| `CHANGELOG.md` | heading `## [0.1.0] - Unreleased` becomes `## [0.1.0] - 2026-10-29` |

## Checked locally

- `uv lock --check` passes.
- `uv build` builds the sdist and the wheel; `scripts/check_dist.py dist --version 0.1.0` finds the licenses, `py.typed` and the data files in the wheel, the sdist and the wheel built from the sdist; `twine check --strict` passes for both files.
- The changelog entry was read against the merged changes and lists the APIs of the merged pull requests.

## After the merge

Merging does not publish. The release is created with `gh release create v0.1.0 --target <merge sha>` (command in `RELEASING.md`), after `main.yml` and `deploy-docs.yml` pass on the merge commit. The `pypi` environment requires approval and accepts tags `v*` only.

## Not verified

The publish workflow has run once, as the manual TestPyPI dry run; the `release: published` event and the upload to PyPI have not run.
