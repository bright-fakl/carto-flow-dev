---
pr: 12
title: "isotile: catalog, migration notes, benchmark and README for 0.1.0"
description: A catalog of the 81 types generated at build time, migration notes from tactile, a benchmark script and page (with an optional tactile comparison) and README badges and citation; strict docs build green.
kind: pr
topic: infra
project: isotile
url: https://github.com/bright-fakl/isotile/pull/12
branch: release-docs
base: main
related: isotile-release-readiness, isotile-release-infra-pr
date: 2026-10-29 19:20
before: bright-fakl/isotile main at c1535fc; docs without catalog, migration or benchmark pages
after: release-docs (figures from make_figures.py in this directory; CI results below)
inputs: uv 0.8.17, Python 3.13 (docs group) locally, AMD Ryzen 7 5825U under WSL2; tactile 0.1.x for the comparison
---

Phase 5 of the isotile plan, part 2, see [isotile-release-readiness](../isotile-release-readiness/index.html). The docs site was not viewed in a browser (the browser extension was not connected); figure 1 is the catalog drawn by the same function as the page, figure 2 the benchmark.

## Changes

- Catalog page: `docs/hooks.py` is an mkdocs hook that adds `catalog.md` and 162 SVG files (light and dark, 81 types) to the build from the type data, with the drawing helpers of `scripts/make_doc_figures.py`. Nothing is written to `docs/`; the build takes about 13 s with the curved figures (6 s with straight ones). Tables by number of vertices with aspects, parameters, edge shapes, edge shape ids and reflections. A test checks that all 81 types are listed. The figures use example parameters and curves (see the design decision below).
- External link check: `scripts/check_links.py` (standard library; 2xx after redirects and 429 pass, 3 retries with growing wait, ignore list `scripts/link_ignore.txt`) and the workflow `check-links.yml`: weekly (Monday) and manual runs build the site and check the site, README, RELEASING.md and CHANGELOG.md and are the gate; a pull request run checks only the changed Markdown files, skips the docs site (its pages exist only after the deploy) and has `continue-on-error`, so it never fails the PR. Ignored until they exist: the PyPI project, the PyPI badges, the releases URL and the three new docs pages. Documented in `docs/development.md`; two offline tests.
- Migration page: the mapping of every tactile attribute and the fill to isotile, with the isotile code run by the page tests (tactile code is fenced `py`, not run).
- Benchmark: `benchmarks/bench.py` and the Benchmark page. Operations `fill_region`, `vertices`, `adjacency`, `neighbor_lists`, `geometric_adjacency` at about 1,000, 10,000 and 100,000 tiles for IH7, IH46, IH84 and the preset `puzzle_piece`; `check_prototile`; with `--tactile` the scanline fill against tactile up to 10,000 tiles. The lattice and geometric adjacency are compared inside the script. Total run time 26 s with tactile. Not in default CI; `tests/test_bench.py` runs it at 60 tiles.
- README: PyPI, Python, CI, license and docs badges, the `plot` extra, documentation links, background and citation of Tactile (Kaplan) and Grünbaum and Shephard. `api/index.md` lists `InvalidPrototileError`; the adjacency page links the benchmark; `deploy-docs.yml` builds when `scripts/make_doc_figures.py` changes.

## Catalog design decision

First version: every type at its default parameters with straight edges. Result: IH1 to IH20 are all regular hexagons and many square and triangle types are indistinguishable (figure 1 of the previous revision of this page), so the figures carried no information about the type.

Options considered: (a) group the types with the same default shape into one figure with a list of types; (b) draw each type at example parameters with example curves. Chosen: (b). Reasons: the types of one default shape differ in which edges are related by symmetry and in how many parameters they have, and that is visible only when the parameters are moved and the edges are curved; grouping would hide exactly that, would leave 26 types without parameters in groups of identical figures, and breaks the one-row-per-type table. The rule is stated on the catalog page: each parameter moves 40 percent from its default to the nearer finite end of its safe range (0.15 if both ends are infinite); each edge of shape J, U or S gets a fixed curve of its shape (an asymmetric wave, a bump, an S), different edge shape ids get different curves; edges of shape I stay straight; an invalid prototile halves the step and the curve heights up to four times, then falls back to the default value or a straight edge. The choice is deterministic.

