- grid 128: DC covers 0.04 cells; cells whose density changes by more than 10 %: 26 in the crop
- grid 256: DC covers 0.15 cells; cells whose density changes by more than 10 %: 84 in the crop

| input | grid | rasterization | status | iterations | reported max error % | true max error % | true mean error % | seconds |
|---|---|---|---|---|---|---|---|---|
| states | 128 | center | converged | 63 | 8.30 | 7.75 | 1.193 | 0.3 |
| states | 128 | exact | converged | 62 | 9.66 | 8.87 | 1.297 | 0.3 |
| states | 256 | center | converged | 113 | 4.38 | 4.36 | 0.313 | 0.6 |
| states | 256 | exact | converged | 112 | 0.79 | 0.78 | 0.203 | 0.2 |
| districts | 256 | center | converged | 150 | 8.00 | 8.05 | 1.065 | 0.8 |
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

Late phase of the states at grid 256 (300 iterations, tolerances unreachable, stall rule off, every iteration recorded). True maximum area error over the last 50 iterations:

| rasterization | lowest % | median % | highest % |
|---|---|---|---|
| center | 0.020 | 1.049 | 2.547 |
| exact | 0.303 | 0.815 | 2.003 |

Fresh field at every iteration (recompute_every=1, no recompute on rise); true maximum error over the last 30 iterations against dt:

| dt | center: lowest / median / highest % | exact: lowest / median / highest % |
|---|---|---|
| 0.4 | 1.445 / 1.482 / 1.538 | 1.102 / 1.583 / 2.248 |
| 0.2 | 0.580 / 0.769 / 0.904 | 0.724 / 0.804 / 0.912 |
| 0.1 | 0.082 / 0.467 / 1.120 | 0.193 / 0.426 / 0.685 |
| 0.05 | 0.175 / 0.204 / 0.246 | 0.206 / 0.210 / 0.213 |

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
| states | 128 | 1.8 | 2.8 |
| states | 256 | 2.8 | 2.6 |
| states | 512 | 6.1 | 4.4 |
| states | 1024 | 20.4 | 11.3 |
| districts | 128 | 12.3 | 6.6 |
| districts | 256 | 15.0 | 7.0 |
| districts | 512 | 19.7 | 8.9 |
| districts | 1024 | 36.3 | 17.2 |
