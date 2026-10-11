| case | before: status, iterations, true max error | after: status, iterations, true max error |
|---|---|---|
| districts, grid 128, dt 0.4, 1 % / 2 % | stalled, 110, 26.41 % | converged, 151, 1.95 % |
| districts, grid 128, dt 0.2, 1 % / 2 % | converged, 135, 1.58 % | converged, 135, 1.58 % |
| districts, grid 256, tolerances 0.5 % / 1 % | converged, 156, 0.73 % | converged, 156, 0.73 % |
| districts, grid 256, default tolerances | converged, 145, 9.76 % | converged, 145, 9.76 % |
| states, grid 256, default tolerances | converged, 112, 0.78 % | converged, 112, 0.78 % |

Stalled run (before): 22 of 432 regions are invalid; the rings of regions [23, 98] reach the rasterizer with a sign opposite to their shoelace area (true errors 3.9 %, 21.2 %). The worst region is 41 (error 26.4 %); the wrong-sign regions are not among its six nearest neighbors. The two fields differ in 31 cells; the summed density deviation (cells) there is -0.068 before and +0.564 after.
