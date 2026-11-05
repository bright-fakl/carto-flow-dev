---
title: One tile layout algorithm for single-tile and grouped regions (design)
description: Design of a shared algorithm for the grid and mosaic layouts: allocation (which tiles are usable) followed by assignment by capacitated optimal transport with a reserve sink, a contiguity-guarded swap search and an optional pre-morph. Prototype results on US states, districts by state, Europe and Africa, the Texas tip, and a nonlinearity of the compactness parameter.
kind: proposal
topic: symbol
project: carto-flow
status: open
related: grid-energy-assignment-pr
date: 2026-11-05 12:00
before: GridBasedLayout (one tile per region, energy descent) and MosaicLayout (tile_count and group_by, morph then Hungarian and repair) are separate algorithms
after: prototype only (scratch scripts, nothing committed)
inputs: US states (49), 432 congressional districts grouped by state, Europe, Africa; hexagon lattice (square for checks); compactness c in {0.25, 1}, 11 values for the linearity test; pre-morph on and off.
---
## Goal

Grid and mosaic differ mainly in interface, not in algorithm: grid is built for one tile per region and no grouping, mosaic for `tile_count` and `group_by`. The generic layout interface offers both for every layout. The aim is one layout that covers both cases, with the guarantees below. Work on PR 207 waits for this decision.

Requirements (from the design notes):
- Grouping and `tile_count` are guarantees on the output: a group never splits, a region receives exactly its tile count.
- Size variable and normalization concern symbol size, not tile size.
- The layout resembles the overall shape, keeps stand-out features recognizable (a tile at the south-east tip is not assigned to a state other than Florida), and resembles location and neighbor relations.
- Islands lie at their geometry or compactly near others, with optional forced spacing. A multi-part geometry with one tile places the tile near the main part.
- Pre-morphing is optional; the algorithm works without it.
- Exact tile count gives shape control but hard assignment; surplus tiles give flexibility but allow holes.

## Pipeline

Two stages that are evaluated and inspectable separately.

1. **Allocation.** Choose the usable tile set. Compactness `c` in 0..1 sets its size to `n + round((1 - c)(m - n))` (n tiles needed, m lattice tiles in the window); `c = 1` is exactly n tiles. The set is built from the silhouette of each land part (already in PR 207).
2. **Assignment.** Capacitated optimal transport on the allocated set: group g has capacity N_g (1 for ungrouped regions), cost is the squared distance from the tile center to the group's geometry plus 0.1 times the squared distance to its centroid. A reserve sink takes the m - n surplus tiles; its per-tile cost is `beta` times the distance to the convex hull boundary of the allowed set (`hull`, beta 1; with 3 neighbor iterations for groups, beta 1 to 2). Solved exactly with the Hungarian algorithm on replicated rows.
3. **Repair.** A swap local search accepts only moves that do not increase the number of extra components (lexicographic: components, then cost), plus chain moves over up to 3 groups.
4. **Pre-morph (optional).** A flow cartogram to equal area before assignment.
5. **Contact descent (open).** The grid energy's contact term reduces false contacts; the OT result has more of them (27 against 16 on states, c 0.25 and 0.5).

The sink is what removes the interior holes that Hungarian assignment and the grid energy leave below c = 1: surplus tiles are paid for at the allowed set's boundary, so they end up there.

## Results

hexagon lattice; disp is displacement in tile steps (mean/max/p95); touch is the share of truly adjacent pairs that touch; false is the number of touching pairs that are not adjacent; split/stray counts groups split and stray tiles; grid is the main-branch layout (districts: the tile_count path of the same layout); off/on is pre-morph. All pre-morphs converged. Runtime excludes the pre-morph (about 1 s Europe, 1.3 s Africa).

