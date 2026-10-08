---
pr: 68
title: ci: add a wheel smoke test for the built wheel
description: Adds a CI job that builds the wheel, installs it into a clean venv, and proves the seven bundled data files and dataset loaders work from outside the repo checkout.
url: https://github.com/bright-fakl/carto-flow/pull/68
branch: ci/wheel-smoke-test
base: origin/main @ bafb662
date: 2026-09-27 06:02
before: origin/main @ bafb662
after: ci/wheel-smoke-test @ 66835e0
inputs: the built carto_flow wheel, installed into a clean Python 3.10 venv
---

## What this guards against

`carto_flow` bundles seven data files (six `.parquet`, one `.csv`) inside the
package under `carto_flow/data/`. Nothing in the existing CI jobs checks that
these files actually ship in the built wheel: `tests-and-type-check` runs
against the source tree via `uv sync --frozen`, so a `pyproject.toml`
packaging regression that drops a data file (for example, forgetting to
declare a new file under `[tool.hatch.build.targets.wheel]`) would pass every
existing check and reach PyPI undetected. `us_covid_weekly.parquet`, added in
a recent PR, is exactly the kind of file that packaging config can miss.

The property under test — is the file present, and does the loader work —
is a property of the wheel archive itself, not of any package index. The new
`wheel-smoke-test` job therefore needs no network access, no TestPyPI upload,
and no retry loop: it builds the wheel locally with `uv build`, inspects the
archive contents directly, installs the wheel into a clean venv (not the
project venv, not editable), and runs the import and dataset-loading checks
from `/tmp/smoke-neutral`, a directory outside the repo checkout. Running
from a neutral directory matters because `import carto_flow` from the repo
root can resolve against local `src/` instead of the installed wheel (the
src-layout makes this less likely, but the job does not rely on that — it
asserts `carto_flow.__file__` does not point into `${{ github.workspace }}`
as an explicit check, not just an inference from the working directory).

## Local run output

Full sequence, matching the job's steps exactly:

```
$ uv build -o dist
Building source distribution...
Building wheel from source distribution...
Successfully built dist/carto_flow-1.1.2.tar.gz
Successfully built dist/carto_flow-1.1.2-py3-none-any.whl

$ uv run python -m zipfile -e dist/carto_flow-1.1.2-py3-none-any.whl /tmp/wheel-metadata
$ cat /tmp/wheel-metadata/carto_flow-1.1.2.dist-info/WHEEL
Wheel-Version: 1.0
Generator: hatchling 1.32.4
Root-Is-Purelib: true
Tag: py3-none-any
tag ok
purelib ok

$ (data-file presence loop)
found: cities.parquet
found: us_census_2020_state.parquet
found: us_census_2020_congressional_district.parquet
found: us_covid_weekly.parquet
found: us_state_population.csv
found: us_states.parquet
found: world.parquet

$ uv venv /tmp/smokevenv --python 3.10
Using CPython 3.10.18
Creating virtual environment at: /tmp/smokevenv

$ VIRTUAL_ENV=/tmp/smokevenv uv pip install dist/carto_flow-1.1.2-py3-none-any.whl
Resolved 30 packages ... Installed 30 packages (geopandas, numpy, pandas, pyarrow, shapely, ...)

$ cd /tmp/smoke-neutral && VIRTUAL_ENV=/tmp/smokevenv uv run --no-project python -c "<import + load checks>"
wheel smoke test passed: /tmp/smokevenv/lib/python3.10/site-packages/carto_flow/__init__.py
```

The reported `carto_flow.__file__` resolves inside `/tmp/smokevenv/...`, not
the repo checkout, confirming the checks ran against the installed wheel.

## Deliberate-failure demonstration

To prove the job can actually fail, the `load_world` assertion in
`.github/workflows/main.yml` was temporarily changed from `== 177` to
`== 178`, and the neutral-directory check step was rerun in isolation:

