---
pr: 47
title: Warn about unplaced mosaic regions, add min_one_tile_per_region
description: Regions on a land mass smaller than one tile get no symbol and vanish silently; this reports them by name and adds an off-by-default option that places them without costing any other region a tile.
url: https://github.com/bright-fakl/carto-flow/pull/47
branch: feat/mosaic-min-one-tile
base: fix/mosaic-component-pool-overlap
date: 2026-09-23
before: fix/mosaic-component-pool-overlap @ bd2e76e (this PR's own parent, so the numbers isolate this change)
after: feat/mosaic-min-one-tile @ e5343e4
inputs: world countries (Natural Earth, Mollweide ESRI:54009) at 384 nominal / 460 actual and 800 nominal / 848 actual tiles, africa, world mainland only, US states, congressional districts grouped by State Name
kind: pr
topic: symbol
---

figure: m1_world_b384_morph1.png — world, 384 nominal / 460 actual tiles, morph=True. min_one_tile_per_region=False (the default) above, True below. Regions with no symbol are red.
figure: m1_world_b384_morph0.png — the same input at morph=False, where thirteen regions go missing by default.

**Stacked on #46.** Review that first; this branch contains it, and the before column
below is #46's output, not main's.

## The problem

A region only draws tiles from the pool of its own geographic component. A component whose
every covering lattice cell falls below `min_overlap_frac` — a land mass smaller than about
a tenth of a tile — wins no tile at all, so its pool is empty, the Hungarian solve is
skipped, and its regions get no symbol. They simply do not appear on the map, and nothing
is said about it.

At world 384 nominal / 460 actual with morph=True that is the **Bahamas** (best overlap
0.034 of a tile) and **Trinidad and Tobago** (0.009). At morph=False it is thirteen regions:
Fiji, Bahamas, Falkland Is., Fr. S. Antarctic Lands, Puerto Rico, Jamaica, Vanuatu, New
Caledonia, Solomon Is., Taiwan, N. Cyprus, Cyprus and Trinidad and Tobago.

The tile *count* already asks for these regions: a caller building `tile_count` with
`max(1, round(...))` has requested one tile each. The layout fails to place them.

## What changes

**A warning, always.** Whenever any region ends up with no tile the layout warns, names the
regions (up to ten, then a count) and gives the concrete ways out. It fires whether or not
the option is set — with the option set it drops the option from the list of remedies.

```
2 region(s) received no tile and are missing from the mosaic: Bahamas, Trinidad
and Tobago. Each sits on a land mass no tile overlaps by min_overlap_frac, so its
geographic component has no tiles to assign. To place them, set
min_one_tile_per_region=True to place them on the nearest free cells, raise the
tile budget so each of them covers more of a tile, or lower min_overlap_frac.
```

**`min_one_tile_per_region: bool = False`**, a new `MosaicLayoutOptions` field. A component
short of tiles is given the cells that overlap it most, enough to cover its requested count.
Cells come from outside the calibrated core, or from a component whose pool holds more tiles
than it needs — never one that would leave another region short. The search widens in three
steps until enough cells are available, so a component in a crowded archipelago still finds
them.

**Off by default.** A region below one tile's worth of area is drawn at a full tile either
way, which overstates it against every other region on the map. Whether that trade is right
depends on what the map is for, so it is the caller's decision, not a silent default. The
option also means the mosaic holds more tiles than the calibrated core does, since the
seeded cells sit outside it.

## The naive guarantee is NOT free — corrected finding

An earlier reading of this problem was that the guarantee costs nothing, because the
shortfall is per-component pool emptiness rather than a global tile shortage. **That was
wrong, and the probe that settled it is worth stating.**

For every region with no symbol, the cell overlapping its geometry most was located and
checked against the final assignment:

| input | regions with no symbol | best-overlapping cell free | best-overlapping cell already owned |
|---|---|---|---|
| world 384 / 460, morph=True | 2 | 0 | **2** |
| world 384 / 460, morph=False | 13 | 6 | **7** |

So a first draft that only ever took *unclaimed* cells still left Jamaica, N. Cyprus and
Cyprus unplaced at morph=False: every cell near them already belonged to another component.
The shipped version additionally draws on components whose pool holds **more** tiles than
their regions request, so the surplus absorbs the loss and nobody's count changes. Across
all four world configurations, requested and placed totals then match exactly.

Two further points the probe settled:

* **Always achievable?** Practically yes, and the failure mode is geometric rather than
  combinatorial. Two regions on one sub-tile land mass — N. Cyprus and Cyprus share a
  component — simply need two cells, and the search widens until it finds them. What cannot
  be guaranteed is that the cell is *near* the region: in a crowded archipelago the nearest
  available cell may be a sea cell some distance away. The option guarantees a symbol, not a
  well-placed one.
* **Interaction with component splitting: total.** The guarantee has to run as a
  pool-seeding step before the empty-pool skip, and a seeded cell has to be excluded from
  every other component's pool — which is only meaningful once pools are disjoint. That is
  why this PR is stacked on #46.
* **Interaction with calibration:** it breaks the `len(core_set) == target_count` invariant.
  Seeded cells sit outside the calibrated core, so the mosaic holds more tiles than the core
  does. That shows up as a symbol protruding into the sea, which is the correct appearance
  for a country that is genuinely there.

## Effect

| input | off: short / zero | on: short / zero | off: non-contiguous | on: non-contiguous | option changes the result |
|---|---|---|---|---|---|
| world 384 / 460, morph=True | 2 / 2 | **0 / 0** | 2 | 2 | yes |
| world 384 / 460, morph=False | 13 / 13 | **0 / 0** | 3 | 1 | yes |
| world 800 / 848, morph=True | 3 / 3 | **0 / 0** | 3 | 3 | yes |
| world 800 / 848, morph=False | 11 / 11 | **0 / 0** | 3 | 4 | yes |
| africa 150 / 159, both morph settings | 0 / 0 | 0 / 0 | 0 | 0 | **no — bit-identical** |
| world mainland only 384 / 446, both morph settings | 0 / 0 | 0 / 0 | 1 / 5 | 1 / 5 | **no — bit-identical** |
| US states, both morph settings | 0 / 0 | 0 / 0 | 0 | 0 | **no — bit-identical** |
| congressional districts, both morph settings | 0 / 0 | 0 / 0 | 0 | 0 | **no — bit-identical** |

Every region is placed on all four world configurations and no region gives up a tile. The
option is **inert** — byte-identical placement and tile size — on every input that had no
unplaced region to begin with, which is what default-off should mean in practice. Split
groups are zero throughout. Runtime is unchanged within noise everywhere.

## Verification

`make check` clean, full suite 635 passed, including three new tests: the warning fires and
names the region; the option places it without any other region losing a tile; the option is
inert when every region already has tiles.

## One thing the figures show that this PR does not fix

At morph=False on world the mosaic places symbols very far from their regions — the tile
nearest Jamaica carries Senegal, the tile nearest Cyprus carries India, median displacement
3398 km. That is a separate problem in `_build_cost_matrix` and is out of scope here. It is
written up in `visual_checks/mosaic-world-islands/summary.md` and evaluated in
`visual_checks/mosaic-distance-normalisation/`.
