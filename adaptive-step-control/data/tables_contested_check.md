Measured on the rebased branch after #124 (ring orientation), with the contested-regions commit applied (1a70e9d). Status c converged, s stalled; iterations / true max error of the output.

Multiresolution (min_resolution 128, 3 levels, 300 iterations per level):

| input | tolerances | dt | constant dt | CONTESTED_FRACTION 0 (dead band only) | 0.8 |
|---|---|---|---|---|---|
| districts | 0.5 % / 1 % | 0.2 | 128: c173, 1.0 % | 128: c157, 0.7 % | 128: c152, 0.9 % |
| districts | 0.2 % / 0.4 % | 0.2 | 128: s270, 256: s50, 512: c3, 0.4 % | 128: s240, 256: c12, 0.4 % | 128: s240, 256: s50, 512: s50, 0.5 % |
| districts | default | 0.4 | 128: c102, 8.9 % | 128: c102, 8.9 % | 128: c106, 9.0 % |
| districts | 0.5 % / 1 % | 0.4 | 128: s160, 256: s50, 512: s50, 6.1 % | s170, s50, s50, 4.8 % | s170, s50, s50, 5.3 % |
| states | 0.5 % / 1 % | 0.2 | 128: c94, 1.0 % | 128: c70, 0.5 % | 128: c69, 0.7 % |

Single runs:

| input | grid | dt | tolerances % | recompute_on_rise | constant dt | dead band only | 0.8 |
|---|---|---|---|---|---|---|---|
| states | 128 | 0.2 | 0.2 / 0.4 | 0.01 | c400, 0.46 % | c73, 0.17 % | c73, 0.31 % |
| states | 256 | 0.2 | 0.2 / 0.4 | 0.01 | c148, 0.39 % | c118, 0.21 % | c123, 0.38 % |
| states | 512 | 0.4 | 0.2 / 0.4 | 0.01 | s220, 0.64 % | c114, 0.33 % | c126, 0.13 % |
| states | 128 | 0.2 | 0.1 / 0.2 | 0.01 | c400, 0.46 % | c74, 0.16 % | c138, 0.20 % |
| states | 256 | 0.2 | 0.1 / 0.2 | 0.01 | s260, 0.31 % | c121, 0.11 % | c124, 0.18 % |
| states | 128 | 0.2 | 0.2 / 0.4 | None | s270, 1.12 % | c103, 0.39 % | c182, 0.35 % |
| districts | 256 | 0.2 | 0.5 / 1 | 0.01 | c156, 0.73 % | c160, 0.51 % | c159, 0.99 % |
| districts | 256 | 0.4 | 0.5 / 1 | 0.01 | c97, 0.85 % | c93, 0.99 % | c91, 0.45 % |
| states | 256 | 0.6 | default | 0.01 | c42, 6.64 % | c42, 6.64 % | c42, 6.64 % |
| districts | 256 | 0.4 | default | 0.01 | c81, 4.84 % | c81, 4.84 % | c80, 9.53 % |
| districts | 128 | 0.2 | 0.2 / 0.4 | 0.01 | c259, 0.39 % | c210, 0.37 % | c181, 0.37 % |
| districts | 128 | 0.4 | 1 / 2 | 0.01 | c151, 1.95 % | c124, 1.91 % | c122, 1.96 % |
| districts | 256 | 0.4 | 0.5 / 1 | None | s190, 62.42 % | c184, 0.86 % | s190, 62.42 % |
| | | | | total iterations | 2674 | 1497 | 1631 |
