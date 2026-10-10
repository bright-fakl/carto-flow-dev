---
pr: 56
title: Document each mosaic option by its measured effect
description: Rewrites the MosaicLayoutOptions / HungarianOptions documentation on the mosaic explanation page so every option is described by what it does to a result, not by what it was intended to do. This page records the measurements each claim rests on, since the explanation page itself carries no numbers.
url: https://github.com/bright-fakl/carto-flow/pull/56
branch: docs/mosaic-option-behavior
base: origin/main @ 78060af
date: 2026-09-24 14:30
before: docs/explanations/symbol-cartogram-mosaic-layout.md @ 78060af
after: docs/mosaic-option-behavior
inputs: no new runs — this PR re-reads two existing measurement workspaces: visual_checks/mosaic-options-sweep (670 runs, 11 parameters x 4-7 values x 5 inputs x 2 morph settings) and visual_checks/grid-vs-mosaic-similarity (including the 238-run interior_bonus gating check, section 6)
kind: pr
topic: symbol
---

## What changed

`docs/explanations/symbol-cartogram-mosaic-layout.md` described `MosaicLayoutOptions`
and `HungarianOptions` by intent. Two measurement workspaces now show that several
options do not behave as described. The page's parameter tables gain a `Type` column
and a new section, **How Each Option Behaves**, describes each option by its effect.

`docs/explanations/` explains algorithms only: no result tables, no measurements, no
PR references, no decision history. Every claim on the page is therefore stated as
behavior. The table below is the audit trail: claim on the left, measured basis on
the right.

Three docstrings in `src/carto_flow/symbol_cartogram/layouts/mosaic/__init__.py`
(`distance_weight`, `outside_penalty`, `spacing`, `extra_tile_rings`,
`min_overlap_frac`) were corrected in the same way. `distance_weight`'s was actively
wrong, not merely incomplete.

No behavior changed. No source logic was touched.

## Claim-to-evidence map

Sources: **S** = `visual_checks/mosaic-options-sweep/summary.md` (with `tables.md`,
`results.jsonl`); **G** = `visual_checks/grid-vs-mosaic-similarity/summary.md`.

| Claim on the explanation page | Measured basis |
|---|---|
| `spacing` draws a gap by shrinking each symbol inside its tile: the lattice is calibrated first, then `Transform.scale` is divided by `1 + spacing`. The grid layout does the same, so leaving the assignment unchanged is correct, not anomalous | S, "spacing": fingerprint, tile size and all ~40 metrics identical for 0.0 / 0.05 / 0.2 / 0.5 on all five inputs at both morph settings. `spacing_check.json`: symbol-area ratio matches `1/(1+s)²` to machine precision; `tiles_gdf` total area unchanged |
| `outside_penalty`'s sign is input-dependent; on grouped inputs at `morph=False` every non-default value splits a group | S, "outside_penalty": world/morph=True 0.0 beats default on displacement (3.30 vs 3.85) and adjacency (0.631 vs 0.544); states/morph=True 0.0 is worse on displacement (2.56 vs 2.10). Integrity screen: districts/morph=False disqualifies 0.0, 0.25, 0.5, 2.0, 4.0, 10.0 |
| The cost function is not scale-free in `distance_weight` x `outside_penalty`; equal-ratio pairs do not agree | S, joint grid: 32 of 32 equal-ratio comparisons gave different placements. Cost is `distance_weight*dist + outside_penalty*outside - interior_bonus*connectivity + neighbor_weight*neighbor`; `interior_bonus` (2.0) and the neighbor term (0.3) are absolute |
| `distance_weight` off 1.0 splits regions more often than not | S: `distance_weight != 1.0` disqualified in 24 of 40 off-default cells on districts and world |
| `max_connectivity_iters` is inert at `morph=True`; at `morph=False` it converges within a few passes; 0 or 1 splits a group and can be slower | S: values 0/1/2/5/15/30 byte-identical on all five inputs at `morph=True`. At `morph=False` identity groups `{0} {1} {2,5,15,30}`. districts/morph=False at 0: 1 split group, adjacency 0.485 → 0.352, 16.1 s against 3.5 s at the default |
| `penalize_disconnected` is a switch, not a magnitude; on/off separates only at `morph=False` | S, "disconnected_penalty_mult" (the field this replaced): byte-identical on 8 of 10 combos; on the other two the identity groups are `{0.0}` and `{1.0, 2.0, 5.0, 10.0, 50.0}`. No integrity defect from disabling it on any input |
| `swap_repair_passes` affects integrity only; monotone to zero defects; saturation point moves with the input; inert at one tile per region | S, "swap_repair_passes": largest median-displacement change across the sweep 0.08 tiles. Defect counts fall monotonically 0 → 10 on states/districts/world; saturation at 2 (districts/morph=True), 5 (world/morph=False), 10 (districts/morph=False); inert on both states_uniform tilings; 30 never differs from 10 |
| `ring_swapback_max_hops`: defects at both ends; low values best on fidelity at one tile per region, disqualified on grouped/world; a much larger reach reintroduces a split | S, "ring_swapback_max_hops": states_uniform/morph=False hops 0-4 give displacement 1.46 / adjacency 0.74 against 2.24 / 0.52 at the default, with zero defects on that input; silhouette IoU goes the other way (0.735 vs 0.819). districts/morph=True needs >= 2, world/morph=True >= 4. districts/morph=False at 32: 1 split group the default does not have, adjacency 0.464 vs 0.485 |
| `extra_tile_rings` is non-monotone; 0 starves the pool; >= 2 splits regions everywhere; runtime grows sharply | S, "extra_tile_rings": world/morph=False 30 tiles unplaced at 0 (18 at the default), world/morph=True 24 (11). Only the default 1 is clean on all five inputs at both morph settings. states_uniform/morph=True displacement 1.30, 1.53, 1.77, 1.19, 1.77. districts/morph=True 6.0 s at default, 41.3 s at 5 |
| `min_overlap_frac` is non-monotone in both directions; the best-fidelity values split regions; 1.0 degenerates | S, "min_overlap_frac": world/morph=False IoU 0.497, 0.542, 0.654, 0.656, 0.523, 0.341 across 0.02-1.0; districts/morph=False peaks at 0.5 (0.926 vs 0.857 at the default) — both optima disqualified. 0.02 also disqualified on districts/morph=True and world/morph=True. world/morph=True at 1.0: 1138 unassigned core tiles, IoU 0.209 |
| `tile_size` at the calibrated value reproduces calibration exactly; no off-calibration value is cleanly better | S, "tile_size": x1.0 reproduces the baseline fingerprint on all ten combos. x1.25 on districts/morph=False: displacement 7.29 → 4.22, adjacency 0.485 → 0.560, by leaving 62 requested tiles unplaced. x0.8 on districts/morph=False: 2 split groups, 244 unassigned core tiles |
| `interior_bonus` is strongly non-monotone; the default is one of the few values clean on every input; it is the worse choice at one tile per region with `morph=False` | G section 6 (238 runs): integrity screen admits only 0.5 and 2.0 of the seven values tested; adjacency on states_uniform hexagon/morph=True runs 0.651, 0.761, 0.697, 0.569, 0.725, 0.716, 0.771 — a trough at 1.0 between two peaks. 2.0 wins 6 of 8 panels; the 2 losses are exactly the one-tile-per-region morph=False panels on both tilings |
| The square tiling's calibrated tile set is not fixed at one tile per region, unlike hexagon | G section 6, "Incidental correction": square morph=True IoU 0.635 → 0.701 across `interior_bonus` values; hexagon flat at 0.713 |
| `neighbor_bfs=True` does not close the mosaic-vs-grid gap at one tile per region | G section 5, "REFUTED: `neighbor_bfs=True` is not the explanation" |
| Best-fidelity values are repeatedly the disqualified ones | S, "Integrity screen": the pattern holds for `min_overlap_frac`, `tile_size`, `extra_tile_rings` and `interior_bonus` |
| Most defects appear at `morph=False` | S: 9 of the 10 combos with baseline defects or the most disqualifications are `morph=False`. G section 6: every `interior_bonus` failure but one is on districts or at `morph=False` |

