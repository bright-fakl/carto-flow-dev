---
title: Flow cartogram performance, 1.1.2 against 2.0.0
description: One-off comparison for the 2.0.0 release. The flow morph is 3.5x to 11.6x faster than 1.1.2 depending on grid size, with identical iteration counts.
date: 2026-09-25 01:30
before: 1.1.2 (tag, 2026-03-13)
after: main @ 443529a
inputs: contiguous US states from the bundled census snapshot, exported once to WKB and fed to both versions
kind: exploration
topic: flow
status: no-action
outcome: the speedups were recorded in the 2.0.0 changelog (#61); nothing else follows
---

No figures: the output geometry is unchanged, so before and after images would
be identical. The measurement is the result.

## Why this was run

`docs/explanations/performance.ipynb` reports one benchmark run and has no
history, so it cannot answer "did 2.0.0 make the flow cartogram faster". The
published results also predated the release work by six months. This is a
one-off measurement for the release; no harness was committed, because a
cross-version harness rots the moment `MorphOptions` changes and nobody would
notice until it was needed.

## Method

`MorphOptions` gained three fields in 2.0.0 (`benchmark`, `parallel_density`,
`parallel_fft`) and lost none, so both versions accept the same call. Both
parallel flags default to `False`, so this compares serial execution.

Contiguous US states were exported once from the bundled census snapshot to
WKB and loaded by both versions, bypassing `load_us_census`: at 1.1.2 that
function required `censusdis`, a Census API key and network access, and would
have fed each version different geometry.

`morph_geometries(geoms, values, options=MorphOptions(n_iter=200,
grid_size=<grid>, show_progress=False))`. Four runs per configuration, the
first discarded for numba compilation, best of the remaining three. Same
machine, same session, AMD Ryzen 7 5825U under WSL2.

## Grid-size sweep, 34,510 vertices

| grid | 1.1.2 | 2.0.0 | speedup | iterations, both |
| --- | --- | --- | --- | --- |
| 128 | 0.438 s | 0.125 s | 3.5x | 63 |
| 256 | 1.129 s | 0.212 s | 5.3x | 113 |
| 512 | 4.848 s | 0.487 s | 10.0x | 200 |
| 1024 | 16.618 s | 1.434 s | 11.6x | 200 |

**Iteration counts are identical at every grid size.** `morph_geometries` stops
early once its error tolerances are met, so this had to be checked: without it
a wall-clock comparison could be measuring convergence behavior rather than
speed. 63, 113, 200, 200 in both versions means the two follow the same
convergence path and stop at the same point. The numerics did not change; the
work per iteration got cheaper.

## Vertex-count check

| geometry | vertices | 1.1.2 | 2.0.0 | speedup |
| --- | --- | --- | --- | --- |
| states | 34,510 | 1.234 s | 0.208 s | 5.9x |
| states, segmentized at 500 m | 241,290 | 1.321 s | 0.499 s | 2.6x |

Run at the default grid size of 256.

## What the shape of the result says

The speedup grows with grid size (3.5x at 128 to 11.6x at 1024) and shrinks
with vertex count (5.9x at 34k vertices to 2.6x at 241k). Both point the same
way: the optimization is in the per-cell grid work — density rasterization and
the FFT solve — rather than in per-vertex advection.

Practically, the larger the grid the more 2.0.0 helps. At 1024, where 1.1.2
took nearly 17 seconds, 2.0.0 takes 1.4.

## Caveats

Measured on one workstation, not on CI, so these numbers are not comparable
with `benchmark_results.json`, which is measured on a GitHub runner. One
input shape (contiguous US states) at one `n_iter`. Serial only.
