---
pr: 48
title: Honest defaults for two HungarianOptions fields
description: max_connectivity_iters drops 15 to 5 because the cap never binds, and disconnected_penalty_mult becomes a boolean because every non-zero value is indistinguishable; both verified bit-identical over 40 Hungarian solves.
url: https://github.com/bright-fakl/carto-flow/pull/48
branch: refactor/mosaic-honest-hungarian-defaults
base: main
date: 2026-09-23
before: origin/main @ 8b197eb
after: refactor/mosaic-honest-hungarian-defaults @ 14947cf
inputs: US states (uniform hexagon, uniform square, 154 tiles), congressional districts grouped by State Name, world countries (Natural Earth, Mollweide ESRI:54009, 384 nominal / 460 actual tiles) — each at both morph settings
kind: pr
topic: symbol
---

**No figures, deliberately.** The change is bit-identical by construction and verified so
over 40 Hungarian solves, which means a before/after pair would be two identical images.
The evidence below is the point of this page.

Two `HungarianOptions` fields advertise behaviour they do not have. Neither change alters
any result.

## `max_connectivity_iters`: 15 → 5

The cap never binds. The repair loop also stops as soon as a pass fails to improve on the
incumbent, and that always happens first. Passes actually run, over all five sweep inputs at
both morph settings:

| input | morph=False | morph=True |
|---|---|---|
| states (uniform, hexagon) | 2 | 2 |
| states (uniform, square) | 3 | 2 |
| states (154 tiles) | **4** | 2 |
| congressional districts | **4** | 2 |
| world countries (384 nominal / 460 actual tiles) | 2 | 2 |

The worst case over everything measured is four passes. A cap of 5 allows six, so it still
cannot bind, while no longer implying a range of behaviour that cannot occur. If an input
ever does need more, the field is still there to raise.

## `disconnected_penalty_mult`: float → `penalize_disconnected: bool`

The value scales a raise applied to a disconnected tile's cost, as a multiple of the
*static cost maximum*:

```python
disc_penalty = cost_static_max * options.disconnected_penalty_mult
```

Any multiple above one already puts that tile out of contention outright, so every value
from 1.0 to 50.0 produces the identical assignment and only 0.0 differs. It is a switch
wearing a float's clothing, and a caller reading `10.0` reasonably assumes 5.0 or 20.0 would
mean something.

Renamed to `penalize_disconnected: bool = True`. The former default moves to
`_DISCONNECTED_PENALTY_MULT = 10.0` in `_assignment.py`, following the pattern #43
established for `_GAP_BRIDGE_MULT` and `_DISCONNECTED_SCORE_WEIGHT`. The branch itself is
untouched, so no behaviour is removed: `penalize_disconnected=False` reproduces
`disconnected_penalty_mult=0.0` exactly.

**Breaking change.** `HungarianOptions(disconnected_penalty_mult=...)` now raises
`TypeError`. `disconnected_penalty_mult=0.0` becomes `penalize_disconnected=False`; every
other value was the default and needs nothing.

## Bit-identity evidence: 40 solves, all identical

Verified with the same-process technique from `visual_checks/mosaic-inert-verify/` (PR #43).
A naive end-to-end before/after comparison would look like a regression at morph=True and
would not be one — `morph_geometries` produces a different result on every run. So the morph
runs **once** and feeds both implementations inside one process: for every Hungarian solve
the layout performs, the new `hungarian_morphed_assignment` and the one from `origin/main`
are called on identical captured arguments, the old one given a shim options object carrying
`max_connectivity_iters=15` and `disconnected_penalty_mult=10.0`, and the two assignments
compared elementwise.

```
states_uniform     morph=0:   1 solve(s)  max passes run=2  IDENTICAL
states_uniform     morph=1:   1 solve(s)  max passes run=2  IDENTICAL
states_uniform_sq  morph=0:   1 solve(s)  max passes run=3  IDENTICAL
states_uniform_sq  morph=1:   1 solve(s)  max passes run=2  IDENTICAL
states             morph=0:   1 solve(s)  max passes run=4  IDENTICAL
states             morph=1:   1 solve(s)  max passes run=2  IDENTICAL
districts          morph=0:   1 solve(s)  max passes run=4  IDENTICAL
districts          morph=1:   1 solve(s)  max passes run=2  IDENTICAL
world              morph=0:  12 solve(s)  max passes run=2  IDENTICAL
world              morph=1:  21 solve(s)  max passes run=2  IDENTICAL

worst passes run over all inputs = 4 (cap allows 6)
```

Script: `visual_checks/mosaic-world-islands/pr4_same_proc.py`. `make check` clean, full
suite 632 passed. The reference table in `docs/explanations/symbol-cartogram-mosaic-layout.md`
is corrected for both fields.

## Deliberately not changed

`swap_repair_passes` and `ring_swapback_max_hops` are both live: every value gives a
distinct result, the saturation point of `swap_repair_passes` moves with the input and it
never saturates on world at morph=True, and `ring_swapback_max_hops` buys a monotonic
reduction in empty core tiles while 32 re-introduces a defect on districts. Neither is a
misleading default. Per-value tables for both are in
`visual_checks/mosaic-world-islands/tables.md`.
