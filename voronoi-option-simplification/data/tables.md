## adjacency_spring (resolution 150, 60 iterations, no weights)

| adjacency_spring | fraction of input-adjacent pairs that stay adjacent |
|---|---|
| 0.0 | 0.661 |
| 0.1 | 0.697 |
| 0.3 | 0.725 |
| 0.6 | 0.826 |

## intra_group_spring with group_by (resolution 100, adjacency_spring 0.1, 60 iterations)

| group_by | intra_group_spring | discontiguous groups |
|---|---|---|
| Division | None | 3 |
| Division | 0.5 | 0 |
| Division | 1.0 | 0 |

## ElasticBoundary strength (resolution 120, 40 iterations)

| strength | area of the cell union / area of the input union |
|---|---|
| 0.0 | 1.000 |
| 0.05 | 1.025 |
| 0.3 | 1.010 |

## boundary (resolution 100, 20 iterations)

| boundary | union area / input union area | roundness 4 pi A / P^2 | share of the input covered |
|---|---|---|---|
| union | 1.00 | 0.07 | 1.000 |
| bbox | 1.69 | 0.76 | 1.000 |
| convex_hull | 1.35 | 0.83 | 1.000 |
| circle | 3.17 | 1.00 | 1.000 |

## simplify_tol (resolution 120, 10 iterations)

| simplify_tol (m) | vertices of the cell union |
|---|---|
| None | 14572 |
| 20000.0 | 3589 |
| 100000.0 | 3419 |
