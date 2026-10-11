| grid | regions below the one-cell floor (current or target) | one-cell floor (main) | error_floor 1e-3 (new) | no floor |
|---|---|---|---|---|
| 128 | 203 of 432 | 176 % | 513 % | 513 % |
| 256 | 115 of 432 | 361 % | 513 % | 513 % |
| 512 | 33 of 432 | 477 % | 513 % | 513 % |
| 1024 | 6 of 432 | 509 % | 513 % | 513 % |

| input | grid | floor | status | iterations | reported mean % | reported max % | true max % | seconds |
|---|---|---|---|---|---|---|---|---|
| states | 128 | one cell (main) | converged | 63 | 1.21 | 8.30 | 7.75 | 0.2 |
| states | 128 | 1e-3 (new) | converged | 63 | 1.21 | 8.30 | 7.75 | 0.2 |
| states | 256 | one cell (main) | converged | 113 | 0.32 | 4.38 | 4.36 | 0.2 |
| states | 256 | 1e-3 (new) | converged | 113 | 0.32 | 4.38 | 4.36 | 0.2 |
| states | 512 | one cell (main) | converged | 214 | 0.50 | 7.28 | 7.27 | 0.6 |
| states | 512 | 1e-3 (new) | converged | 214 | 0.50 | 7.28 | 7.27 | 0.6 |
| districts | 256 | one cell (main) | converged | 150 | 1.07 | 8.00 | 8.05 | 0.7 |
| districts | 256 | 1e-3 (new) | converged | 150 | 1.07 | 8.00 | 8.05 | 0.8 |
| districts | 512 | one cell (main) | converged | 263 | 0.60 | 9.49 | 9.46 | 1.6 |
| districts | 512 | 1e-3 (new) | converged | 263 | 0.60 | 9.49 | 9.46 | 1.7 |

Counties (3108, total votes, area_scale 1e-6, 300 iterations):

| grid | floor | initial mean error % | status | iterations | reported mean % | reported max % | true mean % | true max % |
|---|---|---|---|---|---|---|---|---|
| 256 | one cell (main) | 94.7 | stalled | 300 | 4.47 | 156.2 | 58.5 | 2117.7 |
| 256 | 1e-3 (new) | 372.3 | stalled | 210 | 58.59 | 5351.5 | 75.8 | 5330.0 |
| 256 | 1e-4 | 372.3 | stalled | 220 | 56.17 | 7256.8 | 67.6 | 3164.1 |
| 256 | 0 | 372.3 | stalled | 220 | 56.17 | 7256.8 | 67.6 | 3164.1 |
| 512 | one cell (main) | 270.4 | completed | 300 | 7.98 | 204.0 | 26.4 | 2811.6 |
| 512 | 1e-3 (new) | 372.3 | completed | 300 | 37.17 | 5351.5 | 55.0 | 5318.0 |
| 512 | 1e-4 | 372.3 | completed | 300 | 29.21 | 6811.4 | 39.8 | 4324.5 |
| 512 | 0 | 372.3 | completed | 300 | 29.21 | 6811.4 | 39.8 | 4324.5 |
