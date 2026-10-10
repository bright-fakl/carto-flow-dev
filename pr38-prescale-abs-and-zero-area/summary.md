---
pr: 38
title: Fix pre-scale sign handling, zero-area collapse, and the zero-tile-count mosaic crash
description: Pre-scaling used raw signed data values (a component like [5, -5] summed to zero and was silently skipped); prescale_connected_components now handles all five current/target-area cases explicitly, including an exact zero-area collapse for genuinely zero-data components and a guard against ZeroDivisionError for all-zero datasets. Also fixes a MosaicLayout crash on an isolated zero-tile-count geometry (morph=False), and replaces shapely's internal error with an actionable message for Point-geometry input.
url: https://github.com/bright-fakl/carto-flow/pull/38
branch: fix/prescale-abs-and-zero-area
base: main
date: 2026-09-21
before: origin/main @ af417b6
after: fix/prescale-abs-and-zero-area @ 709b8f8
inputs: synthetic 3-4 cell grids (unit squares), a genuinely isolated zero-value/zero-tile-count "island" geometry, and small mixed-sign/net-negative/all-zero value arrays
kind: pr
topic: flow
---

figure: collapse_before_after.png — A 3-cell mainland (pop 4, 5, 3) plus an isolated zero-population island (g3), size="pop", pre_scale toggled. Before: all 4 geometries keep their original unit-square area (total 4.0000). After: the mainland grows to fill the island's freed share while g3 collapses to an exact zero-area Polygon (is_valid == False, not shown as a filled shape since it has no area) — the total area is preserved exactly (4.0000 both sides).
figure: mixed_sign_area.png — Three 2-geometry components run through prescale_connected_components with abs(values). Mixed-sign [5, -5] (naive signed sum 0) and net-negative [-10, 4] (naive signed sum -6) both keep their full area after prescaling — abs() treats them as real, nonzero data (5+5=10 and 10+4=14 respectively), not as zero data. All-zero [0, 0] correctly collapses to zero area — that is the only case with no data to preserve.
figure: mosaic_zero_tile_fix.png — A 4-cell mainland (tile counts 4, 5, 3, 6) plus an isolated geometry with tile_count=0 (its own geographic component, no neighbours), run through MosaicLayout(morph=False). Before this fix that raised ValueError: zero-size array to reduction operation maximum which has no identity (the isolated component's Hungarian cost matrix had zero rows since it needed zero tile slots). After: the mosaic assignment succeeds, the isolated island correctly gets 0 tiles (shown as an empty box, top right), and the mainland's 18 tiles are assigned normally.
