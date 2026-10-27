---
pr: 2
url: https://github.com/bright-fakl/isotile/pull/2
title: "isotile docs skeleton and GitHub Pages deployment"
description: Adds the mkdocs-material documentation site (home, quickstart, concepts, adjacency, API reference from docstrings, development, changelog), tests that run the page code and check that the API reference lists every public name, a strict docs build job in CI and a Pages deployment workflow for main.
kind: pr
topic: symbol
base: main
branch: docs-skeleton
related: proposal-isohedral-tiling-library
date: 2026-10-27 18:00
before: bright-fakl/isotile main at 39c5778 (phase 1)
after: bright-fakl/isotile docs-skeleton at ffef968 (PR 2, CI green, not merged)
inputs: uv 0.8.17, Python 3.10 locally, mkdocs 1.6.1, mkdocs-material 9.7.7, mkdocstrings 1.0.6 with mkdocstrings-python 2.0.9, pymdown-extensions 11.0.2, headless Chromium for screenshots (dark palette shown by setting data-md-color-scheme="slate" on a copy of the build, because the headless color-scheme flag did not switch the palette)
status: merged
---

figure: home-light.png — Home page, light palette.
figure: home-dark.png — Home page, dark palette.
figure: quickstart-light.png — Quickstart page, light palette.
figure: quickstart-dark.png — Quickstart page, dark palette.
figure: adjacency-light.png — Adjacency page, light palette.
figure: adjacency-dark.png — Adjacency page, dark palette.
figure: concepts-light.png — Concepts page, light palette.
figure: api-tiling-light.png — API reference of the tiling module, light palette.
figure: api-tiling-dark.png — API reference of the tiling module, dark palette.
figure: api-types-light.png — API reference of the types module, light palette.

## What changed

- Dependency group `docs` (`mkdocs<2`, mkdocs-material, mkdocstrings[python], `pymdown-extensions>=10.12,<12`); `uv.lock` updated; default `uv sync` unchanged. The pins are commented in `pyproject.toml`: mkdocstrings 1.0.x crashed with pymdown-extensions 12.3 (`Highlight.__init__` missing `md`), and Material warns about MkDocs 2.0.
- `mkdocs.yml`: material theme with carto-flow's light and dark palettes and navigation features, code copy, search, permalinks, strict; logo and favicon unset (Material shows its default book icon until the logo PR).
- Pages: `index`, `quickstart`, `concepts`, `adjacency`, `development`, `changelog` (pymdownx.snippets include of `CHANGELOG.md`, which also works on Windows), and the API reference `api/index`, `api/tiling`, `api/types`, `api/prototile`, `api/adjacency`.
- Docstrings: numpy style completed (Parameters, Returns, Attributes, property docstrings); Sphinx roles replaced by mkdocstrings cross-references. No behavior change.
- `tests/test_docs_examples.py`: runs the python blocks of index, quickstart, concepts, adjacency and development (shared namespace per page, temporary directory, Agg backend if matplotlib is mentioned); fails if any other docs page has a python block; checks that the `::: isotile.X` entries in `docs/api/*.md` equal `isotile.__all__` exactly and that all `__all__` names import. Skips when `docs/` is absent (sdist).
- CI: a `check-docs` job in `main.yml` (`--group docs --no-group tactile`); `deploy-docs.yml` with a build job on push, pull request (paths limited) and dispatch, and a deploy job only on push to `main` and dispatch (pages permissions, concurrency group `pages`, `github-pages` environment, `upload-pages-artifact@v3`, `deploy-pages@v4`).
- README docs link and a static docs badge; CHANGELOG Unreleased entry.

## Checks

| Check | Result |
|---|---|
| `mkdocs build -s` | no warnings; an unresolvable `::: isotile.Nope` fails the build (verified) |
| pytest | 2,843 passed, 78 skipped |
| ruff, ruff format, mypy --strict, `uv lock --check`, `_build_data --check` | clean |
| CI at ffef968 | all jobs green (lint, typecheck, tests on Linux 3.10 to 3.13, macOS 3.12, Windows 3.12, tactile-equivalence, data-check, minimum-versions, wheel-smoke-test, check-docs, deploy-docs build); the deploy job is skipped on the PR by design |
| Visual | light and dark checked for six pages; tables, code with copy buttons, API signatures, table of contents and class and method summaries render; long code comments scroll horizontally inside code blocks |
| Claims in the docs | checked by running the code (tile counts, neighbor counts, `safe_ranges` of type 7, `find_types`, table symmetry for all 81 types, lattice against geometric adjacency, tile order of `cover`) |

## Could not be verified

- The deployment itself: the `github-pages` environment only allows `main`, so the live site at https://bright-fakl.github.io/isotile/ can only be checked after the merge.
- The docs build on Windows and macOS (the docs job runs on Linux).
- A griffe DeprecationWarning (invalid escape) surfaced once and was fixed; strict mode would not have failed on it, so the build output should be watched.

## Open questions

Logo and favicon (next PR); whether the static badge becomes the Pages deployment badge once the site is live.
