---
pr: 69
title: Register the Jupyter kernel before the release docs build
description: Cutting 2.0.0-rc1 failed with "No such kernel named carto-flow". release.yml never registered the kernel that its own docs build needs, so every release would have failed the same way. Also aligns release.yml and deploy-docs.yml to the strict build that gates every pull request.
url: https://github.com/bright-fakl/carto-flow/pull/69
branch: fix/release-docs-kernel
base: origin/main @ 9c65b90
date: 2026-09-27 18:05
before: origin/main @ 9c65b90
after: fix/release-docs-kernel @ fa09ecd
inputs: n/a - CI workflow change
---

No figures. The change is a CI workflow fix with no rendered output.

## The failure

`gh workflow run release.yml -f version=2.0.0-rc1` failed at step 10 of 14:

```
jupyter_client.kernelspec.NoSuchKernel: No such kernel named carto-flow
```

The documentation executes notebooks through mkdocs-jupyter, which needs the
project kernel registered first. Two workflows already do it:

| workflow | registers the kernel |
|---|---|
| `main.yml` (`check-docs`) | yes |
| `deploy-docs.yml` | yes |
| `release.yml` | **no** |

So every release would have failed at the same step. The bug is pre-existing
and unrelated to anything merged on 2026-09-27; `2.0.0` would have hit it
identically.

## Why no earlier signal

The kernel is registered in the local development environment and in
`check-docs`, so local builds and every pull request build passed. Only
`release.yml` ran without it, and `release.yml` had not been run since the
kernel requirement was introduced. The failure was reachable only by cutting a
release, which is what the release candidate did.

For the same reason the failure cannot be reproduced locally without
unregistering the kernel from the developer's own environment, which was not
done. The CI log is the evidence.

## Strict-mode inconsistency, fixed in the same change

`check-docs` gates every pull request into main with `mkdocs build -s`. Neither
`release.yml` nor `deploy-docs.yml` used `-s`:

| workflow | before | after |
|---|---|---|
| `main.yml` | `mkdocs build -s` | unchanged |
| `release.yml` | `mkdocs build -d site` | `mkdocs build -s -d site` |
| `deploy-docs.yml` | `mkdocs build -d site` | `mkdocs build -s -d site` |

Both accepted warnings that the pull request producing the commit would have
rejected, and `deploy-docs.yml` publishes to the production site. Aligning them
is a slight widening beyond the reported failure and can be split out if the
narrower change is preferred.

## What the failed release run left behind

The run completed nine steps before failing, so several effects are permanent:

| | state |
|---|---|
| version files on `main` | bumped to `2.0.0-rc1` (commit `9c65b90`) |
| tag `2.0.0-rc1` | created |
| GitHub release | created, marked Pre-release |
| documentation | build failed; deploy skipped, as it is for any pre-release |
| TestPyPI | unchanged |
| real PyPI | unchanged - still only `1.1.2` |

Nothing was published. The irreversible surface was never touched, which is the
protection the release-candidate flow exists to provide.

## Verification

- `mkdocs build -s` on `main` at `2.0.0-rc1`: succeeds, 269.85 s. The strict
  flag does not break the release.
- All three workflows register the kernel, confirmed by grep.
- Both modified workflow files parse as YAML.
