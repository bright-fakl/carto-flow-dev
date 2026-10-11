Adjacency of the cells against the original polygons and against the flow map (all pairs; for the districts, pairs inside one state):

| input | pairs | morph keeps of the original | cells keep of the original | cells keep of the morph | new pairs in the cells (not in the morph) |
|---|---|---|---|---|---|
| states | all, 109 | 1.000 | 0.789 | 0.789 | 31 |
| districts | all, 1133 | 1.000 | 0.600 | 0.601 | 500 |
| districts | within a state, 814 | 1.000 | 0.636 | 0.637 | 220 |

Group cohesion of the districts by state (metrics that do not depend on which cells are neighbors), flow map polygons against cells:

| layout | largest piece | solidity | neighbor purity | compactness |
|---|---|---|---|---|
| flow map (the premorph's own polygons) | 0.993 | 0.760 | 0.702 | 0.191 |
| premorph cells, anchor 0.25 | 0.977 | 0.752 | 0.656 | 0.718 |
| fixed outline, no spring | 0.848 | 0.610 | 0.520 | 0.805 |
| fixed outline, intra_group_spring 0.5 | 0.990 | 0.748 | 0.635 | 0.771 |
| elastic boundary, intra_group_spring 0.5 | 0.973 | 0.760 | 0.656 | 0.765 |
