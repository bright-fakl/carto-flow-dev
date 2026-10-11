## Fresh runs, default tolerances (5 % / 10 %), wall time is the minimum of two runs

| input | grid | dt | constant dt: status, iterations, recomputes, cost, wall s, true max % | adaptive_dt: same |
|---|---|---|---|---|
| states | 128 | 0.2 | converged, 62, 7, 125, 0.14, 8.87 | converged, 62, 7, 125, 0.14, 8.87 |
| states | 256 | 0.2 | converged, 112, 12, 256, 0.30, 0.78 | converged, 112, 12, 256, 0.23, 0.78 |
| states | 512 | 0.2 | converged, 214, 22, 742, 0.54, 9.22 | converged, 214, 22, 742, 0.55, 9.22 |
| districts | 256 | 0.2 | converged, 145, 15, 460, 0.57, 9.76 | converged, 145, 15, 460, 0.56, 9.76 |
| states | 256 | 0.4 | converged, 62, 7, 146, 0.15, 3.50 | converged, 62, 7, 146, 0.15, 3.50 |
| districts | 256 | 0.4 | converged, 81, 13, 354, 0.41, 4.84 | converged, 81, 13, 354, 0.42, 4.84 |
| horizontal | 256 | 0.2 | converged, 207, 24, 495, 0.35, 8.98 | converged, 207, 24, 495, 0.35, 8.98 |
| horizontal | 256 | 0.6 | converged, 122, 18, 338, 0.38, 8.20 | converged, 122, 18, 338, 0.28, 8.20 |
| tangential | 256 | 0.2 | converged, 187, 20, 427, 0.32, 7.49 | converged, 187, 20, 427, 0.30, 7.49 |
| tangential | 256 | 0.6 | converged, 118, 21, 370, 0.26, 8.63 | converged, 118, 21, 370, 0.27, 8.63 |
| tilted | 256 | 0.2 | converged, 162, 17, 366, 0.27, 7.75 | converged, 162, 17, 366, 0.28, 7.75 |
| tilted | 256 | 0.6 | converged, 95, 15, 275, 0.22, 8.52 | converged, 95, 15, 275, 0.21, 8.52 |

## Tight tolerances (mean / max)

