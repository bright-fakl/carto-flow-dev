---
pr: 11
title: "isotile: release infrastructure for 0.1.0"
description: Trusted-publishing workflow (tag or release to PyPI, manual run to TestPyPI), RELEASING.md, distribution checks shared with the CI smoke test, the 0.1.0 changelog entry and metadata; nothing is uploaded or tagged.
kind: pr
topic: infra
project: isotile
url: https://github.com/bright-fakl/isotile/pull/11
branch: release-infra
base: main
related: isotile-release-readiness, isotile-release-docs-pr, isotile-gui-deployment-pr
date: 2026-10-29 19:20
before: bright-fakl/isotile main at c1535fc; no publish workflow, no RELEASING.md, version 0.1.0.dev0
after: release-infra (CI results below)
inputs: uv 0.8.17, Python 3.10 and 3.12 locally, GitHub Actions ubuntu-latest; the publish workflow itself has not run
---

Phase 5 of the isotile plan, part 1, see [isotile-release-readiness](../isotile-release-readiness/index.html). No figures: the change is workflow, scripts and text.

## Workflow `pypi-publish.yml`

| Trigger | Target | Notes |
|---|---|---|
| tag `v*` pushed or release published, final version | PyPI, environment `pypi` | tag must equal `v` plus the version of `pyproject.toml` (PEP 440 normalized) |
| tag or release, pre-release or dev version | TestPyPI, environment `testpypi` | a real PyPI upload can never be replaced, so these never go to PyPI |
| manual run | TestPyPI | never PyPI |

Jobs: `build` (tests without tactile, `uv build`, `scripts/check_dist.py`, `twine check --strict`, install of the wheel into a clean Python 3.10 venv and `scripts/smoke_test.py --version`, upload of `dist` as an artifact) and `publish-pypi` or `publish-testpypi` (`id-token: write` only there, `pypa/gh-action-pypi-publish@release/v1`, download of the artifact). The upload is skipped when the version is already on the target index; creating a release together with its tag fires both events, the runs are serialized by a concurrency group and the second one uploads nothing. `scripts/release_plan.py` holds the decision logic and has seven tests.

## Other changes

- `RELEASING.md`: what each workflow does, the one-time setup (PyPI pending publisher with owner, repository, workflow file and environment name; TestPyPI; GitHub environments), the checklist (release PR with version, `uv lock` and changelog date; CI; optional TestPyPI dry run before the bump; `gh release create` or tag; verification in a clean venv; next dev version; consumers switch to `isotile>=0.1.0`).
- Version: main stays `0.1.0.dev0`. The release PR sets `0.1.0` and runs `uv lock` (checked: without it `uv lock --check` fails); the workflow refuses a tag that differs.
- `main.yml` `wheel-smoke-test` uses the two scripts and adds `twine check --strict`; the inline checks are gone.
- `pyproject.toml`: Development Status, Operating System and `Python 3 :: Only` classifiers, four project URLs, three keywords.
- `CHANGELOG.md`: one `## [0.1.0] - Unreleased` entry written as a first-release summary. Its Documentation bullet names the catalog, migration notes and benchmark that [isotile-release-docs-pr](../isotile-release-docs-pr/index.html) adds; merge both before the release.

## Verified

- Locally: `uv build`; `scripts/check_dist.py dist` passes and fails with `--version 0.1.0` against the dev build; `twine check --strict` passes; wheel installed in a Python 3.10 venv and `scripts/smoke_test.py` run from `/tmp` (81 types); `release_plan.py` for dispatch, tag equal to the version, tag differing, dev tag and branch ref (it reads test.pypi.org read-only); `uv lock` after setting `0.1.0` changes only the project version; the test suite on main passed (4277 passed, 199 skipped) before the new tests were added, the new tests pass; ruff and mypy clean.
- The workflow parses as YAML.
- CI on the PR: see the Check runs below. The first run failed on Python 3.10 because `release_plan.py` imported `tomllib`; fixed by reading the version with a regular expression.

## Environments and refs

Settings made by the maintainer: environment `pypi` with the maintainer as required reviewer and deployments restricted to the tags `v*`; environment `testpypi` without restriction; pending publishers on pypi.org and test.pypi.org. `RELEASING.md` records them and the following, which follows from the workflow and `scripts/release_plan.py` (tests cover the target rules):

- `publish-pypi` runs only for a tag event with a final version equal to the tag; any other ref makes `release_plan.py` exit with an error before the job exists, so `pypi` is never used on a branch ref. A manual run always targets `testpypi`, also from a tag.
- `release: published` runs on `refs/tags/vX.Y.Z`, which the pattern `v*` admits, as it admits a pushed tag.
- `gh release create v0.1.0 --target <sha>` creates the tag at that commit and publishes the release; the run checks out `<sha>`, whose `pyproject.toml` must say `0.1.0`. The tag push and the release event both start a run; the second waits in the concurrency queue and uploads nothing, so there is one approval. A draft release creates the tag on publication.

The behavior of the environment protection with the release event was derived from the GitHub documentation and the workflow, not observed.

## Not verified

- The workflow has never run: trusted publishing, the environments, the `release` event, the concurrency behavior on a release created with its tag and the artifact hand-off between jobs can only be tested by a real run. A dry run on TestPyPI (manual run, needs the TestPyPI publisher) is the safe test and is in `RELEASING.md`.
- actionlint is not installed; the workflow was read, not linted.
