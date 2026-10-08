STATUS: PRELIMINARY / NOT FINAL - awaiting an 8/14/16 comparison table before
any default is chosen. That choice is the user's, not the agent's.

Code change (HungarianOptions.ring_swapback_max_hops 8 -> 14), docs, and
tests are committed on branch `worktree-agent-ad6b42019a759c778` in this
worktree (commit 291b652, based on main@9c664f9). Nothing pushed, no PR
opened, default left at 14 in the meantime per the coordinator's
instruction -- this is not itself the chosen final value.

## Corrected account of the two earlier discrepancies

Both were errors in how the task brief was written, not measurement errors
on this branch's side; confirmed by the coordinator.

1. **The "districts/morph=True: ring 6->0, empty core 10->4, enclosed 1->0"
   verify numbers were PR #33's hops=8->16 column**, transcribed into a
   14-hop brief by mistake. They were never a 14-hop measurement. This
   branch's actual hops=14 result on that config is ring 6->5, empty_core
   10->9, enclosed 1->0 (confirmed by a direct hop sweep: (6,10,1) at
   8/10, (5,9,0) at 12/14, (0,4,0) at 16+).

2. **The "no configuration regresses" claim and the aggregate pp_min/
   pp_mean (0.1249 / 0.5577) covered a different 8-config set** than this
   branch's harness. The original sweep used the synthetic 3x3 fixture +
   states + districts + districts_group_by (x morph), not world. This
   branch's harness substituted world for the fixture, so the aggregates
   were never comparable, and world -- never part of the original sweep
   -- is exactly where the split-region regression (5->6) and the worse
   pp_min (0.1483->0.1187) at hops=14 appear. The "mean of per-config
   summaries" methodology itself was fine; the config sets just differed.

## What's running now

`sweep_hops.py` runs the same code (swap-back logic is unchanged between
main and this branch; only the default differs) at hops in {8, 14, 16},
explicit `HungarianOptions(ring_swapback_max_hops=...)`, across the SAME
8 configs as the earlier before/after run here (states, districts,
districts_group_by, world x morph True/False) -- so 8/14/16 are finally on
one consistent config set. Results are appended one line at a time to
`sweep_8_14_16.jsonl` as each of the 24 runs completes (cheap configs
first, world last), so a partial sweep survives an interruption.

See the agent's report to the coordinator for the full per-config
8/14/16 table once the sweep finishes.

## 8/14/16 sweep — complete (same code, same 8 configs, explicit hops)

Raw data: `sweep_8_14_16.jsonl` (24 rows, one per config x hops, written
incrementally as each run finished). before-baseline throughout = the
swap-back logic itself, unchanged between main@9c664f9 and this branch;
only the default value differs, so every row below used an explicit
`HungarianOptions(ring_swapback_max_hops=...)` override on this branch's
code.

| case | hops | ring | empty core | enclosed | split regions | split groups | converged | pp_min | pp_mean |
|---|---|---|---|---|---|---|---|---|---|
| states/morph=True | 8 | 2 | 2 | 0 | 0 | 0 | True | 0.3401 | 0.6969 |
| states/morph=True | 14 | 1 | 1 | 0 | 0 | 0 | True | 0.3373 | 0.6952 |
| states/morph=True | 16 | 1 | 1 | 0 | 0 | 0 | True | 0.3373 | 0.6952 |
| states/morph=False | 8 | 4 | 3 | 0 | 0 | 0 | True | 0.2519 | 0.6858 |
| states/morph=False | 14 | 4 | 3 | 0 | 0 | 0 | True | 0.2519 | 0.6858 |
| states/morph=False | 16 | 4 | 3 | 0 | 0 | 0 | True | 0.2519 | 0.6858 |
| districts/morph=True | 8 | 6 | 10 | 1 | 0 | 0 | True | 0.1526 | 0.4813 |
| districts/morph=True | 14 | 5 | 9 | 0 | 0 | 0 | True | 0.1377 | 0.4851 |
| districts/morph=True | 16 | 0 | 4 | 0 | 0 | 0 | True | 0.1165 | 0.4672 |
| districts/morph=False | 8 | 6 | 16 | 1 | 0 | 0 | True | 0.1192 | 0.4497 |
| districts/morph=False | 14 | 4 | 14 | 0 | 0 | 0 | True | 0.1249 | 0.4499 |
| districts/morph=False | 16 | 2 | 12 | 0 | 0 | 0 | True | 0.1088 | 0.4453 |
| districts_group_by/morph=True | 8 | 8 | 12 | 0 | 0 | 0 | True | 0.1747 | 0.4699 |
| districts_group_by/morph=True | 14 | 6 | 10 | 0 | 0 | 0 | True | 0.17 | 0.4754 |
| districts_group_by/morph=True | 16 | 3 | 7 | 0 | 0 | 0 | True | 0.17 | 0.4717 |
| districts_group_by/morph=False | 8 | 6 | 16 | 1 | 0 | 1 | **False** | 0.1311 | 0.4785 |
| districts_group_by/morph=False | 14 | 4 | 14 | 0 | 0 | 0 | **True** | 0.1249 | 0.4863 |
| districts_group_by/morph=False | 16 | 3 | 13 | 0 | 0 | 0 | **True** | 0.1449 | 0.4913 |
| world/morph=True | 8 | 9 | 32 | 4 | 5 | 0 | False | 0.1483 | 0.756 |
| world/morph=True | 14 | 7 | 30 | 6 | **6** | 0 | False | 0.1483 | 0.7485 |
| world/morph=True | 16 | 6 | 29 | 4 | **6** | 0 | False | 0.1483 | 0.751 |
| world/morph=False | 8 | 23 | 49 | 4 | 4 | 0 | False | 0.1323 | 0.746 |
| world/morph=False | 14 | 20 | 46 | 1 | 3 | 0 | False | 0.1323 | 0.7431 |
| world/morph=False | 16 | 20 | 46 | 1 | 3 | 0 | False | 0.1323 | 0.743 |

