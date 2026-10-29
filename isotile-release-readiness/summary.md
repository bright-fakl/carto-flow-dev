---
title: "isotile 0.1.0: release readiness audit"
description: Checklist of what the first PyPI release of isotile needs, with evidence of the state of main at c1535fc and what the two release PRs change.
kind: exploration
topic: infra
project: isotile
branch: release-infra, release-docs
base: main
related: isotile-release-infra-pr, isotile-release-docs-pr, proposal-isohedral-tiling-library
date: 2026-10-29 19:00
before: bright-fakl/isotile main at c1535fc (version 0.1.0.dev0, no publish workflow, no RELEASING.md)
after: audit only; the fixes are in the two PRs linked under related
inputs: uv 0.8.17, Python 3.10 and 3.13 venvs locally, twine check (uvx), mkdocs build -s, curl against pypi.org and test.pypi.org (read only); nothing was uploaded, tagged or released
---

Phase 5 of the plan in [proposal-isohedral-tiling-library](../proposal-isohedral-tiling-library/index.html), sections 8.4 and 8.5. Status: OK (ready on main), FIX (changed by a release PR), GAP (missing on main, added by a release PR), MANUAL (only the maintainer can do it).

## Checklist

| Item | State on main | Evidence | Action |
|---|---|---|---|
| Name free on PyPI | OK | `pypi.org/pypi/isotile/json`, `pypi.org/simple/isotile/` and `test.pypi.org/pypi/isotile/json` return 404 on 2026-10-29 (`pypi.org/project/isotile/` returns 200 with the site's own page; the JSON and simple APIs are the authority). Recheck right before the first upload. | MANUAL |
| `name`, `description`, `readme`, `authors`, `requires-python` | OK | `pyproject.toml`: `isotile`, one-line description, `README.md`, `FKloosterman`, `>=3.10,<4.0`; `twine check --strict` passes for sdist and wheel | none |
| `version` | FIX | `0.1.0.dev0` in `pyproject.toml`, `uv.lock` holds it too; single source: `isotile.__version__` reads the installed metadata (verified in a clean venv: `0.1.0.dev0`) | PR 11 documents the bump (release PR: `pyproject.toml`, `uv lock`, changelog date); the publish workflow refuses a tag that differs from the version. A dev version on main can never reach PyPI (it routes to TestPyPI) |
| License expression and files | OK | `license = "MIT"`, `license-files = [LICENSE, NOTICE, src/isotile/data/LICENSE-tactile]`; METADATA has `License-Expression: MIT` and the three `License-File` entries | none |
| LICENSE and NOTICE with Kaplan's BSD 3-Clause | OK | wheel: `dist-info/licenses/LICENSE`, `NOTICE`, `.../src/isotile/data/LICENSE-tactile`, and `isotile/data/LICENSE-tactile`; sdist: `LICENSE`, `NOTICE`, `src/isotile/data/LICENSE-tactile`; `tests/test_packaging.py` checks that NOTICE contains the license text | `scripts/check_dist.py` now checks it in CI and in the publish workflow |
| Classifiers | FIX | Python 3.10 to 3.13, `Typing :: Typed`, Intended Audience, Topic present; missing Development Status, Operating System, `Python :: 3 :: Only` | added (PR 11) |
| Project URLs | FIX | only `Repository` | added Homepage, Documentation, Issues, Changelog (PR 11) |
| Keywords | OK / FIX | four keywords | three added |
| Dependency floors | OK | `numpy>=1.26`, `scipy>=1.11`, `shapely>=2.0`, `matplotlib>=3.7`; the `minimum-versions` job installs `--resolution lowest-direct` on Python 3.10 and runs the tests | none |
| `py.typed` | OK | in the wheel (`isotile/py.typed`); `mypy --strict` clean on `src` | checked by `check_dist.py` |
| sdist and wheel contents | OK | wheel: 15 files of the package, `types.npz` (390 KB), no tests; sdist: `src/`, `tests/`, `benchmarks/`, LICENSE, NOTICE, README, CHANGELOG, pyproject. A wheel built from the sdist has the same data files. `twine check --strict`: PASSED for both. The tests that need `docs/` skip in an sdist | none |
| Clean-venv install and smoke test | OK | wheel installed into a Python 3.10 venv, run from `/tmp`: version, 81 types, `fill_region` and adjacency for every type; the existing `wheel-smoke-test` job did the same inline | moved into `scripts/smoke_test.py`, used by CI and the publish workflow (also checks the version) |
| `uv publish --dry-run` | not used | `uv publish --dry-run` still contacts the index and needs credentials for the check; `twine check --strict` plus the build in the workflow replace it. Nothing was uploaded | none |
| CHANGELOG | FIX | `CHANGELOG.md` had an `Unreleased` section with duplicate Documentation headings and fixes relative to development states; `docs/changelog.md` includes it by snippet | rewritten as one `0.1.0` entry (PR 11); `RELEASING.md` says how the date is set. Its Documentation bullet names the pages of PR 12 |
| README | FIX | had install, quickstart, concepts, logo, license; no PyPI, Python and CI badges, no extras line for `plot`, no documentation links, no citation | badges, extras, links, citation of Tactile and Grünbaum and Shephard (PR 12). `pip install isotile` was there. The logo uses absolute raw URLs, so it renders on PyPI |
| Docs: quickstart, concepts, edge curves, adjacency, API reference, development, branding, changelog | OK | `mkdocs build -s` passes; tests run the Python blocks and check that every name of `__all__` is in `docs/api/` | none |
| Docs: catalog of the 81 types | GAP | no page | PR 12: generated at build time by `docs/hooks.py` |
| Docs: adjacency page with the benchmark | GAP | page exists, no timings | PR 12: Benchmark page, link from the adjacency page |
| Docs: migration notes from tactile | GAP | no page | PR 12 |
| API reference completeness | OK / FIX | all 21 names of `__all__` are documented (`tests/test_docs_examples.py`); the new APIs `neighbor_lists`, `offset`, `outline`, `with_parameters`, `InvalidPrototileError`, `repr`, `to_geojson`, `save_geojson` appear in the pages and the class reference; `InvalidPrototileError` was missing from the overview table of `api/index.md` | table row added (PR 12) |
| Strict docs build and link check | OK / FIX | strict build in `check-docs` and `deploy-docs.yml` (internal links and references are errors); external links: 19 of 19 existing URLs return 200; the three new pages return 404 until the docs deploy | none; external link check added in PR 12 (`check-links.yml`, weekly and manual; PRs check changed files without failing) |
| Benchmark | GAP | `benchmarks/bench.py` timed three types with lattice and geometric adjacency only; the old comparison with carto-flow is in the plan page | PR 12: operations at 1,000 to 100,000 tiles, `check_prototile`, optional tactile comparison, `--markdown`; not in default CI; a tiny-size test keeps it running |
| CI matrix | OK | `main.yml`: lint, mypy, tests on Python 3.10 to 3.13 (Linux) and 3.12 (macOS, Windows), tactile equivalence, data check, minimum versions, wheel smoke test, docs build. `deploy-docs.yml`: build on PR, deploy on push to main | PR 11 adds `twine check --strict` to the smoke job |
| Release workflow | GAP | none | PR 11: `pypi-publish.yml` |
| RELEASING.md | GAP | none | PR 11 |
| Trusted publisher (PyPI), environments (GitHub) | OK (set up by the maintainer) | pending publishers on pypi.org and test.pypi.org; `pypi` (required reviewer, tags `v*`) and `testpypi` environments | recorded in `RELEASING.md` |

## Findings that matter for the release

- The only packaging blockers were the missing release workflow and the dev version; the artifacts themselves were already correct (data files, licenses, `py.typed` in wheel and sdist).
- At default parameters and straight edges many types look alike (IH1 to IH20 are all hexagons). The catalog therefore draws each type at example parameters with example curves, by a stated rule (see isotile-release-docs-pr).
- `scripts/make_doc_figures.py --check` reports the committed figures as stale in a local environment with newer matplotlib than the lock file resolves for CI; it is not run in CI.
