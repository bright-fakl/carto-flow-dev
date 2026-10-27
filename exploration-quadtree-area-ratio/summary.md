---
issue: 179
title: The area ratio of the quadtree rebuild rule
description: validity="repair-quadtree" rebuilds its mesh when a triangle falls below a fraction (area_ratio, 0.001) of its area at construction. Over 36 runs with ratios from 0.001 to 0.2 on counties, districts and raw coarse counties, at dt 0.2 to 0.4, every run has 0 invalid polygons and no inversion left. The ratio changes the number of rebuilds only from 10 to 18 on the counties, and the differences in time, vertices and error between ratios come from where the ladder stalls, not from the ratio itself, so there is no evidence for a cost advantage of 0.001 over values up to 0.03.
kind: exploration
topic: flow
status: led-to
related: quadtree-windows-pr, exploration-adaptive-windows
date: 2026-10-25 18:00
before: feat/quadtree-windows @ 233ad80
after: the same branch; script only
inputs: counties (1 km input), congressional districts (1 km) and raw coarse counties (43,084 vertices), morph_multiresolution with auto ladder, area_scale 1e-6, n_iter 1000, dt as stated, validity="repair-quadtree", QuadtreeSettings(area_ratio=...) swept. One run per row (a second run of the counties at dt 0.2 reproduced every row exactly). The errors are of the valid polygons against targets normalized on the valid polygons.
closed: 2026-10-26 02:02
---

**Outcome (2026-10-26).** The area ratio stays 0.001 in `validity="repair-quadtree"` (PR 181, merged); the rule did not trigger in any tested run at 0.001 and below.


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

## Lower ratios, and the rule switched off

The ratio had only been tested from 0.001 upwards, so the sweep was extended downwards: 0.001, 0.0003, 0.0001, 0.00001 and 0 (the area rule never triggers; the rebuilds are the level starts and the inversion fixes), on counties (dt 0.2 and 0.35), districts (dt 0.4 and 0.6) and raw coarse counties (dt 0.2 and 0.35); then 0.001 against 0 at larger step sizes (districts dt 0.8 and 1.0, counties dt 0.6 and 0.8). `sweep.py` now also records the smallest triangle area ratio that the rule saw (`min_area_ratio_seen`, sampled when the rule is evaluated, once per window); `results_low.jsonl` and `results_stress.jsonl` hold the runs (38 in total).

| input | dt | ratios | identical output for all ratios | invalid | unresolved inversions | inversion fixes / limiter runs | rebuilds | smallest area ratio seen |
|---|---|---|---|---|---|---|---|---|
| district | 0.4 | 0.0, 1e-05, 0.0001, 0.0003, 0.001 | yes | 0 | 0 | 47 / 0 | 13 | 5.0e-02 |
| district | 0.6 | 0.0, 1e-05, 0.0001, 0.0003, 0.001 | yes | 0 | 0 | 31 / 2 | 13 | 1.2e-02 |
| coarse | 0.2 | 0.0, 1e-05, 0.0001, 0.0003, 0.001 | yes | 0 | 0 | 46 / 0 | 11 | 8.5e-03 |
| coarse | 0.35 | 0.0, 1e-05, 0.0001, 0.0003, 0.001 | yes | 0 | 0 | 62 / 2 | 14 | 4.6e-03 |
| county | 0.2 | 0.0, 1e-05, 0.0001, 0.0003, 0.001 | yes | 0 | 0 | 56 / 0 | 10 | 1.7e-03 |
| county | 0.35 | 0.0, 1e-05, 0.0001, 0.0003, 0.001 | yes | 0 | 0 | 33 / 2 | 11 | 4.8e-03 |
| district | 0.8 | 0.0, 0.001 | yes | 0 | 0 | 31 / 5 | 12 | 9.3e-02 |
| district | 1.0 | 0.0, 0.001 | yes | 0 | 0 | 22 / 4 | 13 | 4.1e-02 |
| county | 0.6 | 0.0, 0.001 | yes | 0 | 0 | 88 / 14 | 25 | 7.4e-03 |
| county | 0.8 | 0.0, 0.001 | yes | 0 | 0 | 67 / 13 | 18 | 2.2e-02 |

- For every ratio from 0.001 down to 0 the output is identical (same vertices, same error, same rebuilds): the area rule at 0.001 never triggered in any of these runs, and switching it off changes nothing. All runs have 0 invalid polygons and no unresolved inversion.
- The smallest area ratio that any mesh triangle reached before a rebuild was 1.7e-3 on the counties at dt 0.2 (4.8e-3 at dt 0.35, 7.4e-3 at dt 0.6, 2.2e-2 at dt 0.8), 4.6e-3 to 8.5e-3 on the raw coarse counties, 1.2e-2 to 9.3e-2 on the districts. The value 0.001 therefore sits just below the smallest triangle ratio observed on the counties (a factor of 1.7) and well below everything else. The earlier sweep agrees: on the counties the rule starts to act between 0.0017 and 0.003 (0.003 changed the run path).
- So 0.001 is not near a threshold where validity fails: the rule is a backstop that is inactive on these inputs, and the validity comes from the inversion fix, the rebuild after a fix and the limiter. Where the rule becomes active (above about 0.002 on the counties) the runs stay valid as well, only the trajectory changes.
- Not covered: whether a mesh that is kept very long (rule off) on an input whose triangles get squeezed much more than on these (the smallest ratio seen is 1.7e-3) stays valid. The inversion control is what would have to hold; its record in these runs is 0 unresolved inversions in 74 runs.