Checks (run locally against `example()` of `docs/hooks.py`; the check code is not kept):

- All 81 types build a valid prototile; none fell back to the default value or to a straight edge (the check compares against the types that have parameters or curvable edges).
- 9 types stay straight because all their edges have shape I (IH20, 32, 37, 40, 72, 76, 77, 82, 93); for them only the parameters can differ.
- Visible difference: the mean absolute pixel difference of the 48 by 48 grayscale renderings (light theme) between any two types is at least 1.5 on a 0 to 255 scale for all 3,240 pairs (median 34.6); at default parameters and straight edges 388 pairs differ by less than 1 (the minimum is 0.0, median 30.2). The closest pairs are IH55 and IH71 (1.5), IH33 and IH34 (2.2) and IH42 and IH58 (3.6): they have the same prototile geometry at these parameters and differ in which edges share a curve and in the number of aspects, which the table shows. 

## Figures

figure: catalog_sheet.png — Figure 1. All 81 types as the catalog page draws them now (example parameters and curves, light theme). Compare with the straight, default-parameter version in which IH1 to IH20 were identical hexagons.
figure: benchmark_chart.png — Figure 2. Time of one run against the number of tiles for four cases, from `benchmarks/bench.py` (one run per point, so noisier than the best-of-three tables on the page). Growth is about linear; the lattice adjacency is the cheapest operation and `fill_region` of the curved preset the most expensive.

## Benchmark results (best of 3, tiles near 10,000)

| Case | fill_region | adjacency (lattice) | geometric_adjacency | tactile fill | isotile fill |
|---|---:|---:|---:|---:|---:|
| IH7 | 119 ms | 2.5 ms | 31.8 ms | 27.3 ms | 1.4 ms |
| IH46 | 67.5 ms | 1.7 ms | 23.5 ms | 28.0 ms | 1.9 ms |
| IH84 | 50.8 ms | 1.4 ms | 21.5 ms | 25.1 ms | 1.9 ms |
| puzzle_piece | 610 ms | 1.4 ms | 23.2 ms | | |

`fill` is the raw scanline fill in native coordinates (the same tiles and order as tactile, 13 to 20 times faster at 10,000 tiles; 7 to 9 times at 1,000). `fill_region` does more: frame, overlap test and boundary tiles. The full tables are on the Benchmark page.

## Verified

- `mkdocs build -s` passes (5.5 s with the catalog); the built site has 85 table rows on the catalog page (81 types and 4 headers) and 162 catalog SVG files; internal links and references are checked by strict mode.
- External links of README, docs and the built site: `scripts/check_links.py` with the ignore list reports 0 broken of 34; without the ignore entries it reports exactly the three new pages (404 until deployed) and the theme's `fonts.gstatic.com` preconnect hint. A deliberately broken link and a 404 page are reported (exit 1). lychee was not used (not installed; downloading a binary was not done). The workflow `check-links.yml` has not run on GitHub yet.
- Tests: 4136 passed, 197 skipped without the tactile and slow markers; the migration page's isotile blocks run; `tests/test_bench.py` passes.
- ruff, ruff format and mypy are clean.

## Not verified

- The rendered pages in a browser, in either color scheme; the dark catalog figures were not looked at (the light ones were), and whether the amber middle tile is distinguishable in the busiest figures (IH1, IH9, IH15) at the 120 px width of the page.
- The badges: the PyPI and Python badges show "not found" until the package is on PyPI.
- `scripts/make_doc_figures.py --check` in this environment reports all committed figures as stale (newer matplotlib than the lock file resolves in CI); the script is unchanged by this PR and CI does not run the check.
- The benchmark on macOS or Windows, and with other NumPy or SciPy versions.