Aggregate (sum of counters / mean of per-config pp across these 8 configs):

| hops | sum ring | sum empty core | sum enclosed | sum split regions | sum split groups | # converged /8 | min(pp_min) | mean(pp_mean) |
|---|---|---|---|---|---|---|---|---|
| 8 | 64 | 140 | 11 | 9 | 1 | 5 | 0.1192 | 0.5955 |
| 14 | 51 | 127 | 7 | 9 | 0 | 6 | 0.1249 | 0.5962 |
| 16 | 39 | 115 | 5 | 9 | 0 | 6 | 0.1088 | 0.5938 |

Notable, not smoothed over:
- `split_regions` for world/morph=True gets *worse* going from 8 to either 14 or 16 hops (5 -> 6),
  identically at both 14 and 16 -- the extra reach does not fix it and this is the one metric that
  moves the wrong way as reach increases, on either candidate value.
- 14 and 16 tie on `sum split_regions` (9 each, same as 8) and on `# converged` (6/8, both beat 8's
  5/8) -- convergence and split-region counts do not distinguish 14 from 16.
- 16 dominates 14 on every hole-closing counter (ring 39 vs 51, empty core 115 vs 127, enclosed 5
  vs 7) and on `min(pp_min)` (0.1088 vs 0.1249 -- though lower pp_min is *worse* compactness, so
  this is not a clean win for either direction; see districts/morph=True where 16 gives the worst
  per-config pp_min of the three, 0.1165, while still closing the most holes).
- districts_group_by/morph=False is the one census config where 16 has a worse `pp_min` (0.1449)
  than 14 (0.1249) despite closing one more hole -- reach vs. compactness genuinely trade off
  differently per config; there is no hop count that is a strict Pareto improvement over the
  others across every config and every metric simultaneously.

This is a holes-vs-compactness trade-off between 14 and 16, and a genuine (if small) regression at
both 14 and 16 on world/morph=True's split-region count relative to 8. Picking the shipped default
from here is a judgement call left to the user.

## Final: shipped as 16, not 14 (2026-09-20)

The user's decision was 16, on the reasoning that holes are the defect users
keep noticing visually and 16 closes materially more of them than 14 (see
the sweep table above and `summary.md`). The compactness cost is accepted
knowingly. PR: https://github.com/bright-fakl/carto-flow/pull/34. Pushed
branch `fix/mosaic-ring-swapback-reach`, commit 825aee8, verified against
`origin/fix/mosaic-ring-swapback-reach` directly (HEAD == remote, and
`ring_swapback_max_hops: int = 16` read back from the remote tree via
`git show`).


## Correction: the "hash-seed sensitive" finding above was wrong (2026-09-20)

The coordinator independently ran the world configuration three times under
`PYTHONHASHSEED` 0, 1 and 12345 (default hops=16) and got a bit-identical
assignment vector every time, and pointed out the mechanism I proposed
cannot exist: `PYTHONHASHSEED` only salts hashing of `str`/`bytes`/
`datetime`; the repair loop's tie-breaking runs over integer tile indices,
and `hash(n) == n` for ints regardless of the seed, so a set/dict keyed on
tile indices iterates identically in every process.

I reproduced the disagreement directly rather than assume either side.
Script: a minimal harness calling `MosaicLayout(morph=True)` at the default
`ring_swapback_max_hops=16` on the bundled world dataset (same filtering,
CRS, and 600-tile budget as `make_figures.py`'s `world_gdf()`), printing
`ring_used`, `empty_core`, and `hash(tuple(assignments))`.

- **Unseeded, 3 consecutive runs:** `ring_used` 6, then 3, then 3 (two
  distinct outputs, not one).
- **`PYTHONHASHSEED=0`, 2 runs:** 3, 3 (matched, but that alone doesn't
  prove seed-dependence).
- **`PYTHONHASHSEED=1`, 2 runs:** 6, then 3 — **the same seed gave two
  different outputs.**
- **`PYTHONHASHSEED=12345`, 2 runs:** 3, then 6 — same again.

Same seed does not guarantee the same output, and different seeds
sometimes agree. This rules out hash-seed as the mechanism, exactly as the
coordinator said. **The earlier "hash-seed sensitive" explanation was
wrong and is retracted** — corrected in this file, `summary.md`, and the
PR #34 body.

What's actually true, demonstrated but not explained: the `world`
configuration (176 countries, many small-population tile-count ties)
produces **genuine run-to-run nondeterminism** across separate process
invocations of identical code with identical options — on `main` as well
as on this branch, so it predates and is unrelated to this PR. The root
cause has not been identified (candidates include floating-point
summation order under threaded linear algebra, or some other source of
non-seed randomness) and nothing here attributes one. `states`,
`districts`, and `districts_group_by` were stable across every run in
this investigation — only `world` showed the effect.

Practical consequence for this directory: the `world_*` numbers and
figures here are one run each, not a guaranteed-reproducible measurement.
`PYTHONHASHSEED=0` remains pinned in `make_figures.py` for internal
consistency across this PR's own regenerations, but — now demonstrated,
not merely disclaimed — it is not a fix and does not by itself guarantee
reproducing these exact `world` numbers on a fresh run. This is flagged
as a real, separate finding worth investigating on its own; nothing in
this PR was changed because of it.
