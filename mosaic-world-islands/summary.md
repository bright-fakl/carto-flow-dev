---
title: Why the mosaic layout drops regions on world countries, and why its contiguity repair is slow
description: Two independent mechanisms lose a region's tiles on multi-landmass inputs, a 99.5%-wasted path enumeration explains the repair cost, and both are fixed bit-identically or with evidence.
branch: perf/contiguity-path-reachability-precheck, fix/mosaic-component-pool-overlap, feat/mosaic-min-one-tile, refactor/mosaic-honest-hungarian-defaults
base: main
date: 2026-09-23
before: origin/main @ a095187 (investigation) and @ 8b197eb (before/after measurements)
after: the four branches above
inputs: africa (Natural Earth, Mollweide ESRI:54009), world countries (same), world mainland only, US states, congressional districts grouped by State Name
kind: exploration
topic: symbol
status: led-to
related: pr44-contiguity-reachability-precheck, pr46-mosaic-component-pool-overlap, pr47-mosaic-min-one-tile, pr48-mosaic-honest-hungarian-defaults
---

figure: fig_africa_b150.png — africa, the clean control: no region loses a tile at either morph setting
figure: fig_world_b384.png — world: red regions receive no symbol at all, amber ones are short
figure: fig_world_mainland_b384.png — world with every island land mass dropped: completely clean
figure: m2_world_b384_morph1.png — cross-component overwrite, before and after the fix
figure: m2_world_b384_morph0.png — the same at morph=False
figure: m2_world_b800_morph1.png — the same at a larger tile budget
figure: m1_world_b384_morph1.png — min_one_tile_per_region, off (default) above and on below
figure: m1_world_b384_morph0.png — the same at morph=False

## A note on tile budgets

Every world budget below is written `nominal / actual`. The fixture builds tile counts as
`max(1, round(pop / pop.sum() * budget))`, and because 140 of 176 countries hold less than
half a tile's worth of population, the `max(1, ...)` floor raises the requested total well
above the nominal figure: nominal 300 requests 384 tiles, 384 requests 460, 800 requests
848, 1500 requests 1527. Earlier write-ups of this input quote only the nominal number and
understate the tile count by up to 28%. Nothing in the library is wrong here — `tile_count`
is a caller-supplied column, so the rounding convention is the caller's.

## What was asked, and the headline

Why does the mosaic layout leave regions without a symbol on world countries, is it the
islands, and why does the contiguity repair take tens of seconds?

**It is the islands, but not in the way it looks.** Two independent mechanisms lose tiles,
and at `morph=True` the regions that actually lose them are mostly *mainland* countries —
Germany, Belgium, both Koreas, Bhutan, Timor-Leste. The islands are the ones taking their
tiles. The earlier framing of this investigation, that the failures were island states
losing out, is right only at `morph=False`, where the other mechanism dominates.

## The three-input control

| input | budget nominal / actual | morph | regions short | regions with no symbol |
|---|---|---|---|---|
| africa (51 countries, 2 components) | 150 / 159 and 300 / 306 | both | 0 | 0 |
| world (176 countries, 24 components) | 384 / 460 | True | 8 | 6 |
| world | 384 / 460 | False | 18 | 14 |
| world | 800 / 848 | True | 6 | 3 |
| world | 1500 / 1527 | True | 6 | 2 |
| **world mainland only (150 countries, 1 component)** | 384 / 446, 800 / 831, 1500 / 1511 | both | **0** | **0** |

"Mainland only" keeps the countries in the **largest connected component of the
land-adjacency graph** and drops the rest. On this input that component holds 150 of 176
countries — all of Afro-Eurasia *and* the Americas, which are linked to Europe because
Natural Earth's France polygon includes French Guiana, bordering Brazil and Suriname. The
26 dropped countries form the other 23 components: Australia, Japan, Cuba, the UK+Ireland
pair, the Philippines, Fiji and so on.

Dropping them makes the input perfectly clean at every budget and both morph settings. Tile
loss is entirely a multi-component phenomenon.

## Mechanism 1 — a component with an empty tile pool

Each core tile is assigned to exactly one geographic component. A region on a land mass
that no lattice cell overlaps by `min_overlap_frac` (default 0.1) wins no core tile, its
component's pool is empty, and the per-component loop skips it outright:

```python
if not pool_c or int(counts_c.sum()) == 0:
    continue          # the region's tile is lost here, silently
```

`extra_tile_rings` cannot rescue it: the expansion grows *from* the pool, and growing an
empty set gives an empty set.

At world 384 / 460, `morph=True`: **Bahamas** (best overlap 0.034 of a tile) and **Trinidad
and Tobago** (0.009). At `morph=False`: thirteen regions — Fiji, Bahamas, Falkland Is., Fr.
S. Antarctic Lands, Puerto Rico, Jamaica, Vanuatu, New Caledonia, Solomon Is., Taiwan,
N. Cyprus, Cyprus, Trinidad and Tobago.

## Mechanism 2 — one component overwriting another's tiles

