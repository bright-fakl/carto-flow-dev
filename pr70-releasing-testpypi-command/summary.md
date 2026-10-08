---
pr: 70
title: Correct the TestPyPI verification command in RELEASING.md
description: Running the documented command against the real 2.0.0-rc1 found three faults, the worst of which silently installed 1.1.2 and verified the previous release while appearing to pass.
url: https://github.com/bright-fakl/carto-flow/pull/70
branch: fix/releasing-testpypi-command
base: origin/main @ c5e4d29
date: 2026-09-27 18:40
before: origin/main @ c5e4d29
after: fix/releasing-testpypi-command
inputs: carto-flow 2.0.0rc1 as published to TestPyPI, installed into a clean Python 3.10 venv
---

No figures. The change is documentation, verified by executing the command it
documents.

## How the faults were found

The command was executed for real against `2.0.0rc1` on TestPyPI, as part of
the release-candidate verification, rather than reviewed by reading. All three
faults share a failure mode: the check does not fail loudly, it passes while
testing the wrong thing or fails for a reason that looks unrelated.

## Fault 1 - no version pin

TestPyPI carries `1.0.0`, `1.1.1`, `1.1.2` and now `2.0.0rc1`. The unpinned
command installed **1.1.2**:

```
version   : 1.1.2
  load_sample_cities            243 rows
ImportError: The 'censusdis' package is required for loading US Census data
```

The verification would have reported the previous release as working and said
nothing about the release candidate. The `ImportError` is itself informative:
on 1.1.2 `load_us_census` needs `censusdis`, whereas on 2.0.0 the bundled
snapshot removes that requirement, so the two versions are clearly
distinguishable - and the check was looking at the wrong one.

The pin is written PEP 440 style: the git tag `2.0.0-rc1` normalizes to the
version `2.0.0rc1`.

## Fault 2 - missing index strategy

`--index-strategy unsafe-best-match` is required. By default uv takes every
version of a package from the first index that offers it, to avoid dependency
confusion attacks. With TestPyPI listed first, dependency resolution fails once
both indexes carry part of the tree. Pinning the version without the flag fails
outright:

```
ModuleNotFoundError: No module named 'carto_flow'
```

## Fault 3 - uv run without --no-project

Without `--no-project`, `uv run` picks up the repository's own environment, so
`import carto_flow` can resolve against local source rather than the installed
wheel. The existing `cd /tmp` was necessary but not sufficient on its own.

## Verification of the corrected command

```
version   : 2.0.0-rc1
location  : /tmp/.../tpypi3/lib/python3.10/site-packages/carto_flow/__init__.py
  load_sample_cities            243 rows
  load_us_census                 49 rows
  load_us_covid_weekly         9184 rows
  load_us_state_population     6290 rows
  load_us_states                 51 rows
  load_world                    177 rows
subpackage imports: ok
```

The resolved path confirms the installed wheel was used. `load_us_census`
returning 49 rows with no `censusdis` present confirms the bundled census
snapshot reached the wheel.

## What this establishes about 2.0.0rc1

Beyond the documentation fix, executing the corrected command validated the
release candidate itself: the metadata was accepted by the index, trusted
publishing over OIDC worked on its first ever use, dependency resolution
succeeds from a clean environment, and every bundled dataset loads from the
published artifact.
