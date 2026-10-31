---
pr: 201
title: "Runtime benchmarks for Voronoi and proportional cartograms, and a Performance docs section"
description: Two basic benchmark suites for the Voronoi cartogram and the proportional partitioning, and a top-level Performance section in the docs with one page per cartogram type.
kind: pr
topic: infra
project: carto-flow
url: https://github.com/bright-fakl/carto-flow/pull/201
branch: benchmarks-voronoi-proportional
base: main
related: remove-deprecated-names-pr
date: 2026-10-31 12:30
before: main at a126c0d; only the flow cartogram has benchmarks, and its page is explanations/performance.ipynb
after: benchmarks-voronoi-proportional (CI results on the PR)
inputs: Python 3.12, US states (49 regions) and congressional districts (432 regions, simplified at 1 km); 5 rounds after 1 warm-up round, local workstation.
---
## Change

Part B, step 1 of the comparison and benchmark plan (carto-flow #75, #80, #113).

- `benchmarks/test_voronoi_cartogram.py`: `create_voronoi_cartogram` with the default backend, weighted by population.
- `benchmarks/test_proportional_cartogram.py`: `partition_geometries` with `shrink` and `split`.
- Docs: new top-level Performance section (`docs/performance/`) with an overview, the flow cartogram page (moved from `explanations/performance.ipynb`) and a new page for the Voronoi and proportional cartograms. `benchmark_results.json` moved to `docs/performance/`; `benchmarks.yml`, `.pre-commit-config.yaml` and `RELEASING.md` follow.

## Local results

| Case | US states | Congressional districts |
|---|---|---|
| Voronoi | 0.82 s | 6.20 s |
| `split` | 0.19 s | 0.74 s |
| `shrink` | 4.84 s | 4.09 s |

Voronoi grows roughly with the number of regions. `shrink` does not: the states take longer than the districts, which have fewer vertices per region (about 700 against 210).

## Checked

- Local: the six cases pass; the new notebook was executed and the docs were built and served locally (about 5 minutes, no errors or warnings).
- The committed `benchmark_results.json` has no Voronoi or proportional entries; those subsections show a short note until the manual `benchmarks.yml` run at the next release.
- Not changed: the benchmark workflow stays manual (`workflow_dispatch`).
