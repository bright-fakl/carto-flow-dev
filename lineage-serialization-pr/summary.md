---
pr: 183
url: https://github.com/bright-fakl/carto-flow/pull/183
issue: 182
title: save_cartogram stores the vertex lineage
description: Cartogram.save writes the vertex lineage of validity="repair-crossings" and "repair-quadtree" runs and Cartogram.load restores it, so a loaded cartogram lifts the input to its vertex set and takes part in align_vertices. Files without a lineage load as before. No figures; the change is a file format.
kind: pr
topic: flow
base: main
branch: feat/lineage-serialization
related: validated-windows-pr, quadtree-windows-pr
date: 2026-10-26 16:00
before: main @ 4271a3b
after: feat/lineage-serialization @ 48134f1
inputs: the squeezed-strip scenes of the test suite (validity="repair-crossings" and "repair-quadtree").
---

## Behavior

- `VertexLineage.to_dict()` / `VertexLineage.from_dict()`: a versioned dictionary (`version: 1`) of the rounds. An insertion round stores the new indices, the left parents, the fraction and the iteration. A removal round stores the indices that it removes, which are few, instead of the ones it keeps. An unknown version raises `ValueError`.
- `save_cartogram` adds the key `vertex_lineage` when the cartogram has one; `load_cartogram` restores it when the key is present. A file without the key loads with `vertex_lineage = None`.
- A file holds the best iterate and the source geometries only. A loaded cartogram therefore lifts the stored input to its vertex set (`lift_coordinates`) and aligns with other cartograms (`align_vertices`); it has no other snapshots to lift.

## Tests

Round trip of a lineage with insertion rounds, removal rounds and a scalar and an array fraction; a loaded cartogram of each method lifts the input to the same coordinates as the original; two loaded cartograms align to the same vertex counts as the originals; a file without a lineage; an unknown version.
