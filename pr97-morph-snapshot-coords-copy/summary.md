---
pr: 97
issue: 73
title: Copy displaced coordinates into each morph snapshot
description: With displacement_coords and snapshot_every, each snapshot's coords now holds the positions at its own iteration instead of the final positions; geometry output is unchanged.
url: https://github.com/bright-fakl/carto-flow/pull/97
branch: fix/morph-snapshot-coords-copy
base: main
date: 2026-10-08 15:05
before: main (every snapshot's coords equal the final positions)
after: fix/morph-snapshot-coords-copy
inputs: US census (bundled), 9x6 grid via displacement_coords=(X, Y), preset_balanced, area_scale=1e-6, snapshot_every=10, n_iter=400 (13 snapshots)
---

figure: grid_snapshots.png — co-displaced grid at snapshots 0, 3, 6 and 12 over the original state outlines. Top row: before, the grid is identical in every snapshot (final positions). Bottom row: after, the grid progresses with the iteration.

## What changed

`flat_coords` is updated in place each iteration, and `_convert_coords_to_input_format` returns the array itself or views of it, so all snapshots shared one buffer. The array is now copied when a snapshot is built; nothing is copied for iterations without a snapshot.

## Evidence

- `TestSnapshotCoords` in `tests/test_flow_cartogram.py` runs the three `displacement_coords` formats ((X, Y) tuple, (N, 2), (M, N, 2)) with `snapshot_every=5`. It checks that the first and last snapshots differ, that successive snapshots differ, that the last equals `cartogram.get_coords()`, and that no two snapshots share memory. All three fail on main and pass now.
- Geometry output on the US census run above: 13 snapshots on both branches, maximum absolute coordinate difference 4.7e-9 on coordinates of order 1e6 (relative ~1e-15, the run-to-run noise of the parallel numba kernels).
- Before, all 13 snapshots had identical grid coordinates; after, they do not.
