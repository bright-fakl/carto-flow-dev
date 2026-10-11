## held-out fresh runs

| case | constant | cf 0.8 | cf 0.9 | cf 1.0 |
|---|---|---|---|---|
| horizontal dt 0.4 | 134 c, 8.58 % | 140 c, 8.77 % | 139 c, 9.77 % | 139 c, 9.94 % |
| horizontal dt 0.8 | 96 c, 8.65 % | 107 c, 8.99 % | 102 c, 8.94 % | 102 c, 8.91 % |
| tangential dt 0.4 | 111 c, 8.18 % | 111 c, 8.07 % | 111 c, 8.07 % | 111 c, 8.18 % |
| tangential dt 0.8 | 109 c, 9.18 % | 122 c, 9.12 % | 133 c, 9.08 % | 122 c, 9.13 % |
| tilted dt 0.4 | 109 c, 8.78 % | 109 c, 9.05 % | 109 c, 9.05 % | 109 c, 8.79 % |
| tilted dt 0.8 | 76 c, 8.02 % | 76 c, 8.63 % | 76 c, 8.63 % | 76 c, 8.63 % |
| states 128 dt .4 default | 36 c, 4.79 % | 36 c, 7.6 % | 36 c, 7.6 % | 36 c, 7.6 % |
| states 512 dt .4 default | 111 c, 8.79 % | 111 c, 8.79 % | 111 c, 8.79 % | 111 c, 8.79 % |
| districts 256 dt .2 default | 145 c, 9.76 % | 145 c, 9.76 % | 145 c, 9.76 % | 145 c, 9.76 % |
| districts 256 dt .4 default | 81 c, 4.84 % | 80 c, 9.53 % | 80 c, 9.53 % | 80 c, 9.53 % |
| states 128 tol 1/2 dt .2 | 66 c, 1.95 % | 67 c, 1.41 % | 67 c, 1.41 % | 66 c, 1.16 % |
| states 128 tol .1/.2 dt .2 | 400 c, 0.46 % | 138 c, 0.2 % | 138 c, 0.2 % | 76 c, 0.02 % |
| states 256 tol 1/2 dt .2 | 112 c, 0.78 % | 112 c, 0.78 % | 112 c, 0.78 % | 112 c, 0.78 % |
| states 256 tol .1/.2 dt .2 | 260 s, 0.31 % | 124 c, 0.18 % | 124 c, 0.18 % | 124 c, 0.16 % |
| states 256 tol .2/.4 dt .2 rise on | 148 c, 0.39 % | 123 c, 0.38 % | 123 c, 0.38 % | 123 c, 0.1 % |

Sum of iterations: constant 1994, cf 0.8 1601, cf 0.9 1606, cf 1.0 1532

## held-out multiresolution and continuation

| case | constant | cf 0.8 | cf 0.9 | cf 1.0 |
|---|---|---|---|---|
| multires states .5/1 | 94 c, 0.97 % | 69 c, 0.75 % | 69 c, 0.75 % | 69 c, 0.75 % |
| multires districts default | 123 c, 8.31 % | 123 c, 9.67 % | 125 c, 9.88 % | 123 c, 8.93 % |
| cont states 256 5/20 -> .5/1 | 92 c, 0.98 % | 3 c, 0.41 % | 3 c, 0.41 % | 3 c, 0.41 % |
| cont districts 256 5/20 -> .5/1 | 7 c, 0.78 % | 13 c, 0.75 % | 13 c, 0.75 % | 13 c, 0.71 % |

Sum of iterations: constant 316, cf 0.8 208, cf 0.9 210, cf 1.0 208

## original 11 cases

| case | constant | cf 0.8 | cf 0.9 | cf 1.0 |
|---|---|---|---|---|
| states 256 default dt .2 | 112 c, 0.78 % | 112 c, 0.78 % | 112 c, 0.78 % | 112 c, 0.78 % |
| states 256 default dt .4 | 62 c, 3.5 % | 62 c, 3.5 % | 62 c, 3.5 % | 62 c, 3.5 % |
| horizontal dt .6 | 122 c, 8.2 % | 127 c, 8.48 % | 127 c, 8.48 % | 124 c, 8.31 % |
| tangential dt .6 | 118 c, 8.63 % | 123 c, 9.2 % | 127 c, 8.91 % | 124 c, 8.84 % |
| tilted dt .6 | 95 c, 8.52 % | 98 c, 9.17 % | 98 c, 9.11 % | 97 c, 8.21 % |
| districts 128 default | 118 c, 9.77 % | 118 c, 9.89 % | 118 c, 9.77 % | 118 c, 9.77 % |
| states 256 .2/.4 rise None dt .2 | 192 c, 0.2 % | 152 c, 0.12 % | 152 c, 0.12 % | 171 c, 0.29 % |
| states 256 .2/.4 dt .4 | 100 c, 0.37 % | 71 c, 0.25 % | 71 c, 0.25 % | 71 c, 0.25 % |
| states 256 .5/1 dt .2 | 112 c, 0.78 % | 112 c, 0.78 % | 112 c, 0.78 % | 112 c, 0.78 % |
| districts 256 .5/1 dt .2 | 156 c, 0.73 % | 159 c, 0.99 % | 159 c, 0.99 % | 160 c, 0.49 % |
| states 512 .5/1 dt .2 | 219 c, 0.68 % | 219 c, 0.32 % | 219 c, 0.32 % | 219 c, 0.2 % |

