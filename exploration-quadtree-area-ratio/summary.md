---
issue: 179
title: The area ratio of the quadtree rebuild rule
description: validity="repair-quadtree" rebuilds its mesh when a triangle falls below a fraction (area_ratio, 0.001) of its area at construction. Over 36 runs with ratios from 0.001 to 0.2 on counties, districts and raw coarse counties, at dt 0.2 to 0.4, every run has 0 invalid polygons and no inversion left. The ratio changes the number of rebuilds only from 10 to 18 on the counties, and the differences in time, vertices and error between ratios come from where the ladder stalls, not from the ratio itself, so there is no evidence for a cost advantage of 0.001 over values up to 0.03.
kind: exploration
topic: flow
status: open
related: quadtree-windows-pr, exploration-adaptive-windows
date: 2026-10-25 18:00
before: feat/quadtree-windows @ 233ad80
after: the same branch; script only
inputs: counties (1 km input), congressional districts (1 km) and raw coarse counties (43,084 vertices), morph_multiresolution with auto ladder, area_scale 1e-6, n_iter 1000, dt as stated, validity="repair-quadtree", QuadtreeSettings(area_ratio=...) swept. One run per row (a second run of the counties at dt 0.2 reproduced every row exactly). The errors are of the valid polygons against targets normalized on the valid polygons.
---

`sweep.py INPUT DT [REPEAT]` runs the six ratios on one input; `results.jsonl` holds all 36 runs. The mesh is rebuilt when the area of a triangle falls below the ratio times its area at construction, at the start of each ladder level, and at the next window after an inversion fix.

## Results

Counties, dt 0.2:

| area ratio | time | iterations | rebuilds | inversion fixes | limiter runs | vertices | mean / median error (%) | above 10 % | invalid |
|---|---|---|---|---|---|---|---|---|---|
| 0.001 | 38.9 s | 1000 | 10 | 57 | 0 | 1,267,995 | 5.04 / 0.868 | 294 | 0 |
| 0.003 | 67.8 s | 1000 | 12 | 50 | 8 | 1,844,876 | 0.84 / 0.017 | 65 | 0 |
| 0.01 | 53.9 s | 980 | 16 | 42 | 7 | 1,639,879 | 1.9 / 0.133 | 122 | 0 |
| 0.03 | 38.8 s | 1000 | 11 | 29 | 8 | 1,219,805 | 6.68 / 0.453 | 359 | 0 |
| 0.1 | 48.0 s | 1000 | 15 | 7 | 0 | 1,852,998 | 2.22 / 0.157 | 144 | 0 |
| 0.2 | 46.3 s | 910 | 18 | 0 | 0 | 1,898,830 | 2.19 / 0.353 | 110 | 0 |

Counties, dt 0.35:

| area ratio | time | iterations | rebuilds | inversion fixes | limiter runs | vertices | mean / median error (%) | above 10 % | invalid |
|---|---|---|---|---|---|---|---|---|---|
| 0.001 | 42.7 s | 760 | 12 | 45 | 4 | 1,619,276 | 4.46 / 0.45 | 269 | 0 |
| 0.003 | 36.6 s | 760 | 12 | 45 | 4 | 1,619,276 | 4.46 / 0.45 | 269 | 0 |
| 0.01 | 64.0 s | 1000 | 13 | 29 | 2 | 1,843,254 | 1.41 / 0.32 | 69 | 0 |
| 0.03 | 63.6 s | 1000 | 13 | 29 | 2 | 1,843,254 | 1.41 / 0.32 | 69 | 0 |
| 0.1 | 33.0 s | 610 | 15 | 18 | 0 | 1,575,719 | 4.13 / 0.224 | 266 | 0 |
| 0.2 | 68.8 s | 1000 | 25 | 3 | 0 | 2,187,640 | 1.32 / 0.283 | 71 | 0 |

Districts, dt 0.2 and dt 0.4 and raw coarse counties, dt 0.2: every ratio gives 0 invalid polygons, 11 to 19 rebuilds and no unresolved inversion; for ratios up to 0.01 the districts and the raw coarse input give identical results (the area rule never triggers; the rebuilds are the level starts and the inversion fixes).

## Reading

- Validity does not depend on the ratio in this range: 0 invalid polygons and 0 unresolved inversions in all 36 runs, including districts at dt 0.4 and counties at dt 0.35. The kernel fix, the rebuild after a fix and the limiter carry the validity, as they did in the prototype.
- The rebuild count rises with the ratio, but little: 10 at 0.001 to 18 at 0.2 on the counties at dt 0.2, 12 to 25 at dt 0.35. Most rebuilds are not caused by the area rule at small ratios.
- The differences in time, vertices and error between ratios come from the path of the run, not from the cost of the rule: the ladder stalls at different iterations, so runs end at different levels (0.001 ends at 740 and 260 iterations without reaching the finest level and has the lowest vertex count and the highest error; 0.003 reaches the finest level and takes 68 s with 1.84 M vertices and 0.84 % mean error). The time per iteration (39 to 68 ms) follows the share of iterations spent at the finest grid. The earlier comparison of 0.001 with 0.2 (38 to 40 s against 44 to 68 s on the counties) mixes the two effects and is not evidence of a cost advantage.
- So the data do not distinguish values between 0.001 and about 0.03; 0.1 and 0.2 rebuild more often (15 to 25) at no visible gain. Whether a ratio between 0.001 and 0.01 gives more margin against squeezed triangles at larger step sizes than dt 0.4 on the districts is not tested.