| data | c | variant | s | disp | pockets | touch | false | split/stray |
|---|---|---|---|---|---|---|---|---|
| States | .25 | grid | .69 | .63/1.6/1.5 | 3 | .77 | 21 | 0/0 |
| | | off | .04 | .63/1.3/1.2 | 1 | .71 | 35 | 0/0 |
| | | on | .05 | .86/1.7/1.4 | 0 | .76 | 31 | 0/0 |
| | 1 | grid | .60 | 1.48/3.6/2.3 | 0 | .74 | 32 | 0/0 |
| | | off | .02 | 1.49/2.8/2.3 | 0 | .72 | 34 | 0/0 |
| | | on | .02 | .91/2.2/1.7 | 0 | .74 | 35 | 0/0 |
| Districts | .25 | grid | 1.16 | 3.5/10.7/8.2 | 3 | .83 | 114 | 35/94 |
| | | off | .50 | 1.56/3.8/2.4 | 3 | .80 | 21 | 0/0 |
| | | on | .53 | 2.46/4.5/3.9 | 4 | .86 | 22 | 0/0 |
| | 1 | grid | .61 | 6.7/12.4/10.3 | 0 | .86 | 124 | 41/117 |
| | | off | .34 | 4.25/7.5/6.8 | 0 | .82 | 31 | 1/5 |
| | | on | .17 | 2.54/4.6/4.1 | 0 | .84 | 24 | 0/0 |
| Europe | .25 | grid | .20 | .76/2.0/1.3 | 2 | .78 | 10 | 0/0 |
| | | off | .02 | .92/2.0/1.7 | 3 | .66 | 31 | 0/0 |
| | | on | .02 | 1.03/1.8/1.7 | 3 | .63 | 35 | 0/0 |
| | 1 | grid | .11 | 1.19/7.8/2.1 | 0 | .67 | 27 | 0/0 |
| | | off | .004 | .84/1.6/1.5 | 0 | .52 | 38 | 0/0 |
| | | on | .004 | .83/2.0/1.6 | 0 | .60 | 37 | 0/0 |
| Africa | .25 | grid | .18 | .70/1.9/1.5 | 3 | .76 | 18 | 0/0 |
| | | off | .01 | .58/1.3/1.1 | 0 | .66 | 45 | 0/0 |
| | | on | .01 | .71/1.6/1.4 | 0 | .69 | 43 | 0/0 |
| | 1 | grid | .07 | .85/2.4/1.6 | 0 | .73 | 40 | 0/0 |
| | | off | .005 | .83/2.1/1.6 | 0 | .64 | 50 | 0/0 |
| | | on | .005 | .73/2.0/1.7 | 0 | .65 | 48 | 0/0 |

Findings:
- **Grouped input:** the main-branch layout splits 35 to 41 of 49 groups; the pipeline splits 0 to 1 and halves or better the displacement (district c = 1: 6.7 to 4.25, 2.54 with pre-morph).
- **Ungrouped input** (states, Europe, Africa): displacement is similar to the grid layout; touching is lower (Europe c = 1: .52 to .60 against .67; Africa .64 to .65 against .73) and false contacts are higher. The grid layout's contact term is worth keeping as a descent layer.
- **Pre-morph** helps the hard cases (states and districts at c = 1: displacement .91 and 2.54 against 1.49 and 4.25) and is neutral or slightly worse for Europe, Africa and for c = .25. It should be an option, not a default.
- **Runtime:** OT is 0.005 to 1 s here (exact solver, dense); counties scale is untested (the dense assignment grows as (n + reserve)^2).

Figures:
- ![States](pipe_states.png)
- ![Districts by state](pipe_districts.png)
- ![Europe](pipe_europe.png)
- ![Africa](pipe_africa.png)

Visible defects: districts c = 1 without pre-morph: Louisiana is pushed into a thin tendril, Florida stretched along the Gulf, western states crowded. Africa: the Maghreb and the west coast shift east (Morocco above Mauritania), Madagascar sits next to Mozambique. Europe: Nordic tiles form a vertical strip at c = 1.

## Compactness is not linear