| input | grid | tolerances % | dt | recompute_on_rise | constant dt: status, it, cost | adaptive_dt: status, it, cost | true max %: constant / adaptive |
|---|---|---|---|---|---|---|---|
| states | 128 | 0.2 / 0.4 | 0.2 | 0.01 | completed, 400, 1975 | converged, 73, 163 | 0.46 / 0.17 |
| states | 128 | 0.2 / 0.4 | 0.2 | None | stalled, 270, 513 | converged, 103, 202 | 1.12 / 0.39 |
| states | 128 | 0.2 / 0.4 | 0.4 | 0.01 | stalled, 100, 424 | converged, 52, 124 | 1.64 / 0.17 |
| states | 128 | 0.2 / 0.4 | 0.4 | None | stalled, 240, 456 | converged, 87, 168 | 7.14 / 0.28 |
| states | 128 | 0.5 / 1 | 0.2 | 0.01 | converged, 182, 776 | converged, 71, 152 | 0.98 / 0.57 |
| states | 128 | 0.5 / 1 | 0.2 | None | stalled, 240, 456 | converged, 102, 201 | 1.12 / 0.97 |
| states | 128 | 0.5 / 1 | 0.4 | 0.01 | stalled, 100, 424 | converged, 45, 108 | 1.64 / 0.99 |
| states | 128 | 0.5 / 1 | 0.4 | None | stalled, 240, 456 | converged, 94, 184 | 7.14 / 0.32 |
| states | 256 | 0.2 / 0.4 | 0.2 | 0.01 | converged, 148, 508 | converged, 118, 286 | 0.39 / 0.21 |
| states | 256 | 0.2 / 0.4 | 0.2 | None | converged, 192, 432 | converged, 151, 343 | 0.20 / 0.34 |
| states | 256 | 0.2 / 0.4 | 0.4 | 0.01 | converged, 100, 412 | converged, 70, 178 | 0.37 / 0.15 |
| states | 256 | 0.2 / 0.4 | 0.4 | None | stalled, 210, 462 | converged, 122, 278 | 0.79 / 0.19 |
| states | 256 | 0.5 / 1 | 0.2 | 0.01 | converged, 112, 256 | converged, 112, 256 | 0.78 / 0.78 |
| states | 256 | 0.5 / 1 | 0.2 | None | converged, 112, 256 | converged, 112, 256 | 0.78 / 0.78 |
| states | 256 | 0.5 / 1 | 0.4 | 0.01 | converged, 64, 160 | converged, 68, 176 | 0.89 / 0.19 |
| states | 256 | 0.5 / 1 | 0.4 | None | converged, 143, 323 | converged, 99, 219 | 0.85 / 0.95 |
| states | 512 | 0.2 / 0.4 | 0.2 | 0.01 | converged, 243, 1083 | converged, 229, 877 | 0.38 / 0.07 |
| states | 512 | 0.2 / 0.4 | 0.2 | None | converged, 336, 1152 | converged, 256, 880 | 0.38 / 0.23 |
| states | 512 | 0.2 / 0.4 | 0.4 | 0.01 | stalled, 220, 1804 | converged, 114, 426 | 0.64 / 0.33 |
| states | 512 | 0.2 / 0.4 | 0.4 | None | converged, 213, 741 | converged, 152, 536 | 0.23 / 0.24 |
| states | 512 | 0.5 / 1 | 0.2 | 0.01 | converged, 219, 771 | converged, 219, 771 | 0.68 / 0.68 |
| states | 512 | 0.5 / 1 | 0.2 | None | converged, 256, 880 | converged, 244, 844 | 0.97 / 0.98 |
| states | 512 | 0.5 / 1 | 0.4 | 0.01 | converged, 132, 660 | converged, 118, 454 | 0.94 / 0.54 |
| states | 512 | 0.5 / 1 | 0.4 | None | converged, 173, 605 | converged, 132, 468 | 0.72 / 0.36 |
| districts | 256 | 0.2 / 0.4 | 0.2 | 0.01 | stalled, 220, 1291 | converged, 166, 607 | 0.49 / 0.17 |
| districts | 256 | 0.2 / 0.4 | 0.2 | None | stalled, 250, 775 | converged, 205, 646 | 1.66 / 0.21 |
| districts | 256 | 0.2 / 0.4 | 0.4 | 0.01 | converged, 137, 998 | converged, 103, 544 | 0.37 / 0.33 |
| districts | 256 | 0.2 / 0.4 | 0.4 | None | stalled, 190, 589 | converged, 167, 524 | 62.42 / 0.33 |
| districts | 256 | 0.5 / 1 | 0.2 | 0.01 | converged, 156, 555 | converged, 160, 559 | 0.73 / 0.51 |
| districts | 256 | 0.5 / 1 | 0.2 | None | stalled, 250, 775 | converged, 195, 615 | 1.66 / 0.53 |
| districts | 256 | 0.5 / 1 | 0.4 | 0.01 | converged, 97, 538 | converged, 93, 471 | 0.85 / 0.99 |
| districts | 256 | 0.5 / 1 | 0.4 | None | stalled, 190, 589 | converged, 184, 583 | 62.42 / 0.86 |

Converged: constant dt 18 of 32, adaptive_dt 32 of 32.

## Late phase: true maximum area error over the last 50 of 300 iterations (every iteration recorded, tolerances unreachable)

| input | dt | recompute_on_rise | constant dt: lowest / median / highest % | adaptive_dt: lowest / median / highest % |
|---|---|---|---|---|
| states | 0.1 | 0.01 | 0.426 / 0.622 / 2.160 | 0.013 / 0.278 / 0.746 |
| states | 0.1 | None | 0.228 / 4.159 / 17.562 | 0.060 / 1.111 / 3.785 |
| states | 0.2 | 0.01 | 0.302 / 0.814 / 2.003 | 0.101 / 0.108 / 0.322 |
| states | 0.2 | None | 0.303 / 5.322 / 14.540 | 0.075 / 0.482 / 1.435 |
| states | 0.4 | 0.01 | 1.287 / 2.371 / 6.223 | 0.001 / 0.385 / 0.808 |
| states | 0.4 | None | 1.114 / 8.717 / 19.548 | 0.061 / 1.128 / 3.184 |
| districts | 0.2 | 0.01 | 0.388 / 0.964 / 2.742 | 0.034 / 0.335 / 0.813 |
| districts | 0.2 | None | 2.849 / 5.947 / 14.051 | 0.171 / 1.958 / 4.034 |

