---
pr: 36
title: Speed up mosaic calibration: skip adjacency during search, vectorise lattice adjacency
description: Re-profiled the mosaic layout (calibration, tiling.generate/adjacency, assignment, repair) before optimising; skipped lattice-adjacency computation during calibrate_tiling's tile-size search trials and vectorised _compute_adjacency_from_lattice with a KD-tree. Both changes are bit-identical to the previous output - verified on every deterministic (morph=False) config and shown to add no divergence beyond this codebase's pre-existing morph-step float noise on the morph=True configs.
url: https://github.com/bright-fakl/carto-flow/pull/36
branch: perf/mosaic-calibration
base: main
date: 2026-09-20
before: main @ 9064d77
after: perf/mosaic-calibration @ 997c725
inputs: US states (bundled, ~150 tiles via load_us_census(level="state") population), congressional districts (bundled, 432, 1 tile each), congressional districts with group_by="State Name"; each with and without morph
---

## No before/after figures - this is a pure performance change

Output is bit-identical (see below), so there is nothing visual to compare. In place of
figures, this directory holds the raw evidence:

- `profiles/before/` and `profiles/after/` - cProfile `.prof` and `.txt` dumps (top 40 by
  cumulative time) for all six configs, plus `timings.json` with whole-`compute()` wall times.
  Both taken against current `main` @ 9064d77 (includes #29-#35).
- `bitcheck/before/` and `bitcheck/after/` - `LayoutResult.serialize()` + `result.metrics` (as
  JSON) and the styled tile geometry (as WKB hex) for all six configs.
- `scripts/` - the three ad-hoc scripts used to produce the above
  (`_profile_mosaic.py`, `_bitcheck_mosaic.py`, `_compare_morph.py`). Not part of the package;
  kept here only so the numbers below are reproducible.

Note: an earlier pass at this PR was accidentally branched from a stale local `main` missing 4
merged PRs (#31/#32/#34/#35). That produced a misleading profile in which contiguity repair
appeared to dominate one configuration. It was caught before merging (CI never triggered on the
first push; tracing that down found the branch's merge-base was behind `origin/main`) and the
branch was rebased onto current `main`. All data in this directory is from the corrected base.

## Bit-identity evidence

**`morph=False` configs (states, districts, districts grouped by state)** - the three configs
the calibration/adjacency changes directly affect, and the only configs in this pipeline free
of the flow-cartogram's pre-existing morph-step float noise: `serialize()` JSON equal by
Python dict equality, styled-geometry WKB hex equal byte-for-byte, every `MosaicMetrics` /
`AlgorithmMetrics` field equal (including `n_unassigned_core_tiles` and
`n_enclosed_unassigned_tiles`), for all three inputs. Confirmed stable across repeated runs on
both sides (not just before==after, but before==before and after==after across separate
process launches).

**`morph=True` configs** - `main` already has small run-to-run floating-point noise from the
flow-cartogram's numba-parallel morph step (confirmed by running the *unmodified* `main` tree
three times in separate processes: `tile_size` varied at ~1e-10 relative). Comparing before vs
after: `tile_size` relative difference ~6e-16 to ~3e-15 (float64 machine epsilon - below
`main`'s own noise floor), max tile-vertex coordinate difference ~5e-9 to ~1.4e-8 (absolute,
Albers-projection metres), every other metric exactly equal. This branch adds no divergence
beyond what `main` already has.

`load_world()` was not used as a bit-identity reference, per the documented prior run-to-run
variation on that input; it was used for profiling only (not included in the final config set
above, since all three states/districts variants already covered the multi-tile and
one-tile-per-geometry cases the task asked for).

## Numbers

| config | calibrate_tiling before | calibrate_tiling after | lattice-adjacency share (before) |
|---|---|---|---|
| states, nomorph | 0.206s | 0.167s | 0.042s (20%) |
| districts, nomorph | 1.504s | 0.804s | 0.696s (46%) |
| districts grouped, nomorph | 1.491s | 0.889s | 0.692s (46%) |

`_compute_adjacency_from_lattice` no longer appears in any "after" profile's top 40 for the
search-heavy configs (districts) - now only called once, for the accepted tile size.

Whole-`compute()` wall time:

| config | before | after |
|---|---|---|
| states, morph | 1.686s | 1.685s |
| states, nomorph | 0.772s | 0.745s |
| districts, morph | 5.797s | 4.880s |
| districts, nomorph | 4.392s | 3.701s |
| districts grouped, morph | 5.714s | 4.727s |
| districts grouped, nomorph | 4.542s | 4.180s |

Full analysis is in the PR description.
