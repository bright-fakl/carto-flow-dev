## Fresh runs, default tolerances (5 % / 10 %), wall time is the minimum of two runs

| input | grid | dt | constant dt: status, iterations, recomputes, cost, wall s, true max % | adaptive_dt: same |
|---|---|---|---|---|
| states | 128 | 0.2 | converged, 62, 7, 125, 0.14, 8.87 | converged, 62, 7, 125, 0.15, 8.87 |
| states | 256 | 0.2 | converged, 112, 12, 256, 0.30, 0.78 | converged, 112, 12, 256, 0.22, 0.78 |
| states | 512 | 0.2 | converged, 214, 22, 742, 0.55, 9.22 | converged, 214, 22, 742, 0.56, 9.22 |
| districts | 256 | 0.2 | converged, 145, 15, 460, 0.57, 9.76 | converged, 145, 15, 460, 0.59, 9.76 |
| states | 256 | 0.4 | converged, 62, 7, 146, 0.16, 3.50 | converged, 62, 7, 146, 0.16, 3.50 |
| districts | 256 | 0.4 | converged, 81, 13, 354, 0.43, 4.84 | converged, 80, 12, 332, 0.41, 9.53 |
| horizontal | 256 | 0.2 | converged, 207, 24, 495, 0.36, 8.98 | converged, 207, 24, 495, 0.36, 9.03 |
| horizontal | 256 | 0.6 | converged, 122, 18, 338, 0.27, 8.20 | converged, 127, 18, 343, 0.28, 8.48 |
| tangential | 256 | 0.2 | converged, 187, 20, 427, 0.31, 7.49 | converged, 187, 20, 427, 0.33, 7.49 |
| tangential | 256 | 0.6 | converged, 118, 21, 370, 0.28, 8.63 | converged, 123, 20, 363, 0.29, 9.20 |
| tilted | 256 | 0.2 | converged, 162, 17, 366, 0.29, 7.75 | converged, 162, 17, 366, 0.30, 7.75 |
| tilted | 256 | 0.6 | converged, 95, 15, 275, 0.24, 8.52 | converged, 98, 15, 278, 0.25, 9.17 |

## Tight tolerances (mean / max)

