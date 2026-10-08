---
pr: 46
title: Keep mosaic component tile pools disjoint
description: An island component's extra tile rings reached across water into a mainland component's core tiles, and the last component solved silently overwrote the other's symbols; six regions at world 384/460 lose tiles to this.
url: https://github.com/bright-fakl/carto-flow/pull/46
branch: fix/mosaic-component-pool-overlap
base: main
date: 2026-09-23
before: origin/main @ 8b197eb
after: fix/mosaic-component-pool-overlap @ bd2e76e
inputs: world countries (Natural Earth, Mollweide ESRI:54009) at 384 nominal / 460 actual and 800 nominal / 848 actual tiles, africa, world mainland only, US states, congressional districts grouped by State Name
---

figure: m2_world_b384_morph1.png — world, 384 nominal / 460 actual tiles, morph=True. Before above, after below. Red regions receive no symbol, amber ones are short, both labelled got/wanted.
figure: m2_world_b384_morph0.png — the same input at morph=False.
figure: m2_world_b800_morph1.png — world, 800 nominal / 848 actual tiles, morph=True.

Tile budgets are written `nominal / actual`. The fixture builds counts with
`max(1, round(pop / pop.sum() * budget))`, and because 140 of 176 countries hold less than
half a tile's worth of population the floor raises the requested total well above the
nominal figure: nominal 384 requests 460 tiles, nominal 800 requests 848.

## The bug

Every core tile is assigned to exactly one geographic component. The `extra_tile_rings`
expansion then grew each component's pool **independently**, from its own core set, so a
component separated from another by less than `extra_tile_rings` tile widths — an island
off a coast — reached across the water and took the mainland's **core** tiles into its own
pool. Both components solved over those tiles and both placed a symbol on them, and the
per-component write-back assigns unconditionally:

```python
for t in pool_c:
    local_g = int(assignment_c[t])
    if local_g >= 0:
        assignment[t] = int(geom_indices_arr[local_g])
```

so whichever component happened to be enumerated last silently overwrote the other's tile.
Each tile lost that way is a region left short of its requested count, with no error and no
warning, and which region loses depends on component enumeration order.

All eight overwrites at world 384 / 460, morph=True:

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

The islands are not the regions that lose tiles. They are the ones taking them.

## The fix

Grow the rings from all components at once rather than component by component. A tile is
owned by exactly one component throughout: core tiles by the existing partition, ring tiles
by the component that reaches them in the fewest lattice steps, ties going to the component
whose union centroid is nearest — the rule the partition already uses for a tile that
touches no component at all.

Pools are then disjoint by construction, the write-back cannot conflict, and the result no
longer depends on component order. A first-come-first-served guard at the write would have
stopped the corruption too, but it would have left the pools overlapping, left one
component's solver optimising over tiles it is not allowed to have, and left the outcome
dependent on enumeration order — which is what made this latent in the first place.

## Six regions recovered

At world 384 / 460, morph=True the six regions that regain their tiles are exactly the six
victims in the table above:

**Timor-Leste, North Korea, South Korea, Bhutan, Germany, Belgium.**

Short falls 8 → 2. The two that remain, Bahamas and Trinidad and Tobago, fail for an
unrelated reason: their component wins no core tile at all because their area never reaches
`min_overlap_frac` of any tile (best overlap 0.034 and 0.009), so the pool is empty and the
component is skipped. That is handled separately in #47.

At world 800 / 848, morph=False the regions recovered are **India, China, Vietnam,
Bangladesh, Ukraine and Hungary** — mainland countries, not islands.

## Before and after, all inputs

| input | regions short | zero tiles | non-contiguous | split groups | unassigned core | enclosed holes | seconds | result changed |
|---|---|---|---|---|---|---|---|---|
| world 384 / 460, morph=True | **8 → 2** | 6 → 2 | 1 → 2 | 0 → 0 | 25 → 28 | 4 → 1 | 3.7 → 4.7 | yes |
| world 384 / 460, morph=False | **18 → 13** | 14 → 13 | 3 → 3 | 0 → 0 | 55 → 41 | 1 → 0 | 14.2 → 6.8 | yes |
| world 800 / 848, morph=True | **6 → 3** | 3 → 3 | 6 → 3 | 0 → 0 | 32 → 41 | 6 → 7 | **46.7 → 11.6** | yes |
| world 800 / 848, morph=False | **17 → 11** | 12 → 11 | 4 → 3 | 0 → 0 | 81 → 68 | 0 → 0 | 19.7 → 13.1 | yes |
| africa 150 / 159 and 300 / 306, both morph settings | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 | 5-8 → 5-9 | 0 → 0 | unchanged | yes |
| world mainland only, both morph settings | 0 → 0 | 0 → 0 | unchanged | 0 → 0 | unchanged | unchanged | unchanged | **no** |
| US states, both morph settings | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 | unchanged | 0 → 0 | unchanged | **no** |
| congressional districts, both morph settings | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 | unchanged | 0 → 0 | unchanged | **no** |

### Bit-identical inputs

**US states, congressional districts and world-mainland-only are byte-identical before and
after**, at both morph settings — same per-region tile centroids, same tile size. They have
a single geographic component, or none close enough to contend, so there is nothing to make
disjoint. Africa's fingerprint moves because Madagascar is a second component; its integrity
metrics are unchanged and only the count of empty core tiles shifts by one or two either way.

### Integrity

No split groups anywhere, before or after. Non-contiguous regions improve on three of the
four world configurations and regress by one on world 384 / 460 morph=True. Empty core
tiles move in both directions: they rise where the fix returns a tile to a mainland region
that then sits closer to its own land, and fall where an island stops borrowing mainland
tiles.

### Runtime

Falls substantially on world — 46.7 s → 11.6 s at 800 / 848 morph=True — because fewer
regions end up split across the sea, which is what the contiguity repair spends its time on.

## Verification

`make check` clean, full suite 632 passed. Raw records and the scripts behind these numbers
are in `visual_checks/mosaic-world-islands/` (`results.jsonl`, `run_all.py`,
`trace_loss.py`, `pr2_figures.py`).