The allowed-set size is linear in c by construction; the metrics are not (hexagon, no pre-morph, c = 0 to 1 in steps of 0.1):
- States: mean displacement .62 to .71 for c = 0 to .8, then 1.12 at .9 and 1.49 at 1.
- Districts: 1.52 to 1.73 for c = 0 to .7, then 2.12, 2.76, 4.25 at .8, .9, 1.
- States with pre-morph: no knee (.75 to .85, then .91 at 1).
- The knee is where the allowed set shrinks below about 1.2 to 1.4 times n; the displacement rises steeply as the ratio n_allowed/n approaches 1.
- At c in [0, .1] the result is identical on states (the hull sink makes the lowest range redundant); pockets are noisy with no trend.

![Compactness](c_linearity.png)

Suggested parametrization: spread the useful range with a geometric scale, `n_allowed = n (m/n)^(1 - c)`. On states c' = .8 gives ratio 1.24, where linear c = .9 does. Simpler: keep linear c and document c above .8 as the range where shape fidelity trades against displacement.

## Texas tip and feature preservation

- A tile exists at the Texas tip (nearest allowed tile 0.87 steps on states, 1.13 on districts); plain OT gives it to Louisiana because capacities trade tiles globally. The earlier extreme-direction test was ill-posed (the extreme tile in that direction belongs to Florida or Georgia); a nearest-tip test replaces it.
- Pre-morph is the most effective single change (states c = 1: displacement 1.48 to .91; districts: 2 split groups to 0, displacement 4.25 to 2.54).
- Extremes pinning (fixing the tiles at the extreme points of the outline to their regions) is nearly free on hexagon, costs more on square (1.72 against 1.44) and fails Maine and Washington there. Keep it optional; user-supplied landmark lists work the same way.
- Boundary alignment (matching boundary regions to boundary tiles in cyclic order) drops touching from .72 to .51 and splits 14 of 49 groups; dropped. The growth variant (grow regions from OT seeds) leaves 2 to 12 groups split and worse touching; dropped.

![Texas](part_texas_diag.png)
![Sink forms](part_sink_states.png)
![Landmarks](part_landmarks_districts.png)

## Contiguity

Groups split (stray tiles) on districts by state:

| variant | hex c = 1 | hex c = .5 | square c = 1 | square c = .5 |
|---|---|---|---|---|
| OT raw | 5 / 9 | 2 / 2 | 10 / 22 | 6 / 7 |
| + local search | 2 / 6 | 0 / 0 | 2 / 12 | 0 / 0 |
| + chain moves | 1 / 5 | 0 / 0 | 2 / 12 | 0 / 0 |

Contiguity is not guaranteed at exactly n tiles (c = 1): Florida, and Florida with Georgia on squares, remain split. With any slack the search repairs all groups.

## Acceptance tests for a unified layout

1. Zero split groups for `group_by` at c below 1, and at most 1 at c = 1 (documented).
2. Every region receives exactly its tile count.
3. On ungrouped input, mean displacement and touching no worse than the grid layout by more than 0.05 steps and .05 respectively (currently: touching lower on Europe and Africa).
4. Tip tiles (nearest tile to the outline extremes) belong to the owning region on states and districts.
5. Isolated parts (Alaska, Hawaii, Madagascar, Iceland) keep their tiles together and near their geometry in the modes separate, connected and spaced.

## Open items

- Contact descent on top of OT (to recover grid-level false contacts).
- Multi-part geometries: capacity split by part area (France with French Guiana fails now).
- Counties scale: sparse min-cost flow instead of dense Hungarian.
- Exactness at c = 1 (final repair or slack).
- Parametrization of c.
- Fate of PR 207 (silhouette allocation and inspection tool carry over; its energy assignment would be replaced).
- Separate topic: nested group cartogram (groups sized by their total, sub-regions laid out inside, groups separated like explode).

## What was not verified

- Michigan notch feature test; only 6 lattice offsets; square lattice shows the same picture with touching .45 to .55 on ungrouped data.
- Pre-morph left 2 invalid output regions on Europe (not repaired).
- Labels in the new figures are 3-letter truncations and ambiguous for small tiles.
- No test with multi-part groups or with counties.
