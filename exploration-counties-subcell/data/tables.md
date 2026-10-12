## Targets below one grid cell

Votes range from 66 to 4263443 (median 12528); the target area of a county is its share of the total area.

| grid | counties with a target area below one cell | below 0.1 cell |
|---|---|---|
| 256 | 2093 (67 %) | 296 |
| 512 | 852 (27 %) | 30 |
| 1024 | 164 (5 %) | 1 |
| 2048 | 8 (0 %) | 0 |

## Single-level runs (stall rule on, 300 iterations)

| grid | status, iterations | true mean / max error % | regions with target < 1 cell: count, median error % | other regions: median error %, max error % | regions off by > 10 % (of which target < 1 cell) | invalid output regions |
|---|---|---|---|---|---|---|
| 256 | stalled, 210 | 66.7 / 5738 | 2093, 43 | 12.1, 206 | 2366 (1802) | 7 |
| 512 | completed, 300 | 20.6 / 1273 | 852, 28 | 2.6, 162 | 1143 (654) | 51 |
| 1024 | stalled, 50 | 853.4 / 49408 | 164, 5338 | 118.7, 20920 | 2994 (164) | 2 |

## Multiresolution (128 to 1024, 4 levels)

Levels: stalled 120, stalled 120, stalled 140, stalled 110; true mean 22.1 %, max 3594 %, 1066 regions off by more than 10 % (11 s).

## Stall rule off, grid 512 (reported mean / max error % at iteration)

| 1 | 50 | 100 | 200 | 300 | 500 | 800 | 1200 | 1500 |
|---|---|---|---|---|---|---|---|---|
| 370.6 / 53342 | 294.6 / 45089 | 230.3 / 34919 | 111.5 / 13776 | 15.8 / 2001 | 11.7 / 963 | 9.3 / 5351 | 9.2 / 5351 | 10.5 / 7078 |

## Worst regions, grid 512 (stall rule on)

| county | error % | target (cells) | area (cells) |
|---|---|---|---|
| 48261 | 1273 | 0.033 | 0.45 |
| 31007 | 788 | 0.070 | 0.62 |
| 48301 | 734 | 0.011 | 0.09 |
| 48033 | 722 | 0.071 | 0.58 |
| 48269 | 667 | 0.027 | 0.21 |
| 48173 | 497 | 0.111 | 0.66 |
| 31165 | 484 | 0.125 | 0.73 |
| 48137 | 456 | 0.182 | 1.01 |

Sub-cell regions: target 458 cells in total, actual 557 cells; all other regions: target 26412, actual 26313. Regions with a target of at least one cell and an error above 10 %: 489 of 2256 (median error of that group 2.6 %).
