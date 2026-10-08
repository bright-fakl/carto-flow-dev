---
pr: 52
title: Two gallery examples for the mosaic layout
description: MosaicLayout had no gallery example at all; these two show the basic tilegram and group_by block contiguity.
url: https://github.com/bright-fakl/carto-flow/pull/52
branch: docs/mosaic-gallery-examples
base: main
date: 2026-09-23 15:46
before: origin/main @ 58f3cc2 (no mosaic example in the gallery at all)
after: docs/mosaic-gallery-examples @ 2a7e10b
inputs: US states (bundled census, population/2e6 tile counts), US congressional districts (bundled census, one tile each, grouped by State Name)
---

figure: mosaic_layout.png — basic tilegram: US states, one hexagon per two million people, colored by census region
figure: mosaic_groups.png — group_by: one hexagon per congressional district, each state's districts kept as one connected block

## What was added

Two examples under `docs/examples/symbol_cartogram/`, all on bundled data:

| file | what it teaches | runtime (gallery build) |
|---|---|---|
| `plot_symbol_mosaic_layout.py` | `tile_count`, the basic tilegram | 1.6 s |
| `plot_symbol_mosaic_groups.py` | `group_by`, block contiguity | 4.5 s |

No gallery registration was needed: the `gallery` plugin picks up everything
under `docs/examples/` and orders it by filename, so the two land next to the
other symbol-cartogram examples.

## What the figures show

**`mosaic_layout.png`** — the outline of the country is clearly readable: the
West is a wide orange block dominated by California, the Northeast is a dense
red cluster, Texas and Florida keep their shapes. Population, not area, drives
the block sizes, so Montana, Wyoming and the Dakotas shrink to one hexagon each
while California takes about twenty.

**`mosaic_groups.png`** — 432 districts, one hexagon each, grouped by state.
The run reports every region at its exact tile count, no non-contiguous region
and no split group. Two things in the picture are worth naming rather than
glossing over, and the example's prose names both:

- Several lattice cells inside the outline are left empty and read as small
  holes (the run leaves ten), with the same number of tiles pulled from just
  outside the outline instead.
- A few tiles look detached — Michigan's northern one is the clearest — but are
  lattice neighbors; the apparent gap is only the drawn `spacing`. This was
  checked against the metrics rather than assumed.

## Considered and not added

- **A `morph=False` vs `morph=True` contrast.** Written, rendered and then
  dropped: the user judged it not helpful enough to carry. The two panels
  differ in ways that are hard to attribute without already knowing the
  algorithm, and the `morph=False` panel raises questions the gallery is the
  wrong place to answer — Maryland lands among New York and Pennsylvania,
  losing contact with the four states it borders, which is an open question
  about the cost function rather than a lesson about the option.
- **`min_one_tile_per_region` on world countries.** A genuine capability, but the
  input it needs is the one where the layout is roughest, and a world run is
  much slower than a US one. Poor fit for a first impression of the layout in a
  CI-built gallery.
- **A square-tiling variant.** It is a one-word change to an example already
  present and teaches nothing the hexagon version does not.
- **Mosaic versus grid side by side.** The grid layout rejects `group_by`
  outright, so the two cannot be shown on the same input in one figure.

## Checks

- `uv run mkdocs build -s` completes after removing `docs/generated/`: 611 s,
  exit 0, both examples executed (verified in `mg_execution_times.md`).
- `make check` clean; 712 tests pass.
- Every figure above was rendered by the gallery build itself and inspected.
