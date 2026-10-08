---
pr: 43
title: Remove two inert HungarianOptions knobs from the mosaic layout
description: Evidence that gap_bridge_mult and disconnected_score_weight never change a result, and that removing them is bit-identical.
url: https://github.com/bright-fakl/carto-flow/pull/43
branch: agent/mosaic-inert-knobs
base: main
date: 2026-09-22
before: origin/main @ a095187
after: agent/mosaic-inert-knobs
inputs: US states (uniform, and 154 tiles), congressional districts grouped by State Name, world countries (Natural Earth, Mollweide, 384 tiles)
status: reviewed
---

No before/after figures: the change is bit-identical by construction, so side-by-side
panels would be two identical images. The evidence below is the point of this PR.

## Fingerprint

A full-layout fingerprint, not a summary metric: per-tile centre as raw float64 bytes,
per-tile scale, symbol sizes, base size, bounds, `source_indices`, `group_ids`,
`valid_mask`, plus the reported metrics.

| parameter | values swept | combinations | result |
| --- | --- | --- | --- |
| `gap_bridge_mult` | 0.0, 1.0, 5.0, 20.0 | 4 inputs x 2 morph = 8 | identical |
| `disconnected_score_weight` | 0, 1, 10, 100, 1000 | 3 inputs x 2 morph = 6 | identical |

The `states` case at `morph=False` was targeted deliberately: it is the only input where
the repair loop runs four passes AND two passes tie on split-region count, so it is where
a tie-break weight would bite if it ever did. Still identical.

## Insensitive, not dead

Neither code path is unreachable. The repair loop runs 2-4 passes on every input and the
gap count at pass 0 is non-zero everywhere (26-189), so the bridge bonus really executes
and really does change later passes' candidate assignments (pass-1 score moves 28 -> 32 on
US states).

- `gap_bridge_mult`: altered candidates are rejected for not improving on the incumbent;
  where a later pass does win, the same pass wins at every multiplier.
- `disconnected_score_weight`: only separates passes with equal split-region count, and the
  disconnected-tile and gap counts rank those passes the same way at any weight in [0, 1000].
  At weight 0 the score does not collapse, because the gap term survives.

Both were therefore removed by hard-coding their former defaults as module constants in
`_assignment.py` (`_GAP_BRIDGE_MULT = 5.0`, `_DISCONNECTED_SCORE_WEIGHT = 100`). The
branches are untouched, so no behaviour was removed.

## The nondeterminism trap

A naive end-to-end before/after comparison LOOKS like a regression and is not one.
At `morph=False` all five inputs are bit-identical to the a095187 baseline. At `morph=True`
all five differ -- but a baseline-against-ITSELF comparison also differs on all five at
`morph=True` while agreeing everywhere at `morph=False`, and `morph_geometries` alone
produces a different centroid hash on every run in a single unmodified worktree. One
baseline-vs-baseline pair happened to agree; a third run broke it.

The change was isolated from that noise by loading the old and new
`hungarian_morphed_assignment` into ONE process and calling both on identical captured
inputs, so the morph runs once and feeds both, with the old one given a shim options
object carrying the two removed fields at their old defaults.

```
states_uniform     morph=0/1:  1 solve   IDENTICAL
states_uniform_sq  morph=0/1:  1 solve   IDENTICAL
states             morph=0/1:  1 solve   IDENTICAL
districts          morph=0/1:  1 solve   IDENTICAL
world              morph=0:   12 solves  IDENTICAL
world              morph=1:   21 solves  IDENTICAL
```

39 assignment solves across 10 input x morph combinations, every returned array equal.

## Reported in passing, not acted on

- `max_connectivity_iters` (default 15): the cap never binds. Most passes observed is 4
  (`states` and `districts` at `morph=False`); at `morph=True` it is always 2. Any cap >= 3
  is equivalent to 15. It does real work at `morph=False`, where 0, 1 and >=2 give three
  distinct results, so it is not a deletion candidate -- but 15 is dead headroom.
- `disconnected_penalty_mult` (default 10.0): effectively boolean. Only 0 vs non-zero
  separates, and only on `states` and `districts` at `morph=False`; 1.0 through 50.0 are
  indistinguishable. The penalty is a multiple of the static cost maximum, so once it
  exceeds that maximum the tile is out of contention regardless of magnitude.

## Scripts

`verify.py` (sweep + fingerprint), `probe.py` (repair-loop trace), `same_proc.py`
(old-vs-new in one process), `cmpall.py` (end-to-end comparison), `morphhash.py`
(nondeterminism demonstration), `pin.py` (pinned-test values). Raw dumps in `base*.txt`
and `mod*.txt`.