| input | grid | tolerances % | dt | recompute_on_rise | constant dt: status, it, cost | adaptive_dt: status, it, cost | true max %: constant / adaptive |
|---|---|---|---|---|---|---|---|
| states | 128 | 0.2 / 0.4 | 0.2 | 0.01 | completed, 400, 1975 | converged, 73, 163 | 0.46 / 0.31 |
| states | 128 | 0.2 / 0.4 | 0.2 | None | stalled, 270, 513 | converged, 182, 353 | 1.12 / 0.35 |
| states | 128 | 0.2 / 0.4 | 0.4 | 0.01 | stalled, 100, 424 | converged, 51, 123 | 1.64 / 0.21 |
| states | 128 | 0.2 / 0.4 | 0.4 | None | stalled, 240, 456 | converged, 92, 182 | 7.14 / 0.37 |
| states | 128 | 0.5 / 1 | 0.2 | 0.01 | converged, 182, 776 | converged, 70, 151 | 0.98 / 0.71 |
| states | 128 | 0.5 / 1 | 0.2 | None | stalled, 240, 456 | converged, 102, 201 | 1.12 / 0.86 |
| states | 128 | 0.5 / 1 | 0.4 | 0.01 | stalled, 100, 424 | converged, 47, 110 | 1.64 / 0.93 |
| states | 128 | 0.5 / 1 | 0.4 | None | stalled, 240, 456 | converged, 85, 166 | 7.14 / 0.81 |
| states | 256 | 0.2 / 0.4 | 0.2 | 0.01 | converged, 148, 508 | converged, 123, 303 | 0.39 / 0.38 |
| states | 256 | 0.2 / 0.4 | 0.2 | None | converged, 192, 432 | converged, 152, 344 | 0.20 / 0.12 |
| states | 256 | 0.2 / 0.4 | 0.4 | 0.01 | converged, 100, 412 | converged, 71, 179 | 0.37 / 0.25 |
| states | 256 | 0.2 / 0.4 | 0.4 | None | stalled, 210, 462 | converged, 102, 234 | 0.79 / 0.26 |
| states | 256 | 0.5 / 1 | 0.2 | 0.01 | converged, 112, 256 | converged, 112, 256 | 0.78 / 0.78 |
| states | 256 | 0.5 / 1 | 0.2 | None | converged, 112, 256 | converged, 112, 256 | 0.78 / 0.78 |
| states | 256 | 0.5 / 1 | 0.4 | 0.01 | converged, 64, 160 | converged, 70, 178 | 0.89 / 0.95 |
| states | 256 | 0.5 / 1 | 0.4 | None | converged, 143, 323 | converged, 82, 190 | 0.85 / 0.60 |
| states | 512 | 0.2 / 0.4 | 0.2 | 0.01 | converged, 243, 1083 | converged, 221, 797 | 0.38 / 0.05 |
| states | 512 | 0.2 / 0.4 | 0.2 | None | converged, 336, 1152 | converged, 256, 880 | 0.38 / 0.37 |
| states | 512 | 0.2 / 0.4 | 0.4 | 0.01 | stalled, 220, 1804 | converged, 126, 534 | 0.64 / 0.13 |
| states | 512 | 0.2 / 0.4 | 0.4 | None | converged, 213, 741 | converged, 151, 535 | 0.23 / 0.33 |
| states | 512 | 0.5 / 1 | 0.2 | 0.01 | converged, 219, 771 | converged, 219, 771 | 0.68 / 0.32 |
| states | 512 | 0.5 / 1 | 0.2 | None | converged, 256, 880 | converged, 256, 880 | 0.97 / 0.42 |
| states | 512 | 0.5 / 1 | 0.4 | 0.01 | converged, 132, 660 | converged, 118, 454 | 0.94 / 0.54 |
| states | 512 | 0.5 / 1 | 0.4 | None | converged, 173, 605 | converged, 151, 535 | 0.72 / 0.26 |
| districts | 256 | 0.2 / 0.4 | 0.2 | 0.01 | stalled, 220, 1291 | converged, 167, 608 | 0.49 / 0.17 |
| districts | 256 | 0.2 / 0.4 | 0.2 | None | stalled, 250, 775 | converged, 205, 646 | 1.66 / 0.23 |
| districts | 256 | 0.2 / 0.4 | 0.4 | 0.01 | stalled, 150, 1137 | converged, 106, 547 | 0.83 / 0.33 |
| districts | 256 | 0.2 / 0.4 | 0.4 | None | stalled, 190, 589 | stalled, 190, 589 | 62.42 / 62.42 |
| districts | 256 | 0.5 / 1 | 0.2 | 0.01 | converged, 156, 555 | converged, 159, 558 | 0.73 / 0.99 |
| districts | 256 | 0.5 / 1 | 0.2 | None | stalled, 250, 775 | converged, 195, 615 | 1.66 / 0.59 |
| districts | 256 | 0.5 / 1 | 0.4 | 0.01 | converged, 97, 538 | converged, 91, 448 | 0.85 / 0.45 |
| districts | 256 | 0.5 / 1 | 0.4 | None | stalled, 190, 589 | stalled, 190, 589 | 62.42 / 62.42 |

Converged: constant dt 17 of 32, adaptive_dt 30 of 32.

## Late phase: true maximum area error over the last 50 of 300 iterations (every iteration recorded, tolerances unreachable)

| input | dt | recompute_on_rise | constant dt: lowest / median / highest % | adaptive_dt: lowest / median / highest % |
|---|---|---|---|---|
| states | 0.1 | 0.01 | 0.426 / 0.622 / 2.160 | 0.065 / 0.088 / 0.497 |
| states | 0.1 | None | 0.228 / 4.159 / 17.562 | 0.108 / 1.392 / 6.683 |
| states | 0.2 | 0.01 | 0.302 / 0.814 / 2.003 | 0.055 / 0.115 / 0.294 |
| states | 0.2 | None | 0.303 / 5.322 / 14.540 | 0.055 / 0.728 / 1.877 |
| states | 0.4 | 0.01 | 1.287 / 2.371 / 6.223 | 0.220 / 0.232 / 0.696 |
| states | 0.4 | None | 1.114 / 8.717 / 19.548 | 0.081 / 1.194 / 3.110 |
| districts | 0.2 | 0.01 | 0.388 / 0.964 / 2.742 | 0.015 / 0.278 / 0.663 |
| districts | 0.2 | None | 2.849 / 5.947 / 14.051 | 0.074 / 1.156 / 2.400 |

