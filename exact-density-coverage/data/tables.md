- grid 128: DC covers 0.04 cells; cells whose density changes by more than 10 %: 26 in the crop
- grid 256: DC covers 0.15 cells; cells whose density changes by more than 10 %: 84 in the crop

| input | grid | rasterization | status | iterations | reported max error % | true max error % | true mean error % | seconds |
|---|---|---|---|---|---|---|---|---|
| states | 128 | center | converged | 63 | 8.30 | 7.75 | 1.193 | 0.3 |
| states | 128 | exact | converged | 62 | 9.66 | 8.87 | 1.297 | 0.2 |
| states | 256 | center | converged | 113 | 4.38 | 4.36 | 0.313 | 0.6 |
| states | 256 | exact | converged | 112 | 0.79 | 0.78 | 0.203 | 0.2 |
| districts | 256 | center | converged | 150 | 8.00 | 8.05 | 1.065 | 0.7 |
| districts | 256 | exact | converged | 145 | 9.76 | 9.76 | 1.415 | 0.5 |

| input | rasterization | level | grid | status | iterations |
|---|---|---|---|---|---|
| states | center | 1 | 128 | stalled | 100 |
| states | center | 2 | 256 | converged | 34 |
| states | center | total | - | converged | 134 (true max error 5.63 %) |
| states | exact | 1 | 128 | converged | 63 |
| states | exact | total | - | converged | 63 (true max error 9.15 %) |
| districts | center | 1 | 128 | converged | 231 |
| districts | center | total | - | converged | 231 (true max error 8.72 %) |
| districts | exact | 1 | 128 | converged | 123 |
| districts | exact | total | - | converged | 123 (true max error 8.31 %) |

True area error with unreachable tolerances (300 iterations, stall rule off):

| input | grid | rasterization | lowest true max error % | at iteration | true max error % at iteration 291 | true mean error % at iteration 291 |
|---|---|---|---|---|---|---|
| states | 256 | center | 0.04 | 291 | 0.04 | 0.015 |
| states | 256 | exact | 1.32 | 291 | 1.32 | 0.544 |
| states | 512 | center | 0.03 | 241 | 0.06 | 0.016 |
| states | 512 | exact | 0.33 | 261 | 0.35 | 0.093 |
| districts | 256 | center | 0.17 | 291 | 0.17 | 0.033 |
| districts | 256 | exact | 1.53 | 291 | 1.53 | 0.407 |

Stopping at tolerances (mean tolerance / max tolerance as fractions; true errors in %):

| input | grid | tolerances | center: status, iterations, true max, true mean | exact: status, iterations, true max, true mean |
|---|---|---|---|---|
| states | 256 | 0.02 / 0.04 | converged, 115, 0.62, 0.071 | converged, 112, 0.78, 0.203 |
| states | 256 | 0.01 / 0.02 | converged, 115, 0.62, 0.071 | converged, 112, 0.78, 0.203 |
| states | 256 | 0.005 / 0.01 | converged, 115, 0.62, 0.071 | converged, 112, 0.78, 0.203 |
| states | 256 | 0.002 / 0.004 | converged, 161, 0.37, 0.073 | converged, 148, 0.39, 0.129 |
| states | 512 | 0.02 / 0.04 | converged, 215, 1.43, 0.186 | converged, 215, 3.32, 0.237 |
| states | 512 | 0.01 / 0.02 | converged, 215, 1.43, 0.186 | converged, 219, 0.68, 0.113 |
| states | 512 | 0.005 / 0.01 | converged, 217, 0.53, 0.067 | converged, 219, 0.68, 0.113 |
| states | 512 | 0.002 / 0.004 | converged, 219, 0.30, 0.054 | converged, 243, 0.38, 0.099 |
| districts | 256 | 0.02 / 0.04 | converged, 153, 3.64, 0.355 | converged, 151, 3.76, 0.571 |
| districts | 256 | 0.01 / 0.02 | converged, 155, 1.88, 0.252 | converged, 154, 1.50, 0.173 |
| districts | 256 | 0.005 / 0.01 | converged, 163, 0.90, 0.165 | converged, 156, 0.73, 0.132 |
| districts | 256 | 0.002 / 0.004 | converged, 235, 0.39, 0.074 | stalled, 220, 0.49, 0.109 |

| input | grid | center ms | exact ms |
|---|---|---|---|
| states | 128 | 2.0 | 2.4 |
| states | 256 | 3.0 | 2.4 |
| states | 512 | 7.1 | 4.5 |
| states | 1024 | 23.0 | 12.8 |
| districts | 128 | 14.9 | 11.4 |
| districts | 256 | 18.7 | 8.3 |
| districts | 512 | 23.2 | 10.6 |
| districts | 1024 | 40.9 | 19.8 |
