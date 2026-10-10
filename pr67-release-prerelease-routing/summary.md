---
pr: 67
title: fix: route pre-release publishes to TestPyPI, add CHANGELOG rc fallback
description: Routes automatically-triggered pre-release publishes to TestPyPI instead of real PyPI and lets the CHANGELOG lookup fall back from an rc version to its base version; reviewer should check the routing trace table and the changelog-lookup unit test output below.
url: https://github.com/bright-fakl/carto-flow/pull/67
branch: fix/release-prerelease-routing
base: origin/main @ bafb662
date: 2026-09-27 02:01
before: origin/main @ bafb662
after: fix/release-prerelease-routing @ d74246c
inputs: n/a - CI workflow and documentation change
kind: pr
topic: infra
---

## What would happen today if `2.0.0-rc1` were cut

Before this change, `.github/workflows/pypi-publish.yml` gated the publish
step and the `UV_PUBLISH_URL` fallback only on `github.event_name`, not on
whether the release was a pre-release:

```yaml
- name: Publish to PyPI
  if: inputs.environment == 'pypi' || github.event_name == 'release'
  env:
    UV_PUBLISH_URL: ${{ inputs.environment == 'testpypi' && 'https://test.pypi.org/legacy/' || 'https://upload.pypi.org/legacy/' }}
  run: uv publish --trusted-publishing always
```

`release.yml` creating a GitHub Release fires `release: published` regardless
of the `prerelease` flag on that release. For a `release`-triggered run,
`inputs.environment` is unset (there is no `workflow_dispatch` input), so the
`if:` was true via the second clause, and `UV_PUBLISH_URL` fell through the
ternary's `false` branch to `https://upload.pypi.org/legacy/` — real PyPI.
The job's `environment:` field had the same gap:
`${{ inputs.environment == 'testpypi' && 'testpypi' || 'pypi' }}` also
defaults to `pypi` when `inputs.environment` is unset. So cutting
`2.0.0-rc1` today would publish it to real PyPI, an irreversible action:
a version number on PyPI cannot be reused or deleted.

`release.yml`'s CHANGELOG lookup separately hard-fails for `2.0.0-rc1`
because `CHANGELOG.md` has a `## [2.0.0]` section but no `## [2.0.0-rc1]`
section, and the old lookup only tried the exact version string.

## Fix

`pypi-publish.yml` gained a `determine-target` job that computes the
environment name (`pypi` or `testpypi`) and the matching `UV_PUBLISH_URL`
once, from either the release's `prerelease` flag (release-triggered runs)
or the `environment` workflow_dispatch input (manual runs). The downstream
`build-and-publish` job reads both values via `needs.determine-target.outputs.*`,
for its job-level `environment:` field and for `UV_PUBLISH_URL`, replacing the
two near-duplicate publish steps with one.

`release.yml`'s changelog lookup now tries the exact version first, then
falls back to the version with any `-<prerelease>` suffix stripped
(`2.0.0-rc1` -> `2.0.0`) before failing. It still fails loudly, naming both
forms it tried, if neither section exists, and still fails if the found
section is empty.

## Why the changelog falls back to the base version

An rc and the final version it leads to (`2.0.0-rc1`, `2.0.0-rc2`, `2.0.0`)
ship the same intended content — the point of cutting an rc is to validate
that content before it becomes the real release, not to describe a
different set of changes. Requiring a dated `## [2.0.0-rc1]` section
distinct from `## [2.0.0]` would mean either maintaining duplicate
changelog entries that must be kept in sync, or the entry moving/renaming
between rc and final, which then breaks any link written against the rc
section. Falling back to the base version keeps one section that both the
rc and the final release read from.

## Routing trace (hand-traced; GitHub Actions cannot run locally)

| Case | `github.event_name` | prerelease / input | resolves to `environment` | resolves to `UV_PUBLISH_URL` |
| --- | --- | --- | --- | --- |
| `workflow_dispatch`, `environment=testpypi` | `workflow_dispatch` | input = `testpypi` | `testpypi` | `https://test.pypi.org/legacy/` |
| `workflow_dispatch`, `environment=pypi` | `workflow_dispatch` | input = `pypi` | `pypi` | `https://upload.pypi.org/legacy/` |
| `release` event, pre-release (e.g. `2.0.0-rc1`) | `release` | `github.event.release.prerelease == true` | `testpypi` | `https://test.pypi.org/legacy/` |
| `release` event, final (e.g. `2.0.0`) | `release` | `github.event.release.prerelease == false` | `pypi` | `https://upload.pypi.org/legacy/` |
| anomaly: payload field empty or renamed | `release` | neither `true` nor `false` | `testpypi` | `https://test.pypi.org/legacy/` |

