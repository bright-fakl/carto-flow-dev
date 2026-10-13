| case | variant | status | iterations | recomputes | cost | seconds | true mean / max % | invalid | levels (grid, status, iterations) |
|---|---|---|---|---|---|---|---|---|---|
| states-area | baseline | converged | 193 | 40 | 673 | 1.3 | 0.86 / 2.7 | 6 | 64 stal 110, 128 stal 50, 256 conv 33 |
| states-area | cpp | converged | 55 | 17 | 259 | 0.4 | 0.33 / 2.7 | 2 | 64 stal 12, 128 stal 16, 256 conv 27 |
| states-area | p1-20 | converged | 166 | 22 | 430 | 0.5 | 0.31 / 2.9 | 5 | 64 stal 20, 128 stal 30, 256 conv 116 |
| states-area | p2-10 | converged | 153 | 36 | 585 | 0.5 | 0.86 / 2.7 | 6 | 64 stal 90, 128 stal 30, 256 conv 33 |
| states-area | budget | converged | 193 | 40 | 673 | 0.6 | 0.86 / 2.7 | 6 | 64 stal 110, 128 stal 50, 256 conv 33 |
| states-area | cpp+budget | converged | 55 | 17 | 259 | 0.4 | 0.33 / 2.7 | 2 | 64 stal 12, 128 stal 16, 256 conv 27 |
| states-lognormal2 | baseline | stalled | 270 | 124 | 1758 | 0.9 | 15.25 / 106.5 | 36 | 64 stal 160, 128 stal 50, 256 stal 60 |
| states-lognormal2 | cpp | completed | 516 | 56 | 1188 | 0.9 | 1.58 / 9.4 | 36 | 64 stal 8, 128 stal 8, 256 comp 500 |
| states-lognormal2 | p1-20 | converged | 383 | 53 | 1019 | 0.7 | 0.17 / 2.9 | 37 | 64 stal 20, 128 stal 20, 256 conv 343 |
| states-lognormal2 | p2-10 | stalled | 230 | 120 | 1670 | 0.8 | 15.25 / 106.5 | 36 | 64 stal 140, 128 stal 30, 256 stal 60 |
| states-lognormal2 | budget | stalled | 270 | 124 | 1758 | 0.9 | 15.25 / 106.5 | 36 | 64 stal 160, 128 stal 50, 256 stal 60 |
| states-lognormal2 | cpp+budget | completed | 516 | 56 | 1188 | 0.9 | 1.58 / 9.4 | 36 | 64 stal 8, 128 stal 8, 256 comp 500 |
| districts-smooth2 | baseline | stalled | 570 | 74 | 2272 | 3.4 | 4.26 / 44.8 | 121 | 128 stal 170, 256 stal 100, 512 stal 300 |
| districts-smooth2 | cpp | stalled | 296 | 42 | 1262 | 2.0 | 6.03 / 130.3 | 108 | 128 stal 8, 256 stal 8, 512 stal 280 |
| districts-smooth2 | p1-20 | stalled | 280 | 28 | 924 | 1.7 | 10.04 / 250.0 | 90 | 128 stal 20, 256 stal 20, 512 stal 240 |
| districts-smooth2 | p2-10 | stalled | 520 | 62 | 1946 | 2.4 | 3.41 / 43.3 | 111 | 128 stal 110, 256 stal 60, 512 stal 350 |
| districts-smooth2 | budget | stalled | 570 | 74 | 2272 | 2.6 | 4.26 / 44.8 | 121 | 128 stal 170, 256 stal 100, 512 stal 300 |
| districts-smooth2 | cpp+budget | stalled | 296 | 42 | 1262 | 2.1 | 6.03 / 130.3 | 108 | 128 stal 8, 256 stal 8, 512 stal 280 |
| districts-inverse | baseline | stalled | 490 | 70 | 2100 | 2.2 | 18.67 / 330.6 | 289 | 128 stal 230, 256 stal 140, 512 stal 120 |
| districts-inverse | cpp | stalled | 466 | 72 | 2122 | 2.9 | 4.84 / 130.3 | 172 | 128 stal 8, 256 stal 8, 512 stal 450 |
| districts-inverse | p1-20 | stalled | 460 | 55 | 1725 | 2.4 | 4.93 / 126.7 | 162 | 128 stal 20, 256 stal 20, 512 stal 420 |
| districts-inverse | p2-10 | stalled | 310 | 44 | 1322 | 1.8 | 14.99 / 265.5 | 283 | 128 stal 160, 256 stal 70, 512 stal 80 |
| districts-inverse | budget | stalled | 490 | 70 | 2100 | 2.6 | 18.67 / 330.6 | 289 | 128 stal 230, 256 stal 140, 512 stal 120 |
| districts-inverse | cpp+budget | stalled | 466 | 72 | 2122 | 3.1 | 4.84 / 130.3 | 172 | 128 stal 8, 256 stal 8, 512 stal 450 |
| districts-pop64 | baseline | converged | 229 | 36 | 877 | 1.4 | 0.18 / 2.6 | 109 | 64 stal 110, 128 conv 119 |
| districts-pop64 | cpp | stalled | 244 | 53 | 1463 | 2.9 | 0.97 / 18.0 | 61 | 64 stal 8, 128 stal 8, 256 stal 8, 512 stal 220 |
| districts-pop64 | p1-20 | converged | 169 | 30 | 709 | 1.5 | 0.18 / 2.6 | 109 | 64 stal 50, 128 conv 119 |
| districts-pop64 | p2-10 | converged | 189 | 32 | 765 | 1.2 | 0.18 / 2.6 | 109 | 64 stal 70, 128 conv 119 |
| districts-pop64 | budget | converged | 229 | 36 | 877 | 1.2 | 0.18 / 2.6 | 109 | 64 stal 110, 128 conv 119 |
| districts-pop64 | cpp+budget | stalled | 244 | 53 | 1463 | 2.1 | 0.97 / 18.0 | 61 | 64 stal 8, 128 stal 8, 256 stal 8, 512 stal 220 |
| counties | baseline | stalled | 990 | 99 | 24750 | 21.7 | 18.62 / 3076.1 | 139 | 512 stal 400, 1024 stal 280, 2048 stal 310 |
| counties | cpp | stalled | 66 | 7 | 1746 | 4.5 | 853.40 / 49411.7 | 2 | 512 stal 8, 1024 stal 8, 2048 stal 50 |
| counties | p1-20 | stalled | 90 | 9 | 2250 | 4.8 | 797.63 / 46128.5 | 4 | 512 stal 20, 1024 stal 20, 2048 stal 50 |
| counties | p2-10 | stalled | 110 | 11 | 2750 | 5.1 | 746.91 / 43146.3 | 4 | 512 stal 30, 1024 stal 30, 2048 stal 50 |
| counties | budget | completed | 600 | 60 | 15000 | 10.7 | 18.62 / 3076.1 | 139 | 512 stal 400, 1024 comp 50, 2048 comp 150 |
| counties | cpp+budget | stalled | 66 | 7 | 1746 | 4.5 | 853.40 / 49411.7 | 2 | 512 stal 8, 1024 stal 8, 2048 stal 50 |
| states-area | max-cpp | converged | 47 | 16 | 239 | 1.9 | 0.33 / 2.7 | 2 | 64 stal 8, 128 stal 12, 256 conv 27 |
| states-area | max-p1-20 | converged | 166 | 22 | 430 | 0.5 | 0.31 / 2.9 | 5 | 64 stal 20, 128 stal 30, 256 conv 116 |
| states-area | max-p2-10 | converged | 133 | 34 | 541 | 0.6 | 0.86 / 2.7 | 6 | 64 stal 70, 128 stal 30, 256 conv 33 |
| states-lognormal2 | max-cpp | completed | 516 | 56 | 1188 | 0.9 | 1.58 / 9.4 | 36 | 64 stal 8, 128 stal 8, 256 comp 500 |
| states-lognormal2 | max-p1-20 | converged | 383 | 53 | 1019 | 0.9 | 0.17 / 2.9 | 37 | 64 stal 20, 128 stal 20, 256 conv 343 |
| states-lognormal2 | max-p2-10 | converged | 297 | 41 | 789 | 0.8 | 0.72 / 3.0 | 39 | 64 stal 30, 128 stal 80, 256 conv 187 |
| districts-smooth2 | max-cpp | stalled | 296 | 42 | 1262 | 3.2 | 6.03 / 130.3 | 108 | 128 stal 8, 256 stal 8, 512 stal 280 |
| districts-smooth2 | max-p1-20 | stalled | 280 | 28 | 924 | 2.3 | 10.04 / 250.0 | 90 | 128 stal 20, 256 stal 20, 512 stal 240 |
| districts-smooth2 | max-p2-10 | stalled | 280 | 32 | 1016 | 2.4 | 7.07 / 96.2 | 91 | 128 stal 30, 256 stal 30, 512 stal 220 |
| districts-inverse | max-cpp | stalled | 466 | 72 | 2122 | 3.2 | 4.84 / 130.3 | 172 | 128 stal 8, 256 stal 8, 512 stal 450 |
| districts-inverse | max-p1-20 | stalled | 460 | 55 | 1725 | 2.4 | 4.93 / 126.7 | 162 | 128 stal 20, 256 stal 20, 512 stal 420 |
| districts-inverse | max-p2-10 | stalled | 420 | 57 | 1731 | 2.6 | 5.06 / 137.3 | 161 | 128 stal 30, 256 stal 30, 512 stal 360 |
| districts-pop64 | max-cpp | stalled | 244 | 53 | 1463 | 2.3 | 0.97 / 18.0 | 61 | 64 stal 8, 128 stal 8, 256 stal 8, 512 stal 220 |
| districts-pop64 | max-p1-20 | stalled | 220 | 60 | 1600 | 2.3 | 0.33 / 13.6 | 69 | 64 stal 20, 128 stal 20, 256 stal 20, 512 stal 160 |
| districts-pop64 | max-p2-10 | stalled | 200 | 90 | 2270 | 2.5 | 0.23 / 3.5 | 80 | 64 stal 30, 128 stal 30, 256 stal 90, 512 stal 50 |
| counties | max-cpp | stalled | 66 | 7 | 1746 | 7.0 | 853.40 / 49411.7 | 2 | 512 stal 8, 1024 stal 8, 2048 stal 50 |
| counties | max-p1-20 | stalled | 90 | 9 | 2250 | 5.1 | 797.63 / 46128.5 | 4 | 512 stal 20, 1024 stal 20, 2048 stal 50 |
| counties | max-p2-10 | stalled | 110 | 11 | 2750 | 5.2 | 746.91 / 43146.3 | 4 | 512 stal 30, 1024 stal 30, 2048 stal 50 |
