---
pr: 62
title: Fix the multiresolution tutorial's progress output, grid sizes and comparison fairness
description: The tutorial compared a non-converging dt against another non-converging dt, labeled 1024-grid figures as 512, and held the single and multiresolution runs to different tolerances, which made multiresolution look better than it is. No figures here - the changes are notebook outputs, reviewed in the rendered page itself.
url: https://github.com/bright-fakl/carto-flow/pull/62
branch: docs/multires-tutorial-fixes
base: origin/main @ ba87610
date: 2026-09-25 18:00
before: origin/main @ ba87610
after: docs/multires-tutorial-fixes @ b75d7dd
inputs: US states (bundled), densified with max_segment_length=2000 before the 1024 comparison; congressional districts (bundled) for the closing section
kind: pr
topic: flow
---

No figures are attached. Every change here is a notebook output, so the review
surface is the rendered tutorial, built locally from this branch, rather than a
pair of PNGs extracted from it.

## What was wrong

**The dt sweep compared two non-converging runs.** The closing comparison put
`dt=0.1` against `dt=0.5`. Neither converged - `dt=0.1` simply needed more
iterations than the sweep allowed - so the figure showed two failures and
attributed the difference to the step size. It now contrasts `dt=0.5` against
`dt=0.2`, which is the default and does converge, so the comparison isolates the
step size.

**Figure labels hardcoded 512.** The single-versus-multiresolution comparison
ran at grid 1024 but its titles read 512. The labels now read
`result_single.grid.sx`, so they follow whatever the cell actually ran.

**The two runs were held to different tolerances.** The single-resolution run
used `max_tol=0.01` and the multiresolution run `max_tol=0.02`. The single run
then stalled while the multiresolution run converged, and the tutorial presented
that as evidence for multiresolution. Both now use `max_tol=0.02`. The stall was
the tolerance mismatch, not the method.

**A user warning went unexplained.** The `CartogramWorkflow` cell emitted a
"straight segment" warning because the input was not densified enough for a
1024 grid. The notebook now calls `densify_coverage(us_states,
max_segment_length=2000)` before that comparison and says why.

## What was added

- A grid sweep at 256, 512 and 1024 showing how cost scales with resolution.
- A districts section with a comparison table and an error map, so the tutorial
  demonstrates the method on a second, harder input rather than on states alone.
- Both reasons multiresolution is worth using are now shown, rather than only
  the speed argument: it is faster at equal tolerance, and it reaches
  tolerances a single-resolution run stalls before.

## On the remaining densification question

Densifying more is a workaround, not a fix. The warning originates where each
multiresolution level is handed the previous level's output, so a heavily
stretched region can leave a long straight edge that the next, finer level
reports. Re-densifying between levels would address it at source but changes
vertex counts between keyframes, which breaks the animation helpers. That
tension is unresolved and deliberately left open.

## Verification

- The tutorial executes end to end with `nbclient`, `allow_errors=False`.
- `show_progress=False` on every morph call, so no tqdm fragments reach the
  rendered page.
- `make check` clean.
