| input | tiling | wall old / new (s) | calibrate old / new | hungarian old / new | ring relocation old / new | chain swap old / new | _count_split_units calls old / new |
|---|---|---|---|---|---|---|---|
| grid-10x10 | hexagon | 1.06 / 0.58 | 0.63 / 0.29 | 0.18 / 0.17 | 0.15 / 0.02 | 0.00 / 0.00 | 244 / 37 |
| grid-10x10 | square | 0.67 / 0.51 | 0.41 / 0.22 | 0.16 / 0.21 | 0.01 / 0.00 | 0.00 / 0.00 | 22 / 4 |
| districts | hexagon | 3.49 / 7.21 | 0.71 / 0.84 | 1.40 / 1.29 | 0.06 / 0.19 | 0.12 / 3.64 | 120 / 438 |
| districts | square | 5.69 / 5.00 | 2.71 / 2.34 | 1.25 / 1.24 | 0.07 / 0.03 | 0.51 / 0.30 | 166 / 68 |
| states | hexagon | 1.08 / 1.88 | 0.30 / 1.11 | 0.33 / 0.31 | 0.01 / 0.04 | 0.02 / 0.00 | 47 / 163 |
| states | square | 0.95 / 0.92 | 0.29 / 0.27 | 0.27 / 0.28 | 0.03 / 0.01 | 0.01 / 0.00 | 104 / 28 |
| texas | hexagon | 2.36 / 1.06 | 1.52 / 0.20 | 0.48 / 0.49 | 0.06 / 0.08 | 0.00 / 0.00 | 45 / 76 |
| texas | square | 1.12 / 0.98 | 0.22 / 0.17 | 0.54 / 0.49 | 0.06 / 0.04 | 0.00 / 0.01 | 50 / 29 |
| districts-division | hexagon | 3.29 / 3.44 | 0.70 / 0.72 | 1.28 / 1.41 | 0.03 / 0.04 | 0.00 / 0.00 | 52 / 58 |
| districts-division | square | 5.31 / 4.90 | 2.79 / 2.35 | 1.36 / 1.33 | 0.05 / 0.07 | 0.00 / 0.01 | 96 / 150 |

| input | tiling | lattice tiles | hungarian passes | ring tiles relocated | contiguity passes / swaps | chain swap before -> after | noncontiguous regions | split groups | unassigned core | enclosed |
|---|---|---|---|---|---|---|---|---|---|---|
| grid-10x10 | hexagon | 740 / 739 | 2 / 2 | 24 / 32 | 2/3 / 1/4 | [0, 2]->[0, 0] accepted / [0, 4]->[0, 0] accepted | 0 / 0 | 0 / 0 | 0 / 24 | 0 / 0 |
| grid-10x10 | square | 784 / 784 | 2 / 3 | 14 / 0 | 2/14 / 1/12 | [0, 5]->[0, 0] accepted / [0, 4]->[0, 0] accepted | 0 / 0 | 0 / 0 | 26 / 0 | 0 / 0 |
| districts | hexagon | 1178 / 1163 | 4 / 3 | 24 / 18 | 6/51 / 10/93 | [12, 0]->[0, 0] accepted / [9, 0]->[1, 0] accepted | 0 / 0 | 0 / 1 | 14 / 13 | 0 / 0 |
| districts | square | 1230 / 1260 | 3 / 3 | 25 / 27 | 10/247 / 10/210 | [21, 0]->[1, 0] accepted / [16, 0]->[2, 0] accepted | 0 / 0 | 1 / 2 | 4 / 6 | 0 / 0 |
| states | hexagon | 470 / 447 | 4 / 2 | 9 / 10 | 4/29 / 1/7 | [0, 5]->[0, 0] accepted / [0, 4]->[0, 0] accepted | 0 / 0 | 0 / 0 | 3 / 10 | 0 / 0 |
| states | square | 475 / 520 | 2 / 2 | 12 / 11 | 3/31 / 1/14 | [0, 6]->[0, 0] accepted / [0, 6]->[0, 0] accepted | 0 / 0 | 0 / 0 | 2 / 1 | 0 / 0 |
| texas | hexagon | 1872 / 1809 | 2 / 2 | 22 / 24 | 1/4 / 2/13 | [0, 2]->[0, 0] accepted / [0, 7]->[0, 0] accepted | 0 / 0 | 0 / 0 | 6 / 9 | 0 / 0 |
| texas | square | 1935 / 2024 | 2 / 2 | 24 / 24 | 1/22 / 1/22 | [0, 12]->[0, 2] accepted / [0, 10]->[0, 2] accepted | 2 / 2 | 0 / 0 | 11 / 13 | 0 / 0 |
| districts-division | hexagon | 1178 / 1163 | 3 / 4 | 22 / 18 | 1/2 / 0/0 | [1, 0]->[0, 0] accepted / - | 0 / 0 | 0 / 0 | 16 / 13 | 0 / 0 |
| districts-division | square | 1230 / 1260 | 3 / 3 | 25 / 27 | 2/5 / 0/0 | [3, 0]->[1, 0] accepted / [1, 0]->[1, 0] rejected | 0 / 0 | 1 / 1 | 4 / 6 | 0 / 0 |