## Where the sweeps predate current main

The sweep workspaces were run against older revisions. Three of their parameters no
longer exist under the names they were measured under, and two defaults have moved.
The page describes current main; the mapping is:

| In the sweep | On current main |
|---|---|
| `disconnected_penalty_mult` (float, default 10.0) | `penalize_disconnected` (bool, default True). The sweep's finding — only 0 vs non-zero separates — is the reason for the type change, and `_DISCONNECTED_PENALTY_MULT = 10.0` is now a module constant |
| `gap_bridge_mult` (float, default 5.0) | removed; `_GAP_BRIDGE_MULT = 5.0` is a module constant. Byte-identical results 0.0-20.0 on all ten combos |
| `disconnected_score_weight` (int, default 100) | removed; `_DISCONNECTED_SCORE_WEIGHT = 100` is a module constant. Byte-identical results 0-1000 on all ten combos |
| `max_connectivity_iters` default 15 | default 5. The sweep found it saturating at 2 and never binding above 4 passes |
| `interior_bonus` default 0.5 | default 2.0 (the gating check in G section 6) |

Neither removed option is mentioned anywhere in `src/` or `docs/` any more (verified
by grep). The explanation page's repair section already describes both constants
inline, without naming them as options.

## Parameter table audit

Every row of both tables was checked field by field against the dataclass definitions
in `src/carto_flow/symbol_cartogram/layouts/mosaic/__init__.py`. All nine
`MosaicLayoutOptions` fields and all nine `HungarianOptions` fields are present, with
matching names and defaults, and no row names a field that no longer exists. No
mismatch was found — the earlier PRs that removed, renamed and re-defaulted fields had
already updated both tables. The `Type` column is new.

## Checks

* `uv run mkdocs build -s` — passes (437 s, 26 of 26 gallery files, clean
  `docs/generated/` and `site/`)
* `make check` — ruff, ruff format, mypy (80 files), deptry all pass
* `uv run pytest` — 710 passed


## Correction and default change (2026-09-24)

The first draft of this page described `spacing` as an option that "never reaches the layout"
and suggested removing it. That was wrong. `GridBasedLayout` implements `spacing` the same way
— `grid/__init__.py:210-214` calibrates `tile_size` with `spacing=0` and then divides symbol
sizes by `1 + spacing`, exactly as `mosaic/__init__.py:1051` does. Leaving the assignment
unchanged is the correct semantics for a lattice layout: the gap drawn between symbols must
not decide which tile a region gets. `CirclePackingLayout` differs only because it has no
lattice.

The real inconsistency was the default. `GridBasedLayoutOptions.spacing` defaulted to 0.05 and
`MosaicLayoutOptions.spacing` to 0.0, so switching layouts changed the drawn gap with no stated
reason. `MosaicLayoutOptions.spacing` now defaults to 0.05.

Verified that the default change is rendering-only, on US states at 150 tiles:

    assignment identical : True
    tile_size identical  : True   (152406.55758)
    metrics identical    : True   (regions_correct, n_noncontiguous_regions)
    mean symbol scale    : 1.0 -> 0.952381   (ratio 1/1.05 exactly)