Sum of iterations: constant 1406, cf 0.8 1353, cf 0.9 1357, cf 1.0 1370

## districts, three more tolerances in a multiresolution run

| case | constant | cf 0.8 | cf 0.9 | cf 1.0 |
|---|---|---|---|---|
| multires districts (0.01, 0.02) | 157 c, 2.0 % | 141 c, 1.9 % | 151 c, 1.94 % | 145 c, 1.46 % |
| multires districts (0.005, 0.01) | 173 c, 0.97 % | 149 c, 0.97 % | 158 c, 0.93 % | 151 c, 0.93 % |
| multires districts (0.002, 0.004) | 323 c, 0.37 % | 234 c, 0.39 % | 205 c, 0.4 % | 340 s, 0.44 % |
| multires states (0.002, 0.004) | 261 c, 0.26 % | 75 c, 0.17 % | 75 c, 0.17 % | 75 c, 0.17 % |

Sum of iterations: constant 914, cf 0.8 599, cf 0.9 589, cf 1.0 711

## districts grid 128, single level, 4 tolerances x 4 dt

| case | constant | cf 0.8 | cf 0.9 | cf 1.0 |
|---|---|---|---|---|
| districts 128 default dt 0.15 | 167 c, 8.92 % | 167 c, 8.92 % | 167 c, 8.92 % | 167 c, 8.92 % |
| districts 128 default dt 0.2 | 118 c, 9.77 % | 118 c, 9.89 % | 118 c, 9.77 % | 118 c, 9.77 % |
| districts 128 default dt 0.3 | 140 s, 17.2 % | 150 s, 17.83 % | 150 s, 17.76 % | 150 s, 17.76 % |
| districts 128 default dt 0.4 | 110 s, 26.41 % | 110 s, 26.41 % | 110 s, 26.04 % | 110 s, 26.41 % |
| districts 128 (0.01, 0.02) dt 0.15 | 200 c, 2.02 % | 188 c, 1.73 % | 192 c, 1.73 % | 192 c, 1.73 % |
| districts 128 (0.01, 0.02) dt 0.2 | 135 c, 1.58 % | 141 c, 1.81 % | 134 c, 1.92 % | 142 c, 1.93 % |
| districts 128 (0.01, 0.02) dt 0.3 | 140 s, 17.2 % | 150 s, 19.33 % | 150 s, 18.8 % | 170 s, 18.32 % |
| districts 128 (0.01, 0.02) dt 0.4 | 110 s, 26.41 % | 110 s, 26.41 % | 120 s, 26.69 % | 110 s, 26.41 % |
| districts 128 (0.005, 0.01) dt 0.15 | 250 c, 0.96 % | 198 c, 0.83 % | 209 c, 0.99 % | 209 c, 0.94 % |
| districts 128 (0.005, 0.01) dt 0.2 | 183 c, 0.96 % | 149 c, 0.89 % | 143 c, 0.86 % | 143 c, 0.86 % |
| districts 128 (0.005, 0.01) dt 0.3 | 160 s, 17.2 % | 130 s, 20.86 % | 130 s, 20.86 % | 130 s, 20.68 % |
| districts 128 (0.005, 0.01) dt 0.4 | 140 s, 26.41 % | 130 s, 26.41 % | 170 s, 24.43 % | 130 s, 26.41 % |
| districts 128 (0.002, 0.004) dt 0.15 | 334 c, 0.38 % | 212 c, 0.38 % | 221 c, 0.31 % | 230 c, 0.38 % |
| districts 128 (0.002, 0.004) dt 0.2 | 259 c, 0.39 % | 181 c, 0.37 % | 171 c, 0.39 % | 173 c, 0.35 % |
| districts 128 (0.002, 0.004) dt 0.3 | 190 s, 17.2 % | 230 s, 16.45 % | 250 s, 15.96 % | 220 s, 15.83 % |
| districts 128 (0.002, 0.004) dt 0.4 | 140 s, 26.41 % | 210 s, 26.41 % | 140 s, 24.26 % | 210 s, 26.41 % |

Sum of iterations: constant 2776, cf 0.8 2574, cf 0.9 2575, cf 1.0 2604

## Late phase, states grid 256 (median, highest true max error % over the last 50 of 300 iterations)

| dt | recompute_on_rise | constant | cf 0.8 (adopted) | cf 0.9 | cf 1.0 |
|---|---|---|---|---|---|
| 0.2 | 0.01 | 0.81 / 2.00 | 0.12 / 0.29 | 0.12 / 0.29 | 0.21 / 0.45 |
| 0.4 | 0.01 | 2.37 / 6.22 | 0.23 / 0.70 | 0.23 / 0.70 | 0.23 / 0.70 |
| 0.2 | None | 5.32 / 14.54 | 0.73 / 1.88 | 0.68 / 1.87 | 0.92 / 2.46 |
| 0.4 | None | 8.72 / 19.55 | 1.19 / 3.11 | 1.19 / 3.11 | 1.19 / 3.11 |