```
Traceback (most recent call last):
  File "<string>", line 11, in <module>
AssertionError: load_world: expected 178 rows, got 177
exit code: 1
```

The step fails with a specific message naming the loader and the row-count
mismatch, and exits non-zero. The assertion was then reverted to `== 177`
and `.github/workflows/main.yml` was re-verified with
`uv run python -c "import yaml; yaml.safe_load(open('.github/workflows/main.yml')); print('yaml ok')"`,
which printed `yaml ok`.

## Python-version choice

The job runs only on Python 3.10, the minimum supported version, not the
full `["3.10", "3.11", "3.12", "3.13"]` matrix used by
`tests-and-type-check`. The wheel is pure Python (`py3-none-any`), so its
content and installability do not vary across interpreter versions — the
question this job answers ("did all seven data files make it into the
archive, and does the code that loads them work") has the same answer on
every supported Python. Running the full matrix would multiply the job's
cost by four for no additional coverage; one version is sufficient and
cheaper.

## Runtime cost

The job adds one more `ubuntu-latest` runner to the pull-request workflow,
running once per PR (not per matrix entry). Its steps are: environment setup
(shared composite action, already paid for by other jobs), `uv build` (a few
seconds for a pure-Python package), two archive-inspection steps (near
instant), a clean `uv venv` plus `uv pip install` of the wheel and its
dependencies (dominated by pulling geopandas/numpy/pandas/shapely/pyarrow —
comparable to the dependency install time already paid by
`tests-and-type-check`), and a single Python process that loads four small
bundled datasets. No network calls beyond the existing package-dependency
resolution, no retries, no TestPyPI. Total added wall time is on the order of
the existing `tests-and-type-check` setup cost, i.e., well under a minute
beyond dependency installation.

## Review follow-up: the expected contents are derived, not listed (commit 3a1180d)

The first implementation named the seven data files and four loaders in the
workflow. That has two problems, and the second is the serious one.

It is a maintenance burden: every new bundled dataset requires editing the
workflow, by the same person who would forget to.

It also cannot catch the failure worth catching. A hardcoded list detects a
file being *dropped* from a wheel, but a newly added data file that fails to be
packaged is absent from the list as well, so the check passes. That case - a
dataset added to the source tree but not reaching the wheel - is precisely the
risk that motivated the job, and the original form was blind to it.

Both lists are now derived:

- the expected data files are read from `src/carto_flow/data`, and the wheel
  must contain all of them
- the loaders are discovered from `carto_flow.data.__all__`

Adding a dataset extends the check with no workflow edit.

### Row counts are no longer asserted

Exact counts (177, 49, (9184, 3), 243) were dropped. Dataset contents are
covered by `tests/test_data_validity.py`, which runs in the `tests-and-type-check`
job; the question here is only whether the packaged wheel can load them at all.
Each loader must return a non-empty result. Keeping exact counts in two places
would mean a legitimate data update failing in two jobs for one reason.

### Coverage increased

Six loaders are exercised, against four before: `load_us_state_population` and
`load_us_states` were never checked.

```
  load_sample_cities: 243 rows
  load_us_census: 49 rows
  load_us_covid_weekly: 9184 rows
  load_us_state_population: 6290 rows
  load_us_states: 51 rows
  load_world: 177 rows
6 loader(s) verified from /tmp/.../sv2/lib/python3.10/site-packages/carto_flow/__init__.py
```

The resolved path confirms the loaders ran against the installed wheel rather
than the source tree.

### Demonstrated failure, for the case the list could not catch

A file was added to `src/carto_flow/data` without rebuilding the wheel, which
reproduces "a dataset was added and packaging missed it":

```
Data files present in the source tree but absent from the wheel:
  newly_added.parquet
Check the packaging configuration in pyproject.toml.
exit=1
```

The check fails and names the file. Under the hardcoded list the same scenario
passed silently.