Component pools **overlap**, because `extra_tile_rings` expanded each component's pool
independently and an island's ring reaches across the water into the mainland's *core*
tiles. Both components then solve over those tiles and both place a symbol; the write-back
assigns unconditionally, so whichever component is enumerated last silently wins:

```python
for t in pool_c:
    local_g = int(assignment_c[t])
    if local_g >= 0:
        assignment[t] = int(geom_indices_arr[local_g])
```

All eight overwrites at world 384 / 460, `morph=True`:

| tile | assigned by | overwritten by |
|---|---|---|
| 1666 | Belgium (component 1) | United Kingdom (component 12) |
| 1667 | Germany (component 1) | United Kingdom (component 12) |
| 1732 | Germany (component 1) | United Kingdom (component 12) |
| 574 | Timor-Leste (component 1) | Australia (component 16) |
| 1490 | Bhutan (component 1) | Japan (component 21) |
| 1491 | South Korea (component 1) | Japan (component 21) |
| 1621 | North Korea (component 1) | Japan (component 21) |
| 1622 | South Korea (component 1) | Japan (component 21) |

**Per-region verdict at 384 / 460, `morph=True`.** Bahamas and Trinidad and Tobago fail by
mechanism 1. Timor-Leste, North Korea, Bhutan and Belgium lose their only tile to mechanism
2; South Korea (3 → 1) and Germany (4 → 2) lose two each. They do not all fail the same way.

Candidates eliminated by measurement: the rectangular `linear_sum_assignment` never starved
a component (pool ≥ demand everywhere measured), and the component-splitting logic
allocates correctly — it is the write-back that loses the tiles.

## Mechanism 3 — the contiguity repair, and why it was slow

`repair_contiguity`'s `_enumerate_paths` is a heap over **paths**, not nodes. It keeps no
visited set, so a node is re-expanded once per prefix that reaches it, and the search ends
only when enough candidates have been yielded **or the heap empties**. When nothing reaches
the destination, "the heap empties" means enumerating every simple path of up to ten nodes
— about 1.3e5 heap operations to establish that one satellite cannot be repaired at all,
repeated once per satellite and once per pass.

On the captured world 800 / 848 call at the default ten passes: **11,807,758 heap
operations, of which 11,745,176 (99.5%) are inside the 80 calls that yield nothing** — and a
plain node BFS proves all 80 unreachable in linear time. Cost is exactly linear in
`max_passes` (1.48M pops per pass, constant), because every pass redoes the identical
hopeless enumeration.

Scaling: cost ≈ (unrepairable satellites) × (simple paths within ten hops, a lattice
constant) × `max_passes`. Tile count and region count enter only through the satellite
count. **The number of components is the driver** — a satellite is unreachable precisely
when a region's tiles are split across a sea gap, so this mechanism has the same root cause
as the other two. World mainland only, at 1511 tiles and one component, is cheap; world at
848 tiles and 24 components is not.

## What `swap_repair_passes` and `ring_swapback_max_hops` cost and buy

Full tables in `tables.md`. In brief, at world 800 / 848:

* `swap_repair_passes` at `morph=True` runs 8.8 s with 16 non-contiguous regions at 0 and
  38.3 s with 6 at the default 10, and **never saturates** — every value has a distinct
  fingerprint. At `morph=False` it saturates at 2 (values 2, 3, 5 and 10 share one
  fingerprint) yet still costs 7.5 s more at 10 than at 2. On districts it is runtime-flat
  at ~4 s and takes split groups from 12 to 0.
* `ring_swapback_max_hops` costs ~6 s at `morph=True` and ~10 s at `morph=False` for the
  default 16 over 0, and buys a monotonic fall in empty core tiles (135 → 32, 142 → 81).
  On districts it is runtime-flat and takes split groups from 2 to 0 by hop 2.

Neither default was changed. The right answer for `swap_repair_passes` is the pre-check,
not a lower cap, and every `ring_swapback_max_hops` value gives a distinct result while 32
re-introduces a defect on districts.

## A separate problem this investigation exposed: `_build_cost_matrix`

Not fixed, not in scope, recorded so it can be picked up.

`_build_cost_matrix` normalises the **squared** centroid distance by the **global maximum**
squared distance:

```python
dist_matrix = dx**2 + dy**2
max_dist = dist_matrix.max() or 1.0
dist_norm = dist_matrix / max_dist
```

On a world-extent input in Mollweide the maximum squared distance is about 1.6e15, so a
9000 km displacement scores `(9.1e6)² / 1.6e15 ≈ 0.05`, against an `interior_bonus` worth
up to **2.0**. The distance term is worth about 2.5% of the connectivity term at full range.
The assignment is effectively distance-blind at continental scale.

Measured displacement between each placed tile and the centroid of the region owning it, on
world 384 / 460:

| morph | median | 90th percentile | maximum |
|---|---|---|---|
| False | 3398 km | 6627 km | 9106 km |
| True | 2113 km | 4152 km | 8108 km |

At `morph=False` the tile nearest Jamaica carries **Senegal**; the tile nearest Puerto Rico
carries **Mali**; the tile nearest Cyprus carries **India**. Denmark's tile sits in northern
Canada. This is not a small fidelity loss, it is a scrambled map, and it is why the
"which region owns the cell an island needs" question below is currently arbitrary.