## The target fails closed (review follow-up, commit 71b26ad)

The first implementation selected the target by testing
`prerelease == "true"`, which means every other outcome fell through to real
PyPI: a missing or renamed payload field, or an empty expansion, would send a
release candidate to the one surface where a version can never be replaced.
The condition now tests `== "false"` instead, so real PyPI is selected only by
an explicit non-pre-release and everything else routes to TestPyPI, where a
wrong upload costs nothing.

The change is about which way the logic breaks, not about the four intended
cases, which behave identically either way. It matters because the cost is
asymmetric: a wrong TestPyPI upload is discarded, a wrong PyPI upload is
permanent, and preventing the second is the entire purpose of the job.

Verified by simulating the step's shell logic across all six rows of the table
above, including the two anomaly inputs (empty string, and `True` with
different capitalization). Both now resolve to `testpypi`; under the previous
condition both resolved to `pypi`.

The dispatch assignment is also quoted now (`environment="${{ inputs.environment }}"`).
The input is a `choice`, so its value is constrained to two options and the
missing quotes were not exploitable, but an unquoted assignment is not worth
keeping in the script that picks a publish target.

Trace detail for the `determine-target` job's `Determine publish target` step:

- The step's shell script first branches on `github.event_name`. For
  `workflow_dispatch` runs, `${{ github.event_name }}` substitutes to the
  literal text `workflow_dispatch` at compile time, so the outer `if`
  condition (`= "release"`) is false and the script takes the `else` branch:
  `environment=${{ inputs.environment }}`, which substitutes to the literal
  `testpypi` or `pypi` chosen at dispatch time.
- For `release` runs, the outer `if` is true, and the inner check
  `${{ github.event.release.prerelease }} = "true"` compares against the
  literal `true` or `false` GitHub substitutes from the release payload's
  boolean `prerelease` field.
- Either way, `environment` is then used in a second `if` to pick
  `publish_url`: `testpypi` maps to `https://test.pypi.org/legacy/`,
  anything else to `https://upload.pypi.org/legacy/`.
- Both values are written to `$GITHUB_OUTPUT` and read by
  `build-and-publish` via `needs.determine-target.outputs.environment` (used
  directly as the job's `environment:` key, so the environment's protection
  rules apply) and `needs.determine-target.outputs.publish_url` (used as
  `UV_PUBLISH_URL` in the single `Publish package` step).
- The `${{ inputs.environment }}` reference inside the `release`-branch's
  dead `else` clause is inert: for a `release`-triggered run there is no
  `workflow_dispatch` input, so the expression substitutes to an empty
  string, but that line is never reached because the outer `if` already
  took the `release` branch.

All four cases resolve to the environment/URL pairs required by the task:
pre-releases and the `testpypi` dispatch go to TestPyPI; final releases and
the `pypi` dispatch go to real PyPI.

## Verification output

YAML parses for both modified workflow files:

```
$ uv run python -c "import yaml,sys; [yaml.safe_load(open(f)) for f in ['.github/workflows/pypi-publish.yml','.github/workflows/release.yml']]; print('yaml ok')"
yaml ok
```

Extracted the modified CHANGELOG-lookup Python verbatim into a standalone
script and ran it against the real `CHANGELOG.md`:

```
=== 2.0.0 ===
used_version: 2.0.0
error: None
body starts: 'Step-by-step edits for every break below are in the\n[migration guide](https://br'
body len: 12186

=== 2.0.0-rc1 ===
used_version: 2.0.0
error: None
body starts: 'Step-by-step edits for every break below are in the\n[migration guide](https://br'
body len: 12186

=== 9.9.9 ===
used_version: None
error: CHANGELOG.md has neither '## [9.9.9]' section. Add one of them before releasing; the release notes are read from it.

ALL CHECKS PASSED
```

`2.0.0` and `2.0.0-rc1` both resolve to the `## [2.0.0]` section body, and
the two bodies are byte-identical (12186 characters, non-empty). `9.9.9`
fails with a message naming the form it looked for.

Static checks on the three changed files:

```
$ uv run mypy src/carto_flow --exclude 'mosaic_cartogram'
Success: no issues found in 80 source files

$ uv run pre-commit run --files .github/workflows/pypi-publish.yml .github/workflows/release.yml RELEASING.md
check for case conflicts.................................................Passed
check for merge conflicts................................................Passed
check yaml...............................................................Passed
fix end of files.........................................................Passed
trim trailing whitespace.................................................Passed
```

No figures accompany this report: the change is CI workflow YAML and a
documentation rewrite, with no rendered output to compare before/after.
