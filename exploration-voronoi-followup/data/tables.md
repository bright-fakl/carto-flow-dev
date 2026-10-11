| base | prescale | iterations | converged | mean error % | max error % | AK area / target | HI area / target | adjacency kept | time s |
|---|---|---|---|---|---|---|---|---|---|
| F | off | 300 | False | 45.45 | 550.1 | 2.58 | 0.42 | 0.32 | 10.7 |
| F | on | 189 | True | 0.00 | 0.0 | 1.00 | 1.00 | 0.51 | 3.8 |
| E | off | 300 | False | 24.52 | 99.2 | 0.92 | 0.40 | 0.36 | 22.1 |
| E | on | 300 | False | 9.35 | 79.1 | 0.21 | 0.47 | 0.41 | 19.1 |
| P | off | 300 | False | 1.93 | 10.7 | 1.10 | 1.00 | 0.79 | 8.1 |
| P | on | 70 | True | 0.00 | 0.0 | 1.00 | 1.00 | 0.81 | 2.7 |
| P | morph on | 104 | False | 3.49 | 26.6 | 1.00 | 1.00 | 0.79 | 4.6 |
| P | morph on + cells on | 94 | True | 0.00 | 0.0 | 1.00 | 1.00 | 0.79 | 3.2 |

| data | anchor | iterations | TX inside morphed region | TX shift | LA shift | split cells | adjacency kept | compactness | d_flow | time s |
|---|---|---|---|---|---|---|---|---|---|---|
| D | 0 | 12 | 0.94 | 5.41 | 5.04 | 38 | 0.57 | 0.75 | 0.35 | 2.4 |
| D | 0.25 | 9 | 0.95 | 5.36 | 5.05 | 41 | 0.60 | 0.72 | 0.25 | 2.2 |
| D | 0.5 | 9 | 0.96 | 5.36 | 5.07 | 43 | 0.61 | 0.69 | 0.21 | 2.2 |
| S | 0 | 53 | 0.73 | 1.84 | 2.93 | 3 | 0.59 | 0.58 | 0.44 | 1.0 |
| S | 0.25 | 43 | 0.88 | 1.47 | 1.62 | 4 | 0.79 | 0.57 | 0.19 | 0.9 |
| S | 0.5 | 53 | 0.89 | 1.50 | 1.66 | 5 | 0.80 | 0.55 | 0.16 | 0.9 |

| base | setting | iterations | states whole | within-state adj | between-state adj | all adj kept | compactness | time s |
|---|---|---|---|---|---|---|---|---|
| F | intra_group_spring off | 185 | 0.54 | 0.45 | 0.38 | 0.43 | 0.81 | 12.9 |
| F | intra_group_spring 0.25 | 94 | 0.77 | 0.56 | 0.26 | 0.48 | 0.78 | 7.8 |
| F | intra_group_spring 0.5 | 101 | 0.94 | 0.64 | 0.25 | 0.53 | 0.77 | 8.8 |
| F | intra_group_spring 1 | 108 | 1.00 | 0.75 | 0.20 | 0.59 | 0.77 | 9.3 |
| F | intra_group_spring 0.5 + adj 0.1 | 103 | 0.83 | 0.61 | 0.33 | 0.53 | 0.77 | 9.3 |
| F | adjacency_spring 0.1 | 173 | 0.52 | 0.44 | 0.45 | 0.44 | 0.79 | 13.3 |
| E | intra_group_spring off | 300 | 0.42 | 0.39 | 0.36 | 0.38 | 0.79 | 16.8 |
| E | intra_group_spring 0.25 | 300 | 0.73 | 0.59 | 0.24 | 0.49 | 0.78 | 19.2 |
| E | intra_group_spring 0.5 | 300 | 0.83 | 0.66 | 0.23 | 0.54 | 0.76 | 19.2 |
| E | intra_group_spring 1 | 300 | 0.90 | 0.75 | 0.19 | 0.59 | 0.75 | 20.6 |
| E | intra_group_spring 0.5 + adj 0.1 | 300 | 0.92 | 0.67 | 0.30 | 0.57 | 0.77 | 19.2 |
| E | adjacency_spring 0.1 | 300 | 0.52 | 0.48 | 0.44 | 0.47 | 0.79 | 18.0 |
| P | intra_group_spring off | 9 | 0.85 | 0.64 | 0.51 | 0.61 | 0.69 | 2.6 |
| P | intra_group_spring 0.25 | 10 | 0.81 | 0.65 | 0.50 | 0.61 | 0.69 | 3.3 |
| P | intra_group_spring 0.5 | 13 | 0.85 | 0.66 | 0.50 | 0.62 | 0.69 | 3.3 |
| P | intra_group_spring 1 | 300 | 0.88 | 0.69 | 0.48 | 0.63 | 0.68 | 29.2 |
| P | intra_group_spring 0.5 + adj 0.1 | 14 | 0.83 | 0.66 | 0.50 | 0.62 | 0.69 | 3.5 |
| P | adjacency_spring 0.1 | 10 | 0.83 | 0.64 | 0.52 | 0.61 | 0.69 | 3.1 |
