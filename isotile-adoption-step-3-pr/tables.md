| tiling | position | rotation | version | mean distance | largest distance | lattice tiles | seconds |
|---|---|---|---|---|---|---|---|
| hexagon | centered | 0 | main | 1.262 | 3.10 | 149 | 1.61 |
| hexagon | centered | 0 | this PR | 1.262 | 3.10 | 149 | 1.63 |
| hexagon | centered | 30 | main | 1.270 | 3.48 | 149 | 1.61 |
| hexagon | centered | 30 | this PR | 1.185 | 3.50 | 143 | 1.57 |
| hexagon | moved | 0 | main | 1.262 | 3.10 | 149 | 1.61 |
| hexagon | moved | 0 | this PR | 1.262 | 3.10 | 149 | 1.57 |
| hexagon | moved | 30 | main | 12.057 | 16.37 | 149 | 1.62 |
| hexagon | moved | 30 | this PR | 1.185 | 3.50 | 143 | 1.53 |
| square | centered | 0 | main | 0.956 | 2.42 | 160 | 1.66 |
| square | centered | 0 | this PR | 0.956 | 2.42 | 160 | 1.71 |
| square | centered | 30 | main | 0.886 | 1.81 | 160 | 1.67 |
| square | centered | 30 | this PR | 0.808 | 2.19 | 174 | 1.83 |
| square | moved | 0 | main | 0.956 | 2.42 | 160 | 1.68 |
| square | moved | 0 | this PR | 0.956 | 2.42 | 160 | 1.71 |
| square | moved | 30 | main | 7.388 | 9.95 | 160 | 1.70 |
| square | moved | 30 | this PR | 0.808 | 2.19 | 174 | 1.91 |

| layout | tiling | offset | mean distance | largest distance | unassigned core | noncontiguous | seconds |
|---|---|---|---|---|---|---|---|
| grid | hexagon | (0.0, 0.0) | 1.262 | 3.10 |  |  | 1.71 |
| grid | hexagon | (0.25, 0.25) | 1.415 | 3.34 |  |  | 1.70 |
| grid | hexagon | (0.5, 0.5) | 1.330 | 3.14 |  |  | 1.06 |
| mosaic | hexagon | (0.0, 0.0) | 3.375 | 6.33 | 10 | 0 | 1.81 |
| mosaic | hexagon | (0.25, 0.25) | 3.558 | 6.45 | 4 | 0 | 1.12 |
| mosaic | hexagon | (0.5, 0.5) | 3.602 | 7.47 | 5 | 0 | 1.05 |
| grid | square | (0.0, 0.0) | 0.956 | 2.42 |  |  | 1.73 |
| grid | square | (0.25, 0.25) | 0.956 | 2.38 |  |  | 1.71 |
| grid | square | (0.5, 0.5) | 0.758 | 2.24 |  |  | 1.72 |
| mosaic | square | (0.0, 0.0) | 2.551 | 5.85 | 1 | 0 | 0.90 |
| mosaic | square | (0.25, 0.25) | 2.522 | 5.78 | 4 | 0 | 0.93 |
| mosaic | square | (0.5, 0.5) | 2.248 | 4.87 | 5 | 0 | 0.93 |

| position | mean distance | largest distance | unassigned core | noncontiguous | seconds |
|---|---|---|---|---|---|
| centered | 3.544 | 6.81 | 6 | 0 | 1.76 |
| moved | 3.544 | 6.81 | 6 | 0 | 1.75 |

| tiling | rotation | mean distance | unassigned core | noncontiguous | seconds |
|---|---|---|---|---|---|
| square | 0 | 0.530 | 0 | 0 | 0.52 |
| square | 15 | 0.668 | 3 | 0 | 0.43 |
| square | 30 | 0.622 | 0 | 0 | 0.31 |
| square | 45 | 0.725 | 0 | 0 | 0.38 |
| hexagon | 0 | 0.799 | 24 | 0 | 0.57 |
| hexagon | 15 | 0.858 | 7 | 0 | 0.48 |
| hexagon | 30 | 0.765 | 24 | 0 | 0.57 |
| hexagon | 45 | 0.949 | 1 | 0 | 0.36 |

square: unassigned core tiles over the 5 x 5 scan: min 0, max 28, default 0, offset of the minimum (0.0, 0.0)
hexagon: unassigned core tiles over the 5 x 5 scan: min 0, max 27, default 24, offset of the minimum (0.4, 0.2)