## Second run on the output of a first run (tight tolerances 0.5 % / 1 %, workflow refinement)

| input | grid | first run | constant dt: status, it, cost, score after it 1, max score in it 1-5 | adaptive_dt: same |
|---|---|---|---|---|
| states | 256 | converged at 0.5 % / 1 % | converged, 4, 28, 2.5, 5.6 | converged, 1, 13, 0.4, 0.4 |
| states | 256 | converged at 5 % / 20 % | converged, 92, 620, 1.6, 14.0 | converged, 3, 27, 1.5, 3.3 |
| states | 512 | converged at 0.5 % / 1 % | converged, 4, 52, 2.7, 6.2 | converged, 1, 25, 0.0, 0.0 |
| states | 512 | converged at 5 % / 20 % | converged, 4, 52, 8.0, 8.0 | converged, 3, 27, 8.0, 8.0 |
| districts | 256 | converged at 0.5 % / 1 % | converged, 4, 46, 2.3, 5.3 | converged, 1, 22, 0.6, 0.6 |
| districts | 256 | converged at 5 % / 20 % | converged, 7, 70, 7.0, 9.3 | converged, 13, 97, 7.0, 7.0 |

## Multiresolution (min_resolution 128, 3 levels, 300 iterations per level)

| input | tolerances | dt | constant dt: levels (grid:status:it), cost, true max % | adaptive_dt: same |
|---|---|---|---|---|
| states | default 5 % / 10 % | 0.2 | 128:conv:63, 126, 9.15 | 128:conv:63, 126, 9.15 |
| states | default 5 % / 10 % | 0.4 | 128:conv:39, 93, 4.12 | 128:conv:41, 95, 5.57 |
| states | 0.5 % / 1 % | 0.2 | 128:conv:94, 292, 0.97 | 128:conv:69, 150, 0.75 |
| states | 0.5 % / 1 % | 0.4 | 128:conv:45, 126, 0.64 | 128:conv:48, 111, 0.85 |
| districts | default 5 % / 10 % | 0.2 | 128:conv:123, 447, 8.31 | 128:conv:123, 447, 9.67 |
| districts | default 5 % / 10 % | 0.4 | 128:stal:120 256:stal:50 512:stal:50, 1317, 36.37 | 128:stal:120 256:stal:50 512:stal:50, 1317, 36.28 |
| districts | 0.5 % / 1 % | 0.2 | 128:conv:173, 947, 0.97 | 128:conv:149, 671, 0.97 |
| districts | 0.5 % / 1 % | 0.4 | 128:stal:140 256:stal:50 512:stal:50, 1499, 36.37 | 128:stal:140 256:stal:50 512:stal:50, 1520, 36.37 |

## With and without recompute_on_rise

| input | dt | tolerances | recompute_on_rise | constant dt: status, it, cost | adaptive_dt: status, it, cost |
|---|---|---|---|---|---|
| states | 0.2 | (0.002, 0.004) | 0.01 | converged, 148, 508 | converged, 123, 303 |
| states | 0.2 | (0.002, 0.004) | None | converged, 192, 432 | converged, 152, 344 |
| states | 0.4 | (0.002, 0.004) | 0.01 | converged, 100, 412 | converged, 71, 179 |
| states | 0.4 | (0.002, 0.004) | None | stalled, 210, 462 | converged, 102, 234 |
| tilted | 0.6 | default | 0.01 | converged, 95, 275 | converged, 98, 278 |
| tilted | 0.6 | default | None | stalled, 130, 286 | stalled, 130, 286 |
| horizontal | 0.6 | default | 0.01 | converged, 122, 338 | converged, 127, 343 |
| horizontal | 0.6 | default | None | converged, 164, 368 | converged, 162, 366 |

## Counties (3,108, grid 256, 300 iterations)

| adaptive_dt | status | iterations | best iteration | reported mean / max % | true mean / max % | wall s |
|---|---|---|---|---|---|---|
| False | stalled | 210 | 169 | 44.6 / 5351 | 49.6 / 5018 | 3.2 |
| True | stalled | 210 | 169 | 44.6 / 5351 | 49.6 / 5018 | 3.0 |