## Second run on the output of a first run (tight tolerances 0.5 % / 1 %, workflow refinement)

| input | grid | first run | constant dt: status, it, cost, score after it 1, max score in it 1-5 | adaptive_dt: same |
|---|---|---|---|---|
| states | 256 | converged at 0.5 % / 1 % | converged, 4, 28, 2.5, 5.6 | converged, 1, 13, 0.4, 0.4 |
| states | 256 | converged at 5 % / 20 % | converged, 92, 620, 1.6, 14.0 | converged, 3, 27, 1.5, 3.3 |
| states | 512 | converged at 0.5 % / 1 % | converged, 4, 52, 2.7, 6.2 | converged, 1, 25, 0.3, 0.3 |
| states | 512 | converged at 5 % / 20 % | converged, 4, 52, 8.0, 8.0 | converged, 3, 27, 8.0, 8.0 |
| districts | 256 | converged at 0.5 % / 1 % | converged, 4, 46, 2.3, 5.3 | converged, 1, 22, 0.3, 0.3 |
| districts | 256 | converged at 5 % / 20 % | converged, 7, 70, 7.0, 9.3 | converged, 13, 97, 7.0, 7.0 |

## Multiresolution (min_resolution 128, 3 levels, 300 iterations per level)

| input | tolerances | dt | constant dt: levels (grid:status:it), cost, true max % | adaptive_dt: same |
|---|---|---|---|---|
| states | default 5 % / 10 % | 0.2 | 128:conv:63, 126, 9.15 | 128:conv:63, 126, 9.15 |
| states | default 5 % / 10 % | 0.4 | 128:conv:39, 93, 4.12 | 128:conv:39, 93, 6.29 |
| states | 0.5 % / 1 % | 0.2 | 128:conv:94, 292, 0.97 | 128:conv:70, 151, 0.54 |
| states | 0.5 % / 1 % | 0.4 | 128:conv:45, 126, 0.64 | 128:conv:49, 112, 0.76 |
| districts | default 5 % / 10 % | 0.2 | 128:conv:123, 447, 8.32 | 128:conv:123, 447, 8.32 |
| districts | default 5 % / 10 % | 0.4 | 128:conv:102, 480, 8.92 | 128:conv:102, 480, 8.92 |
| districts | 0.5 % / 1 % | 0.2 | 128:conv:173, 947, 0.97 | 128:conv:157, 715, 0.70 |
| districts | 0.5 % / 1 % | 0.4 | 128:stal:160 256:stal:50 512:stal:50, 3154, 6.07 | 128:stal:170 256:stal:50 512:stal:50, 3509, 4.84 |

## With and without recompute_on_rise

| input | dt | tolerances | recompute_on_rise | constant dt: status, it, cost | adaptive_dt: status, it, cost |
|---|---|---|---|---|---|
| states | 0.2 | (0.002, 0.004) | 0.01 | converged, 148, 508 | converged, 118, 286 |
| states | 0.2 | (0.002, 0.004) | None | converged, 192, 432 | converged, 151, 343 |
| states | 0.4 | (0.002, 0.004) | 0.01 | converged, 100, 412 | converged, 70, 178 |
| states | 0.4 | (0.002, 0.004) | None | stalled, 210, 462 | converged, 122, 278 |
| tilted | 0.6 | default | 0.01 | converged, 95, 275 | converged, 95, 275 |
| tilted | 0.6 | default | None | stalled, 130, 286 | stalled, 130, 286 |
| horizontal | 0.6 | default | 0.01 | converged, 122, 338 | converged, 122, 338 |
| horizontal | 0.6 | default | None | converged, 164, 368 | converged, 164, 368 |

