---
pr: 186
url: https://github.com/bright-fakl/carto-flow/pull/186
issue: 177
title: The stall rule follows the lagging regions (stall_lagging)
description: A third component of the stall rule judges the lagging error (total log2 error above the tolerances) and the best iterate is chosen by the same measure; only the finest level of a ladder follows it. On the county ladder (repair-crossings, budget 3000) the finest level ends CONVERGED after 1842 iterations (mean 0.32 %, none above 10 %) instead of stalled after 200 (mean 1.08 %, 45 above 10 %); with a budget of 1000 the mean is 0.46 % and 16 counties are above 10 %. Districts and states are unchanged. Cost is up to the budget.
kind: pr
topic: flow
base: feat/unresolved-regions
branch: feat/stall-lagging-regions
related: exploration-stall-lagging-component, unresolved-regions-pr, exploration-stall-after-validity
date: 2026-10-26 23:30
before: feat/unresolved-regions @ f30c2b4
after: feat/stall-lagging-regions @ 904bfc3
inputs: see exploration-stall-lagging-component (counties with 1 km input, districts, states and strip scenes).
---

The comparison of the candidates and the figure are in `exploration-stall-lagging-component`; this page lists the change.

## Behavior

- `MorphOptions.stall_lagging` (default True). `StallMonitor.update` takes an optional `lag`; its cycle minimum is judged like the mean and the max (progress if it falls below the best of the earlier cycles by the efficiency fraction, and only while it is above 0). `errors.lagging_error` is the sum of the absolute log2 errors in excess of `max_tol` plus the excess of the mean over `mean_tol` times the number of regions; regions excused by `area_tol_cells` count as zero.
- The best iterate is the one with the lowest lagging error (in place of the lowest of the mean and max ratios) when `stall_lagging` is True; `False` restores both the stall rule and the choice of the best iterate.
- In a ladder with one set of options only the finest level follows the lagging regions; levels with their own options (a list) are untouched.
- Runs that stagnate still stall and `n_iter` bounds the run.

## Results (counties, 1 km input, auto ladder)

| validity | budget | stall_lagging | finest level | invalid | mean | above 10 % |
|---|---|---|---|---|---|---|
| repair-crossings | 1000 | False | stalled, 200 | 0 | 1.08 % | 45 |
| repair-crossings | 1000 | True | budget, 420 | 0 | 0.46 % | 16 |
| repair-crossings | 3000 | True | converged, 1842 | 1 | 0.32 % | 0 |
| check | 1000 | False | stalled, 170 | 57 | 1.37 % | 60 |
| check | 1000 | True | budget, 350 | 64 | 0.56 % | 32 |

Districts and states: identical. Test changes: the tests of the old best-iterate rule (`TestBestIterate`, `TestBestAndLast`) and the strip-scene helper of the alignment tests run with `stall_lagging=False`; the `StallMonitor` spy accepts the extra argument.

## Known costs

Iterations up to the budget (2422 iterations, about 5 times the stalled ladder, at 3000); on chaotic strip scenes the best iterate by lagging error can have one invalid polygon (seed 11) where the old one had none, and longer county runs with `"repair-crossings"` leave a few invalid polygons (1 at 3000 iterations).