It connects directly to `interior_bonus`, whose default was recently raised to 2.0: the
higher that value, the wider the range over which distance stops mattering. Nothing here
argues for reverting it — the diagnosis is the normalisation, not the bonus.

## Fixes

Four separate PRs so each can be reviewed and reverted alone.

**Contiguity pre-check** (`perf/contiguity-path-reachability-precheck`, #44). A node-level
BFS in front of the path enumeration. A shortest walk is a simple path, so "no destination
reachable within `max_len` nodes" is exactly when the enumeration yields nothing — the
early return is equivalent by construction. The repair call goes from 30.5 s to 0.23 s with
an array-identical permutation; end-to-end 1.0x to 2.7x depending on how much of a run the
repair was consuming. Bit-identical on world, districts and states at both morph settings.

**Disjoint component pools** (`fix/mosaic-component-pool-overlap`, #46). Rings are grown
from all components at once, so every tile is owned by exactly one component: core tiles by
the existing partition, ring tiles by whichever component reaches them in the fewest lattice
steps. Pools are disjoint by construction, the write-back cannot conflict, and the outcome
no longer depends on component enumeration order — which is what made this latent. A guard
at the write would have stopped the corruption while leaving all three of those problems in
place. Recovers exactly the six mechanism-2 victims at world 384 / 460 `morph=True`, and
India, China, Vietnam, Bangladesh, Ukraine and Hungary at 800 / 848 `morph=False`.
Bit-identical on states, districts and world-mainland-only, which have nothing to
disentangle.

**`min_one_tile_per_region` plus an always-on warning**
(`feat/mosaic-min-one-tile`, #47). The warning fires whenever any region ends up with no
tile, whether or not the option is set, names the regions and gives the remedies. The
option gives a short component the cells overlapping it most, taken from outside the
calibrated core or from a component holding more than it needs, so no other region is left
short. Off by default: a region below one tile's worth of area is drawn at a full tile
either way, which overstates it against everything else on the map. With it on, all four
world configurations place every requested tile; it is byte-identical on every input that
had nothing missing to begin with.

**Honest defaults** (`refactor/mosaic-honest-hungarian-defaults`, #48).
`max_connectivity_iters` 15 → 5 (the most passes ever run is four) and
`disconnected_penalty_mult` → `penalize_disconnected: bool` (every value from 1.0 to 50.0
is indistinguishable; only zero differs). Both verified bit-identical over 40 Hungarian
solves using the same-process technique from `mosaic-inert-verify`, which is the only way
to see past the `morph=True` run-to-run noise.

## Feasibility of the one-tile guarantee, in full

The question was whether it is always achievable and what it costs.

*Is the best cell free?* Not generally. At world 384 / 460 `morph=True` both missing
regions' best-overlapping cells are already core tiles of another component — Bahamas' best
cell belongs to Cuba's component, Trinidad's to a cell the solver gave Senegal. At
`morph=False`, 6 of 13 best cells are free and 7 are taken. So a naive "give it its best
cell" would take a tile from somebody.

*What it costs the region that gives one up:* nothing, as implemented. Cells are only taken
from a component whose pool holds **more** tiles than its regions request, so the surplus
absorbs the loss and no region's count changes. Across all four world configurations,
requested and placed totals match exactly with the option on.

*Is it always achievable?* Practically yes, and the failure mode is geometric rather than
combinatorial. Two regions on one sub-tile land mass (Cyprus and N. Cyprus, which share a
component) simply need two cells, and the search widens until it finds them. What cannot be
guaranteed is that the cell is *near* the region: in a crowded archipelago the nearest
available cell may be a sea cell some distance away. The honest statement is that the
option guarantees a symbol, not a well-placed one — and on world at `morph=False` that
caveat is currently swamped by the `_build_cost_matrix` displacement above.

*Interaction with component splitting:* total. The guarantee has to run as a pool-seeding
step before the empty-pool skip, and a seeded cell has to be excluded from every other
component's pool — which is only meaningful once pools are disjoint. That is why #47 is
stacked on #46.

*Interaction with calibration:* it breaks the `len(core_set) == target_count` invariant.
Seeded cells sit outside the calibrated core, so the mosaic holds more tiles than the core
does. That is visible as a symbol protruding into the sea, which is the correct appearance
for a country that is genuinely there.

## Scripts

`wi_inputs.py` (the three inputs), `diagnose.py` and `trace_loss.py` (stage-by-stage tile
loss), `run_all.py` (diag / metrics / knob sweeps, JSONL written incrementally),
`capture_repair.py` and `analyze_repair.py` (the contiguity instrumentation),
`repair_probe.py` (instrumented and pre-checked copies of `repair_contiguity`),
`taskc_probe.py` (one-tile feasibility), `verify_identical.py`, `time_it.py`,
`pr4_same_proc.py`, `figures.py`, `pr2_figures.py`, `pr3_figures.py`.

Raw records: `results.jsonl`, `repair_analysis.jsonl`, `taskc_probe.jsonl`, `timing_*.json`,
`verify_*.json`.
