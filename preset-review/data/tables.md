## The presets before and after

| input | preset | before (n_iter as listed) | after |
|---|---|---|---|
| states | fast | completed, 30 it, cost 57, 0.12 s; true mean 42.24 / max 395.2 %; invalid 0 | converged, 43 it, cost 88, 0.13 s; true mean 3.15 / max 10.6 %; invalid 0 |
| states | balanced | completed, 100 it, cost 220, 0.20 s; true mean 13.14 / max 133.8 %; invalid 0 | converged, 112 it, cost 256, 0.25 s; true mean 0.20 / max 0.8 %; invalid 0 |
| states | high_quality | completed, 300 it, cost 1020, 0.74 s; true mean 49.11 / max 447.3 %; invalid 0 | converged, 425 it, cost 1457, 0.95 s; true mean 0.09 / max 0.6 %; invalid 0 |
| states | default | converged, 112 it, cost 256, 0.23 s; true mean 0.20 / max 0.8 %; invalid 0 | converged, 112 it, cost 256, 0.22 s; true mean 0.20 / max 0.8 %; invalid 0 |
| districts | fast | completed, 30 it, cost 84, 0.23 s; true mean 64.26 / max 825.6 %; invalid 2 | converged, 79 it, cost 295, 0.39 s; true mean 3.34 / max 21.6 %; invalid 32 |
| districts | balanced | completed, 100 it, cost 310, 0.42 s; true mean 37.37 / max 509.2 %; invalid 3 | converged, 145 it, cost 460, 0.58 s; true mean 1.42 / max 9.8 %; invalid 12 |
| districts | high_quality | completed, 300 it, cost 990, 1.27 s; true mean 47.77 / max 714.0 %; invalid 4 | converged, 519 it, cost 1738, 2.22 s; true mean 0.08 / max 0.9 %; invalid 11 |
| districts | default | converged, 145 it, cost 460, 0.52 s; true mean 1.42 / max 9.8 %; invalid 12 | converged, 145 it, cost 460, 0.55 s; true mean 1.42 / max 9.8 %; invalid 12 |
| counties | fast | completed, 30 it, cost 93, 0.68 s; true mean 482.90 / max 29597.1 %; invalid 2 | stalled, 120 it, cost 372, 1.42 s; true mean 105.89 / max 12048.7 %; invalid 18 |
| counties | balanced | completed, 100 it, cost 575, 1.34 s; true mean 292.88 / max 18100.9 %; invalid 4 | stalled, 210 it, cost 1208, 2.33 s; true mean 66.68 / max 5738.0 %; invalid 7 |
| counties | high_quality | stalled, 50 it, cost 192, 0.92 s; true mean 855.61 / max 49485.2 %; invalid 0 | stalled, 50 it, cost 192, 0.98 s; true mean 855.61 / max 49485.2 %; invalid 0 |
| counties | default | stalled, 210 it, cost 1208, 2.36 s; true mean 66.68 / max 5738.0 %; invalid 7 | stalled, 210 it, cost 1208, 2.34 s; true mean 66.68 / max 5738.0 %; invalid 7 |

## Grid, dt and tolerance sets (n_iter 500; iterations / cost / invalid output regions)

**states**

| grid | dt | loose 15/25 % | default 5/10 % | tight 1/3 % |
|---|---|---|---|---|
| 128 | 0.2 | 61 / 124 / 0 | 62 / 125 / 0 | 66 / 138 / 0 |
| 128 | 0.3 | 43 / 88 / 0 | 47 / 101 / 0 | 50 / 113 / 0 |
| 128 | 0.4 | 35 / 80 / 0 | 36 / 81 / 0 | 45 / 108 / 0 |
| 256 | 0.2 | 110 / 242 / 0 | 112 / 256 / 0 | 112 / 256 / 0 |
| 256 | 0.3 | 75 / 171 / 0 | 76 / 172 / 0 | 78 / 186 / 0 |
| 256 | 0.4 | 59 / 131 / 0 | 62 / 146 / 0 | 64 / 160 / 0 |
| 512 | 0.2 | 212 / 740 / 0 | 214 / 742 / 0 | 216 / 744 / 0 |
| 512 | 0.3 | 143 / 503 / 0 | 145 / 505 / 0 | 148 / 532 / 0 |
| 512 | 0.4 | 110 / 374 / 0 | 111 / 399 / 0 | 112 / 400 / 0 |

**districts**

| grid | dt | loose 15/25 % | default 5/10 % | tight 1/3 % |
|---|---|---|---|---|
| 128 | 0.2 | 108 / 360 / 20 | 118 / 424 / 23 | 133 / 547 / 26 |
| 128 | 0.3 | 79 / 295 / 32 | 92 / 398 / 38 | 111 / 561 / 33 |
| 128 | 0.4 | 71 / 305 / 28 | 99 / 567 / 28 | 113 / 671 / 27 |
| 256 | 0.2 | 143 / 458 / 12 | 145 / 460 / 12 | 152 / 509 / 12 |
| 256 | 0.3 | 101 / 353 / 18 | 104 / 377 / 19 | 107 / 401 / 19 |
| 256 | 0.4 | 77 / 308 / 19 | 81 / 354 / 19 | 84 / 378 / 19 |
| 512 | 0.2 | 261 / 882 / 16 | 264 / 885 / 18 | 268 / 912 / 20 |
| 512 | 0.3 | 180 / 594 / 19 | 182 / 619 / 21 | 230 / 1702 / 21 (stalled) |
| 512 | 0.4 | 139 / 484 / 21 | 190 / 1317 / 22 (stalled) | 190 / 1317 / 22 (stalled) |

## dt for the high-quality preset (grid 512, n_iter 1000)

| input | dt | tolerances | iterations | cost | true mean / max % | invalid regions |
|---|---|---|---|---|---|---|
| states | 0.1 | 1/3 % | 425 (converged) | 1457 | 0.09 / 0.6 | 0 |
| states | 0.1 | 0.5/1 % | 425 (converged) | 1457 | 0.09 / 0.6 | 0 |
| states | 0.15 | 1/3 % | 285 (converged) | 981 | 0.15 / 1.1 | 0 |
| states | 0.15 | 0.5/1 % | 289 (converged) | 1033 | 0.13 / 0.9 | 0 |
| states | 0.2 | 1/3 % | 216 (converged) | 744 | 0.49 / 2.8 | 0 |
| states | 0.2 | 0.5/1 % | 219 (converged) | 771 | 0.11 / 0.7 | 0 |
| districts | 0.1 | 1/3 % | 519 (converged) | 1738 | 0.08 / 0.9 | 11 |
| districts | 0.1 | 0.5/1 % | 519 (converged) | 1738 | 0.08 / 0.9 | 11 |
| districts | 0.15 | 1/3 % | 352 (converged) | 1180 | 0.22 / 1.9 | 15 |
| districts | 0.15 | 0.5/1 % | 355 (converged) | 1206 | 0.06 / 0.7 | 15 |
| districts | 0.2 | 1/3 % | 268 (converged) | 912 | 0.17 / 1.8 | 20 |
| districts | 0.2 | 0.5/1 % | 310 (stalled) | 1828 | 0.05 / 1.5 | 19 |
