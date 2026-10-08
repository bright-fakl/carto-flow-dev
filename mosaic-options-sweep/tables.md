Runs: 670 successful, 0 errors.

## Identity groups (dead zones)

Values whose full assignment fingerprint is byte-identical. `*` marks the group containing the default.

| knob | case | morph | identical groups |
|---|---|---|---|
| outside_penalty | states_uniform | True | {0.0, 0.25} {0.5} {2.0} {4.0} {10.0} {1.0}* |
| outside_penalty | states_uniform | False | {0.0} {0.25} {0.5} {2.0} {4.0} {10.0} {1.0}* |
| outside_penalty | states_uniform_sq | True | {0.0, 0.25, 0.5} {1.0, 2.0}* {4.0} {10.0} |
| outside_penalty | states_uniform_sq | False | {0.0} {0.25} {0.5} {2.0} {4.0} {10.0} {1.0}* |
| outside_penalty | states | True | {0.0} {0.25} {0.5} {2.0} {4.0} {10.0} {1.0}* |
| outside_penalty | states | False | {0.0} {0.25} {0.5} {2.0} {4.0} {10.0} {1.0}* |
| outside_penalty | districts | True | {0.0} {0.25} {0.5} {2.0} {4.0} {10.0} {1.0}* |
| outside_penalty | districts | False | {0.0} {0.25} {0.5} {2.0} {4.0} {10.0} {1.0}* |
| outside_penalty | world | True | {0.0} {0.25} {0.5} {2.0} {4.0} {10.0} {1.0}* |
| outside_penalty | world | False | {0.0} {0.25} {0.5} {2.0} {4.0} {10.0} {1.0}* |
| max_connectivity_iters | states_uniform | True | {0, 1, 2, 5, 15, 30}* |
| max_connectivity_iters | states_uniform | False | {0, 1, 2, 5, 15, 30}* |
| max_connectivity_iters | states_uniform_sq | True | {0, 1, 2, 5, 15, 30}* |
| max_connectivity_iters | states_uniform_sq | False | {0} {1, 2, 5, 15, 30}* |
| max_connectivity_iters | states | True | {0, 1, 2, 5, 15, 30}* |
| max_connectivity_iters | states | False | {0} {1} {2, 5, 15, 30}* |
| max_connectivity_iters | districts | True | {0, 1, 2, 5, 15, 30}* |
| max_connectivity_iters | districts | False | {0} {1} {2, 5, 15, 30}* |
| max_connectivity_iters | world | True | {0, 1, 2, 5, 15, 30}* |
| max_connectivity_iters | world | False | {0, 1, 2, 5, 15, 30}* |
| disconnected_penalty_mult | states_uniform | True | {0.0, 1.0, 2.0, 5.0, 10.0, 50.0}* |
| disconnected_penalty_mult | states_uniform | False | {0.0, 1.0, 2.0, 5.0, 10.0, 50.0}* |
| disconnected_penalty_mult | states_uniform_sq | True | {0.0, 1.0, 2.0, 5.0, 10.0, 50.0}* |
| disconnected_penalty_mult | states_uniform_sq | False | {0.0, 1.0, 2.0, 5.0, 10.0, 50.0}* |
| disconnected_penalty_mult | states | True | {0.0, 1.0, 2.0, 5.0, 10.0, 50.0}* |
| disconnected_penalty_mult | states | False | {0.0} {1.0, 2.0, 5.0, 10.0, 50.0}* |
| disconnected_penalty_mult | districts | True | {0.0, 1.0, 2.0, 5.0, 10.0, 50.0}* |
| disconnected_penalty_mult | districts | False | {0.0} {1.0, 2.0, 5.0, 10.0, 50.0}* |
| disconnected_penalty_mult | world | True | {0.0, 1.0, 2.0, 5.0, 10.0, 50.0}* |
| disconnected_penalty_mult | world | False | {0.0, 1.0, 2.0, 5.0, 10.0, 50.0}* |
| gap_bridge_mult | states_uniform | True | {0.0, 1.0, 2.0, 5.0, 20.0}* |
| gap_bridge_mult | states_uniform | False | {0.0, 1.0, 2.0, 5.0, 20.0}* |
| gap_bridge_mult | states_uniform_sq | True | {0.0, 1.0, 2.0, 5.0, 20.0}* |
| gap_bridge_mult | states_uniform_sq | False | {0.0, 1.0, 2.0, 5.0, 20.0}* |
| gap_bridge_mult | states | True | {0.0, 1.0, 2.0, 5.0, 20.0}* |
| gap_bridge_mult | states | False | {0.0, 1.0, 2.0, 5.0, 20.0}* |
| gap_bridge_mult | districts | True | {0.0, 1.0, 2.0, 5.0, 20.0}* |
| gap_bridge_mult | districts | False | {0.0, 1.0, 2.0, 5.0, 20.0}* |
| gap_bridge_mult | world | True | {0.0, 1.0, 2.0, 5.0, 20.0}* |
| gap_bridge_mult | world | False | {0.0, 1.0, 2.0, 5.0, 20.0}* |
| disconnected_score_weight | states_uniform | True | {0, 1, 10, 100, 1000}* |
| disconnected_score_weight | states_uniform | False | {0, 1, 10, 100, 1000}* |
| disconnected_score_weight | states_uniform_sq | True | {0, 1, 10, 100, 1000}* |
| disconnected_score_weight | states_uniform_sq | False | {0, 1, 10, 100, 1000}* |
| disconnected_score_weight | states | True | {0, 1, 10, 100, 1000}* |
| disconnected_score_weight | states | False | {0, 1, 10, 100, 1000}* |
| disconnected_score_weight | districts | True | {0, 1, 10, 100, 1000}* |
| disconnected_score_weight | districts | False | {0, 1, 10, 100, 1000}* |
| disconnected_score_weight | world | True | {0, 1, 10, 100, 1000}* |
| disconnected_score_weight | world | False | {0, 1, 10, 100, 1000}* |
| swap_repair_passes | states_uniform | True | {0, 1, 2, 5, 10, 30}* |
| swap_repair_passes | states_uniform | False | {0, 1, 2, 5, 10, 30}* |
| swap_repair_passes | states_uniform_sq | True | {0, 1, 2, 5, 10, 30}* |
| swap_repair_passes | states_uniform_sq | False | {0, 1, 2, 5, 10, 30}* |
| swap_repair_passes | states | True | {0, 1, 2, 5, 10, 30}* |
| swap_repair_passes | states | False | {0} {1} {2} {5, 10, 30}* |
| swap_repair_passes | districts | True | {0} {1} {2, 5, 10, 30}* |
| swap_repair_passes | districts | False | {0} {1} {2} {5} {10, 30}* |
| swap_repair_passes | world | True | {0} {1} {2, 5, 10, 30}* |
| swap_repair_passes | world | False | {0} {1} {2} {5, 10, 30}* |
| ring_swapback_max_hops | states_uniform | True | {0} {1, 2} {4} {8, 16, 32}* |
| ring_swapback_max_hops | states_uniform | False | {0} {1} {2} {4} {8} {16, 32}* |
| ring_swapback_max_hops | states_uniform_sq | True | {0} {1} {2} {4} {8, 16, 32}* |
| ring_swapback_max_hops | states_uniform_sq | False | {0} {1} {2} {4} {8, 16, 32}* |
| ring_swapback_max_hops | states | True | {0} {1} {2} {4} {8} {16, 32}* |
| ring_swapback_max_hops | states | False | {0} {1} {2} {4} {8} {16, 32}* |
| ring_swapback_max_hops | districts | True | {0} {1} {2} {4} {8} {32} {16}* |
| ring_swapback_max_hops | districts | False | {0} {1} {2} {4} {8} {32} {16}* |
| ring_swapback_max_hops | world | True | {0} {1} {2} {4} {8} {32} {16}* |
| ring_swapback_max_hops | world | False | {0} {1} {2} {4} {8} {32} {16}* |
| distance_x_outside | states_uniform | True | {dw=0.25,op=0.0} {dw=0.25,op=0.5} {dw=0.25,op=1.0} {dw=0.25,op=2.0} {dw=0.25,op=4.0} {dw=1.0,op=0.0} {dw=1.0,op=0.5} {dw=1.0,op=2.0} {dw=1.0,op=4.0} {dw=4.0,op=0.0} {dw=4.0,op=0.5} {dw=4.0,op=1.0} {dw=4.0,op=2.0} {dw=4.0,op=4.0} |
| distance_x_outside | states_uniform | False | {dw=0.25,op=0.0} {dw=0.25,op=0.5} {dw=0.25,op=1.0} {dw=0.25,op=2.0} {dw=0.25,op=4.0} {dw=1.0,op=0.0} {dw=1.0,op=0.5} {dw=1.0,op=2.0} {dw=1.0,op=4.0} {dw=4.0,op=0.0} {dw=4.0,op=0.5} {dw=4.0,op=1.0} {dw=4.0,op=2.0} {dw=4.0,op=4.0} |
| distance_x_outside | states_uniform_sq | True | {dw=0.25,op=0.0, dw=0.25,op=0.5} {dw=0.25,op=1.0, dw=0.25,op=2.0} {dw=0.25,op=4.0} {dw=1.0,op=0.0, dw=1.0,op=0.5} {dw=1.0,op=2.0}* {dw=1.0,op=4.0} {dw=4.0,op=0.0, dw=4.0,op=0.5} {dw=4.0,op=1.0} {dw=4.0,op=2.0} {dw=4.0,op=4.0} |
| distance_x_outside | states_uniform_sq | False | {dw=0.25,op=0.0} {dw=0.25,op=0.5} {dw=0.25,op=1.0} {dw=0.25,op=2.0} {dw=0.25,op=4.0} {dw=1.0,op=0.0} {dw=1.0,op=0.5} {dw=1.0,op=2.0} {dw=1.0,op=4.0} {dw=4.0,op=0.0} {dw=4.0,op=0.5} {dw=4.0,op=1.0} {dw=4.0,op=2.0} {dw=4.0,op=4.0} |
| distance_x_outside | states | True | {dw=0.25,op=0.0} {dw=0.25,op=0.5} {dw=0.25,op=1.0} {dw=0.25,op=2.0} {dw=0.25,op=4.0} {dw=1.0,op=0.0} {dw=1.0,op=0.5} {dw=1.0,op=2.0} {dw=1.0,op=4.0} {dw=4.0,op=0.0} {dw=4.0,op=0.5} {dw=4.0,op=1.0} {dw=4.0,op=2.0} {dw=4.0,op=4.0} |
| distance_x_outside | states | False | {dw=0.25,op=0.0} {dw=0.25,op=0.5} {dw=0.25,op=1.0} {dw=0.25,op=2.0} {dw=0.25,op=4.0} {dw=1.0,op=0.0} {dw=1.0,op=0.5} {dw=1.0,op=2.0} {dw=1.0,op=4.0} {dw=4.0,op=0.0} {dw=4.0,op=0.5} {dw=4.0,op=1.0} {dw=4.0,op=2.0} {dw=4.0,op=4.0} |
| distance_x_outside | districts | True | {dw=0.25,op=0.0} {dw=0.25,op=0.5} {dw=0.25,op=1.0} {dw=0.25,op=2.0} {dw=0.25,op=4.0} {dw=1.0,op=0.0} {dw=1.0,op=0.5} {dw=1.0,op=2.0} {dw=1.0,op=4.0} {dw=4.0,op=0.0} {dw=4.0,op=0.5} {dw=4.0,op=1.0} {dw=4.0,op=2.0} {dw=4.0,op=4.0} |
| distance_x_outside | districts | False | {dw=0.25,op=0.0} {dw=0.25,op=0.5} {dw=0.25,op=1.0} {dw=0.25,op=2.0} {dw=0.25,op=4.0} {dw=1.0,op=0.0} {dw=1.0,op=0.5} {dw=1.0,op=2.0} {dw=1.0,op=4.0} {dw=4.0,op=0.0} {dw=4.0,op=0.5} {dw=4.0,op=1.0} {dw=4.0,op=2.0} {dw=4.0,op=4.0} |
| distance_x_outside | world | True | {dw=0.25,op=0.0} {dw=0.25,op=0.5} {dw=0.25,op=1.0} {dw=0.25,op=2.0} {dw=0.25,op=4.0} {dw=1.0,op=0.0} {dw=1.0,op=0.5} {dw=1.0,op=2.0} {dw=1.0,op=4.0} {dw=4.0,op=0.0} {dw=4.0,op=0.5} {dw=4.0,op=1.0} {dw=4.0,op=2.0} {dw=4.0,op=4.0} |
| distance_x_outside | world | False | {dw=0.25,op=0.0} {dw=0.25,op=0.5} {dw=0.25,op=1.0} {dw=0.25,op=2.0} {dw=0.25,op=4.0} {dw=1.0,op=0.0} {dw=1.0,op=0.5} {dw=1.0,op=2.0} {dw=1.0,op=4.0} {dw=4.0,op=0.0} {dw=4.0,op=0.5} {dw=4.0,op=1.0} {dw=4.0,op=2.0} {dw=4.0,op=4.0} |
| extra_tile_rings | states_uniform | True | {0} {2} {3} {5} {1}* |
| extra_tile_rings | states_uniform | False | {0} {2} {3} {5} {1}* |
| extra_tile_rings | states_uniform_sq | True | {0} {2} {3} {5} {1}* |
| extra_tile_rings | states_uniform_sq | False | {0} {2} {3} {5} {1}* |
| extra_tile_rings | states | True | {0} {2} {3} {5} {1}* |
| extra_tile_rings | states | False | {0} {2} {3} {5} {1}* |
| extra_tile_rings | districts | True | {0} {2} {3} {5} {1}* |
| extra_tile_rings | districts | False | {0} {2} {3} {5} {1}* |
| extra_tile_rings | world | True | {0} {2} {3} {5} {1}* |
| extra_tile_rings | world | False | {0} {2} {3} {5} {1}* |
| min_overlap_frac | states_uniform | True | {0.02} {0.25} {0.5} {0.75} {1.0} {0.1}* |
| min_overlap_frac | states_uniform | False | {0.02} {0.25} {0.5} {0.75} {1.0} {0.1}* |
| min_overlap_frac | states_uniform_sq | True | {0.02} {0.25} {0.5} {0.75} {1.0} {0.1}* |
| min_overlap_frac | states_uniform_sq | False | {0.02} {0.25} {0.5} {0.75} {1.0} {0.1}* |
| min_overlap_frac | states | True | {0.02} {0.25} {0.5} {0.75} {1.0} {0.1}* |
| min_overlap_frac | states | False | {0.02} {0.25} {0.5} {0.75} {1.0} {0.1}* |
| min_overlap_frac | districts | True | {0.02} {0.25} {0.5} {0.75} {1.0} {0.1}* |
| min_overlap_frac | districts | False | {0.02} {0.25} {0.5} {0.75} {1.0} {0.1}* |
| min_overlap_frac | world | True | {0.02} {0.25} {0.5} {0.75} {1.0} {0.1}* |
| min_overlap_frac | world | False | {0.02} {0.25} {0.5} {0.75} {1.0} {0.1}* |
| spacing | states_uniform | True | {0.0, 0.05, 0.2, 0.5}* |
| spacing | states_uniform | False | {0.0, 0.05, 0.2, 0.5}* |
| spacing | states_uniform_sq | True | {0.0, 0.05, 0.2, 0.5}* |
| spacing | states_uniform_sq | False | {0.0, 0.05, 0.2, 0.5}* |
| spacing | states | True | {0.0, 0.05, 0.2, 0.5}* |
| spacing | states | False | {0.0, 0.05, 0.2, 0.5}* |
| spacing | districts | True | {0.0, 0.05, 0.2, 0.5}* |
| spacing | districts | False | {0.0, 0.05, 0.2, 0.5}* |
| spacing | world | True | {0.0, 0.05, 0.2, 0.5}* |
| spacing | world | False | {0.0, 0.05, 0.2, 0.5}* |
| tile_size | states_uniform | True | {0.8} {0.9} {1.0}* {1.1} {1.25} |
| tile_size | states_uniform | False | {0.8} {0.9} {1.0}* {1.1} {1.25} |
| tile_size | states_uniform_sq | True | {0.8} {0.9} {1.0}* {1.1} {1.25} |
| tile_size | states_uniform_sq | False | {0.8} {0.9} {1.0}* {1.1} {1.25} |
| tile_size | states | True | {0.8} {0.9} {1.0}* {1.1} {1.25} |
| tile_size | states | False | {0.8} {0.9} {1.0}* {1.1} {1.25} |
| tile_size | districts | True | {0.8} {0.9} {1.0}* {1.1} {1.25} |
| tile_size | districts | False | {0.8} {0.9} {1.0}* {1.1} {1.25} |
| tile_size | world | True | {0.8} {0.9} {1.0}* {1.1} {1.25} |
| tile_size | world | False | {0.8} {0.9} {1.0}* {1.1} {1.25} |


## outside_penalty

| case | morph | value | disp | adj | dir | pp | iou | noncontig | split | unassigned_core | enclosed | short | wall_s | fp |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| states_uniform | True | 0.0 | 1.337 | 0.771 | 21.17 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 0.8 | `22582a` |
| states_uniform | True | 0.25 | 1.337 | 0.771 | 21.17 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 0.8 | `22582a` |
| states_uniform | True | 0.5 | 1.526 | 0.716 | 26.83 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 0.8 | `e37ae5` |
| states_uniform | True | 2.0 | 1.504 | 0.569 | 38.58 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 1.0 | `ab65c7` |
| states_uniform | True | 4.0 | 1.529 | 0.560 | 31.17 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 0.9 | `7e1c68` |
| states_uniform | True | 10.0 | 1.835 | 0.651 | 29.80 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 0.8 | `f42eb5` |
| states_uniform | True | None | 1.526 | 0.725 | 28.32 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 0.8 | `d4bfd1` |
| states_uniform | False | 0.0 | 2.305 | 0.642 | 26.47 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `d6b44d` |
| states_uniform | False | 0.25 | 2.580 | 0.624 | 32.32 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `899ff9` |
| states_uniform | False | 0.5 | 2.365 | 0.514 | 33.26 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `9fab23` |
| states_uniform | False | 2.0 | 2.690 | 0.688 | 29.81 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `3685aa` |
| states_uniform | False | 4.0 | 2.305 | 0.633 | 26.47 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `c7b93e` |
| states_uniform | False | 10.0 | 2.628 | 0.532 | 28.83 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `5a4b3c` |
| states_uniform | False | None | 2.238 | 0.523 | 34.23 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `db2447` |
| states_uniform_sq | True | 0.0 | 0.786 | 0.569 | 24.82 | 0.785 | 0.701 | 0 | 0 | 10 | 0 | 0 | 0.9 | `cc5407` |
| states_uniform_sq | True | 0.25 | 0.786 | 0.569 | 24.82 | 0.785 | 0.701 | 0 | 0 | 10 | 0 | 0 | 0.9 | `cc5407` |
| states_uniform_sq | True | 0.5 | 0.786 | 0.569 | 24.82 | 0.785 | 0.701 | 0 | 0 | 10 | 0 | 0 | 0.9 | `cc5407` |
| states_uniform_sq | True | 2.0 | 0.745 | 0.459 | 24.82 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 0.9 | `02f6d0` |
| states_uniform_sq | True | 4.0 | 0.877 | 0.450 | 32.32 | 0.785 | 0.659 | 0 | 0 | 11 | 0 | 0 | 0.9 | `bc5369` |
| states_uniform_sq | True | 10.0 | 1.075 | 0.477 | 32.32 | 0.785 | 0.635 | 0 | 0 | 11 | 0 | 0 | 1.0 | `5ff0cd` |
| states_uniform_sq | True | None | 0.745 | 0.459 | 24.82 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 1.0 | `02f6d0` |
| states_uniform_sq | False | 0.0 | 1.252 | 0.514 | 20.61 | 0.785 | 0.789 | 0 | 0 | 1 | 0 | 0 | 1.2 | `e658eb` |
| states_uniform_sq | False | 0.25 | 1.338 | 0.523 | 25.77 | 0.785 | 0.793 | 0 | 0 | 1 | 0 | 0 | 1.2 | `3fc64f` |
| states_uniform_sq | False | 0.5 | 1.408 | 0.486 | 31.68 | 0.785 | 0.793 | 0 | 0 | 1 | 0 | 0 | 1.5 | `0c0e98` |
| states_uniform_sq | False | 2.0 | 1.502 | 0.468 | 29.64 | 0.785 | 0.789 | 0 | 0 | 1 | 0 | 0 | 1.4 | `f91ff5` |
| states_uniform_sq | False | 4.0 | 1.704 | 0.385 | 34.25 | 0.785 | 0.784 | 0 | 0 | 1 | 0 | 0 | 1.3 | `163d72` |
| states_uniform_sq | False | 10.0 | 1.753 | 0.404 | 31.31 | 0.785 | 0.784 | 0 | 0 | 1 | 0 | 0 | 1.2 | `86f33c` |
| states_uniform_sq | False | None | 1.583 | 0.468 | 30.20 | 0.785 | 0.801 | 0 | 0 | 1 | 0 | 0 | 1.2 | `0fae83` |
| states | True | 0.0 | 2.555 | 0.817 | 14.27 | 0.666 | 0.699 | 0 | 0 | 17 | 0 | 0 | 1.3 | `0c6853` |
| states | True | 0.25 | 2.627 | 0.807 | 14.54 | 0.666 | 0.694 | 0 | 0 | 17 | 0 | 0 | 1.3 | `ca580b` |
| states | True | 0.5 | 2.562 | 0.826 | 14.93 | 0.666 | 0.684 | 0 | 0 | 19 | 0 | 0 | 1.5 | `07a773` |
| states | True | 2.0 | 2.576 | 0.743 | 15.31 | 0.653 | 0.694 | 0 | 0 | 17 | 0 | 0 | 1.3 | `53ecf8` |
| states | True | 4.0 | 2.576 | 0.706 | 17.15 | 0.653 | 0.675 | 0 | 0 | 18 | 0 | 0 | 1.4 | `115a9e` |
| states | True | 10.0 | 2.696 | 0.688 | 18.63 | 0.653 | 0.676 | 0 | 0 | 18 | 0 | 0 | 1.5 | `ab9cd6` |
| states | True | None | 2.099 | 0.798 | 17.11 | 0.653 | 0.687 | 0 | 0 | 19 | 0 | 0 | 1.3 | `febe8e` |
| states | False | 0.0 | 4.112 | 0.697 | 22.09 | 0.680 | 0.852 | 0 | 0 | 0 | 0 | 0 | 1.6 | `52f7e1` |
| states | False | 0.25 | 4.380 | 0.734 | 21.04 | 0.666 | 0.844 | 0 | 0 | 1 | 0 | 0 | 1.5 | `5659d7` |
| states | False | 0.5 | 4.259 | 0.725 | 20.65 | 0.653 | 0.834 | 0 | 0 | 3 | 0 | 0 | 1.5 | `a3f021` |
| states | False | 2.0 | 4.277 | 0.661 | 24.16 | 0.653 | 0.851 | 0 | 0 | 0 | 0 | 0 | 1.6 | `ad8bce` |
| states | False | 4.0 | 4.112 | 0.670 | 22.93 | 0.653 | 0.829 | 0 | 0 | 1 | 0 | 0 | 6.1 | `d52306` |
| states | False | 10.0 | 4.431 | 0.679 | 21.09 | 0.653 | 0.825 | 2 | 0 | 3 | 1 | 0 | 1.6 | `f855b4` |
| states | False | None | 3.929 | 0.697 | 25.37 | 0.653 | 0.812 | 0 | 0 | 3 | 0 | 0 | 6.7 | `02c46d` |
| districts | True | 0.0 | 4.621 | 0.552 | 28.34 | 0.907 | 0.698 | 0 | 0 | 51 | 1 | 0 | 7.3 | `0e8329` |
| districts | True | 0.25 | 4.833 | 0.588 | 27.01 | 0.907 | 0.706 | 0 | 0 | 50 | 0 | 0 | 4.2 | `2e799d` |
| districts | True | 0.5 | 4.874 | 0.572 | 28.40 | 0.907 | 0.708 | 0 | 0 | 49 | 0 | 0 | 4.5 | `6576b6` |
| districts | True | 2.0 | 4.986 | 0.511 | 31.85 | 0.907 | 0.709 | 0 | 0 | 48 | 1 | 0 | 4.1 | `8587df` |
| districts | True | 4.0 | 5.067 | 0.487 | 32.79 | 0.907 | 0.713 | 0 | 1 | 47 | 1 | 0 | 6.2 | `aab07e` |
| districts | True | 10.0 | 5.231 | 0.434 | 37.11 | 0.907 | 0.695 | 0 | 0 | 51 | 1 | 0 | 6.9 | `f27747` |
| districts | True | None | 4.519 | 0.527 | 25.92 | 0.907 | 0.687 | 0 | 0 | 54 | 0 | 0 | 6.0 | `df64c3` |
| districts | False | 0.0 | 7.396 | 0.485 | 35.57 | 0.907 | 0.850 | 0 | 1 | 12 | 0 | 0 | 4.3 | `6ae019` |
| districts | False | 0.25 | 7.330 | 0.470 | 34.56 | 0.907 | 0.871 | 0 | 1 | 12 | 0 | 0 | 10.2 | `8f82c0` |
| districts | False | 0.5 | 7.280 | 0.473 | 36.13 | 0.907 | 0.874 | 0 | 1 | 12 | 0 | 0 | 6.0 | `1d7c28` |
| districts | False | 2.0 | 7.634 | 0.455 | 36.39 | 0.907 | 0.888 | 0 | 1 | 10 | 1 | 0 | 3.6 | `b7566a` |
| districts | False | 4.0 | 7.868 | 0.453 | 35.72 | 0.907 | 0.881 | 0 | 2 | 10 | 1 | 0 | 5.4 | `8db2a9` |
| districts | False | 10.0 | 8.322 | 0.430 | 40.10 | 0.907 | 0.891 | 0 | 2 | 11 | 0 | 0 | 24.3 | `6250b4` |
| districts | False | None | 7.286 | 0.485 | 33.92 | 0.907 | 0.857 | 0 | 0 | 14 | 0 | 0 | 3.5 | `485616` |
| world | True | 0.0 | 3.301 | 0.631 | 26.46 | 0.907 | 0.411 | 0 | 0 | 97 | 1 | 6 | 1.6 | `2c7538` |
| world | True | 0.25 | 3.301 | 0.631 | 26.46 | 0.907 | 0.412 | 0 | 0 | 96 | 1 | 6 | 1.7 | `26a115` |
| world | True | 0.5 | 3.536 | 0.621 | 26.62 | 0.907 | 0.407 | 0 | 0 | 97 | 2 | 5 | 1.7 | `9e0f4c` |
| world | True | 2.0 | 4.253 | 0.490 | 30.97 | 0.907 | 0.436 | 1 | 0 | 103 | 6 | 14 | 1.7 | `26ec7e` |
| world | True | 4.0 | 4.367 | 0.487 | 34.08 | 0.907 | 0.434 | 1 | 0 | 103 | 6 | 11 | 1.8 | `13bad6` |
| world | True | 10.0 | 4.280 | 0.482 | 34.79 | 0.907 | 0.429 | 1 | 0 | 103 | 5 | 11 | 1.8 | `334db0` |
| world | True | None | 3.851 | 0.544 | 27.69 | 0.907 | 0.420 | 0 | 0 | 96 | 5 | 11 | 1.9 | `0360cc` |
| world | False | 0.0 | 7.934 | 0.511 | 29.31 | 0.907 | 0.523 | 0 | 0 | 32 | 1 | 17 | 1.6 | `8a7e7a` |
| world | False | 0.25 | 6.504 | 0.500 | 31.85 | 0.907 | 0.531 | 0 | 0 | 33 | 0 | 16 | 1.8 | `88acd0` |
| world | False | 0.5 | 6.781 | 0.419 | 34.18 | 0.907 | 0.539 | 2 | 0 | 34 | 1 | 17 | 3.7 | `b6735d` |
| world | False | 2.0 | 7.636 | 0.340 | 41.70 | 0.907 | 0.531 | 2 | 0 | 29 | 1 | 18 | 4.7 | `0489d0` |
| world | False | 4.0 | 10.066 | 0.286 | 48.15 | 0.907 | 0.483 | 3 | 0 | 33 | 2 | 18 | 3.8 | `f7db9b` |
| world | False | 10.0 | 9.207 | 0.340 | 34.41 | 0.907 | 0.469 | 3 | 0 | 32 | 0 | 18 | 5.2 | `d2fa99` |
| world | False | None | 6.582 | 0.395 | 37.27 | 0.907 | 0.542 | 2 | 0 | 34 | 1 | 18 | 3.6 | `2944bb` |


## max_connectivity_iters

| case | morph | value | disp | adj | dir | pp | iou | noncontig | split | unassigned_core | enclosed | short | wall_s | fp |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| states_uniform | True | 0 | 1.526 | 0.725 | 28.32 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 0.9 | `d4bfd1` |
| states_uniform | True | 1 | 1.526 | 0.725 | 28.32 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 0.8 | `d4bfd1` |
| states_uniform | True | 2 | 1.526 | 0.725 | 28.32 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 0.8 | `d4bfd1` |
| states_uniform | True | 5 | 1.526 | 0.725 | 28.32 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 0.9 | `d4bfd1` |
| states_uniform | True | 30 | 1.526 | 0.725 | 28.32 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 0.9 | `d4bfd1` |
| states_uniform | True | None | 1.526 | 0.725 | 28.32 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 0.8 | `d4bfd1` |
| states_uniform | False | 0 | 2.238 | 0.523 | 34.23 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `db2447` |
| states_uniform | False | 1 | 2.238 | 0.523 | 34.23 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `db2447` |
| states_uniform | False | 2 | 2.238 | 0.523 | 34.23 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `db2447` |
| states_uniform | False | 5 | 2.238 | 0.523 | 34.23 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `db2447` |
| states_uniform | False | 30 | 2.238 | 0.523 | 34.23 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `db2447` |
| states_uniform | False | None | 2.238 | 0.523 | 34.23 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `db2447` |
| states_uniform_sq | True | 0 | 0.745 | 0.459 | 24.82 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 1.0 | `02f6d0` |
| states_uniform_sq | True | 1 | 0.745 | 0.459 | 24.82 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 0.9 | `02f6d0` |
| states_uniform_sq | True | 2 | 0.745 | 0.459 | 24.82 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 0.9 | `02f6d0` |
| states_uniform_sq | True | 5 | 0.745 | 0.459 | 24.82 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 1.0 | `02f6d0` |
| states_uniform_sq | True | 30 | 0.745 | 0.459 | 24.82 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 1.0 | `02f6d0` |
| states_uniform_sq | True | None | 0.745 | 0.459 | 24.82 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 1.0 | `02f6d0` |
| states_uniform_sq | False | 0 | 1.256 | 0.404 | 32.42 | 0.785 | 0.793 | 0 | 0 | 1 | 0 | 0 | 1.2 | `df86ec` |
| states_uniform_sq | False | 1 | 1.583 | 0.468 | 30.20 | 0.785 | 0.801 | 0 | 0 | 1 | 0 | 0 | 1.2 | `0fae83` |
| states_uniform_sq | False | 2 | 1.583 | 0.468 | 30.20 | 0.785 | 0.801 | 0 | 0 | 1 | 0 | 0 | 1.2 | `0fae83` |
| states_uniform_sq | False | 5 | 1.583 | 0.468 | 30.20 | 0.785 | 0.801 | 0 | 0 | 1 | 0 | 0 | 1.2 | `0fae83` |
| states_uniform_sq | False | 30 | 1.583 | 0.468 | 30.20 | 0.785 | 0.801 | 0 | 0 | 1 | 0 | 0 | 1.0 | `0fae83` |
| states_uniform_sq | False | None | 1.583 | 0.468 | 30.20 | 0.785 | 0.801 | 0 | 0 | 1 | 0 | 0 | 1.2 | `0fae83` |
| states | True | 0 | 2.099 | 0.798 | 17.11 | 0.653 | 0.687 | 0 | 0 | 19 | 0 | 0 | 2.0 | `febe8e` |
| states | True | 1 | 2.099 | 0.798 | 17.11 | 0.653 | 0.687 | 0 | 0 | 19 | 0 | 0 | 1.4 | `febe8e` |
| states | True | 2 | 2.099 | 0.798 | 17.11 | 0.653 | 0.687 | 0 | 0 | 19 | 0 | 0 | 1.4 | `febe8e` |
| states | True | 5 | 2.099 | 0.798 | 17.11 | 0.653 | 0.687 | 0 | 0 | 19 | 0 | 0 | 1.4 | `febe8e` |
| states | True | 30 | 2.099 | 0.798 | 17.11 | 0.653 | 0.687 | 0 | 0 | 19 | 0 | 0 | 5.1 | `febe8e` |
| states | True | None | 2.099 | 0.798 | 17.11 | 0.653 | 0.687 | 0 | 0 | 19 | 0 | 0 | 1.3 | `febe8e` |
| states | False | 0 | 3.971 | 0.716 | 21.30 | 0.653 | 0.820 | 0 | 0 | 2 | 0 | 0 | 1.5 | `3a13c0` |
| states | False | 1 | 4.277 | 0.743 | 19.65 | 0.680 | 0.812 | 2 | 0 | 3 | 0 | 0 | 1.6 | `84d818` |
| states | False | 2 | 3.929 | 0.697 | 25.37 | 0.653 | 0.812 | 0 | 0 | 3 | 0 | 0 | 6.7 | `02c46d` |
| states | False | 5 | 3.929 | 0.697 | 25.37 | 0.653 | 0.812 | 0 | 0 | 3 | 0 | 0 | 6.8 | `02c46d` |
| states | False | 30 | 3.929 | 0.697 | 25.37 | 0.653 | 0.812 | 0 | 0 | 3 | 0 | 0 | 6.9 | `02c46d` |
| states | False | None | 3.929 | 0.697 | 25.37 | 0.653 | 0.812 | 0 | 0 | 3 | 0 | 0 | 6.7 | `02c46d` |
| districts | True | 0 | 4.519 | 0.527 | 25.92 | 0.907 | 0.687 | 0 | 0 | 54 | 0 | 0 | 5.8 | `df64c3` |
| districts | True | 1 | 4.519 | 0.527 | 25.92 | 0.907 | 0.687 | 0 | 0 | 54 | 0 | 0 | 6.0 | `df64c3` |
| districts | True | 2 | 4.519 | 0.527 | 25.92 | 0.907 | 0.687 | 0 | 0 | 54 | 0 | 0 | 6.1 | `df64c3` |
| districts | True | 5 | 4.519 | 0.527 | 25.92 | 0.907 | 0.687 | 0 | 0 | 54 | 0 | 0 | 6.1 | `df64c3` |
| districts | True | 30 | 4.519 | 0.527 | 25.92 | 0.907 | 0.687 | 0 | 0 | 54 | 0 | 0 | 6.2 | `df64c3` |
| districts | True | None | 4.519 | 0.527 | 25.92 | 0.907 | 0.687 | 0 | 0 | 54 | 0 | 0 | 6.0 | `df64c3` |
| districts | False | 0 | 7.091 | 0.352 | 44.55 | 0.907 | 0.847 | 0 | 1 | 17 | 0 | 0 | 16.1 | `351e8e` |
| districts | False | 1 | 6.971 | 0.462 | 37.04 | 0.907 | 0.851 | 0 | 1 | 16 | 0 | 0 | 5.4 | `14d343` |
| districts | False | 2 | 7.286 | 0.485 | 33.92 | 0.907 | 0.857 | 0 | 0 | 14 | 0 | 0 | 5.1 | `485616` |
| districts | False | 5 | 7.286 | 0.485 | 33.92 | 0.907 | 0.857 | 0 | 0 | 14 | 0 | 0 | 5.4 | `485616` |
| districts | False | 30 | 7.286 | 0.485 | 33.92 | 0.907 | 0.857 | 0 | 0 | 14 | 0 | 0 | 5.3 | `485616` |
| districts | False | None | 7.286 | 0.485 | 33.92 | 0.907 | 0.857 | 0 | 0 | 14 | 0 | 0 | 3.5 | `485616` |
| world | True | 0 | 3.851 | 0.544 | 27.69 | 0.907 | 0.420 | 0 | 0 | 96 | 5 | 11 | 1.8 | `0360cc` |
| world | True | 1 | 3.851 | 0.544 | 27.69 | 0.907 | 0.420 | 0 | 0 | 96 | 5 | 11 | 1.8 | `0360cc` |
| world | True | 2 | 3.851 | 0.544 | 27.69 | 0.907 | 0.420 | 0 | 0 | 96 | 5 | 11 | 1.8 | `0360cc` |
| world | True | 5 | 3.851 | 0.544 | 27.69 | 0.907 | 0.420 | 0 | 0 | 96 | 5 | 11 | 1.9 | `0360cc` |
| world | True | 30 | 3.851 | 0.544 | 27.69 | 0.907 | 0.420 | 0 | 0 | 96 | 5 | 11 | 1.9 | `0360cc` |
| world | True | None | 3.851 | 0.544 | 27.69 | 0.907 | 0.420 | 0 | 0 | 96 | 5 | 11 | 1.9 | `0360cc` |
| world | False | 0 | 6.582 | 0.395 | 37.27 | 0.907 | 0.542 | 2 | 0 | 34 | 1 | 18 | 3.5 | `2944bb` |
| world | False | 1 | 6.582 | 0.395 | 37.27 | 0.907 | 0.542 | 2 | 0 | 34 | 1 | 18 | 3.9 | `2944bb` |
| world | False | 2 | 6.582 | 0.395 | 37.27 | 0.907 | 0.542 | 2 | 0 | 34 | 1 | 18 | 3.6 | `2944bb` |
| world | False | 5 | 6.582 | 0.395 | 37.27 | 0.907 | 0.542 | 2 | 0 | 34 | 1 | 18 | 3.6 | `2944bb` |
| world | False | 30 | 6.582 | 0.395 | 37.27 | 0.907 | 0.542 | 2 | 0 | 34 | 1 | 18 | 3.7 | `2944bb` |
| world | False | None | 6.582 | 0.395 | 37.27 | 0.907 | 0.542 | 2 | 0 | 34 | 1 | 18 | 3.6 | `2944bb` |


## disconnected_penalty_mult

| case | morph | value | disp | adj | dir | pp | iou | noncontig | split | unassigned_core | enclosed | short | wall_s | fp |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| states_uniform | True | 0.0 | 1.526 | 0.725 | 28.32 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 0.8 | `d4bfd1` |
| states_uniform | True | 1.0 | 1.526 | 0.725 | 28.32 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 0.9 | `d4bfd1` |
| states_uniform | True | 2.0 | 1.526 | 0.725 | 28.32 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 0.8 | `d4bfd1` |
| states_uniform | True | 5.0 | 1.526 | 0.725 | 28.32 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 0.9 | `d4bfd1` |
| states_uniform | True | 50.0 | 1.526 | 0.725 | 28.32 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 0.8 | `d4bfd1` |
| states_uniform | True | None | 1.526 | 0.725 | 28.32 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 0.8 | `d4bfd1` |
| states_uniform | False | 0.0 | 2.238 | 0.523 | 34.23 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `db2447` |
| states_uniform | False | 1.0 | 2.238 | 0.523 | 34.23 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 0.8 | `db2447` |
| states_uniform | False | 2.0 | 2.238 | 0.523 | 34.23 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 0.7 | `db2447` |
| states_uniform | False | 5.0 | 2.238 | 0.523 | 34.23 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `db2447` |
| states_uniform | False | 50.0 | 2.238 | 0.523 | 34.23 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `db2447` |
| states_uniform | False | None | 2.238 | 0.523 | 34.23 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `db2447` |
| states_uniform_sq | True | 0.0 | 0.745 | 0.459 | 24.82 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 0.9 | `02f6d0` |
| states_uniform_sq | True | 1.0 | 0.745 | 0.459 | 24.82 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 1.3 | `02f6d0` |
| states_uniform_sq | True | 2.0 | 0.745 | 0.459 | 24.82 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 1.1 | `02f6d0` |
| states_uniform_sq | True | 5.0 | 0.745 | 0.459 | 24.82 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 0.9 | `02f6d0` |
| states_uniform_sq | True | 50.0 | 0.745 | 0.459 | 24.82 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 3.0 | `02f6d0` |
| states_uniform_sq | True | None | 0.745 | 0.459 | 24.82 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 1.0 | `02f6d0` |
| states_uniform_sq | False | 0.0 | 1.583 | 0.468 | 30.20 | 0.785 | 0.801 | 0 | 0 | 1 | 0 | 0 | 0.8 | `0fae83` |
| states_uniform_sq | False | 1.0 | 1.583 | 0.468 | 30.20 | 0.785 | 0.801 | 0 | 0 | 1 | 0 | 0 | 1.3 | `0fae83` |
| states_uniform_sq | False | 2.0 | 1.583 | 0.468 | 30.20 | 0.785 | 0.801 | 0 | 0 | 1 | 0 | 0 | 1.3 | `0fae83` |
| states_uniform_sq | False | 5.0 | 1.583 | 0.468 | 30.20 | 0.785 | 0.801 | 0 | 0 | 1 | 0 | 0 | 1.3 | `0fae83` |
| states_uniform_sq | False | 50.0 | 1.583 | 0.468 | 30.20 | 0.785 | 0.801 | 0 | 0 | 1 | 0 | 0 | 1.3 | `0fae83` |
| states_uniform_sq | False | None | 1.583 | 0.468 | 30.20 | 0.785 | 0.801 | 0 | 0 | 1 | 0 | 0 | 1.2 | `0fae83` |
| states | True | 0.0 | 2.099 | 0.798 | 17.11 | 0.653 | 0.687 | 0 | 0 | 19 | 0 | 0 | 1.4 | `febe8e` |
| states | True | 1.0 | 2.099 | 0.798 | 17.11 | 0.653 | 0.687 | 0 | 0 | 19 | 0 | 0 | 1.2 | `febe8e` |
| states | True | 2.0 | 2.099 | 0.798 | 17.11 | 0.653 | 0.687 | 0 | 0 | 19 | 0 | 0 | 1.4 | `febe8e` |
| states | True | 5.0 | 2.099 | 0.798 | 17.11 | 0.653 | 0.687 | 0 | 0 | 19 | 0 | 0 | 1.2 | `febe8e` |
| states | True | 50.0 | 2.099 | 0.798 | 17.11 | 0.653 | 0.687 | 0 | 0 | 19 | 0 | 0 | 1.2 | `febe8e` |
| states | True | None | 2.099 | 0.798 | 17.11 | 0.653 | 0.687 | 0 | 0 | 19 | 0 | 0 | 1.3 | `febe8e` |
| states | False | 0.0 | 4.133 | 0.752 | 18.57 | 0.680 | 0.817 | 0 | 0 | 3 | 0 | 0 | 1.5 | `978193` |
| states | False | 1.0 | 3.929 | 0.697 | 25.37 | 0.653 | 0.812 | 0 | 0 | 3 | 0 | 0 | 6.4 | `02c46d` |
| states | False | 2.0 | 3.929 | 0.697 | 25.37 | 0.653 | 0.812 | 0 | 0 | 3 | 0 | 0 | 6.7 | `02c46d` |
| states | False | 5.0 | 3.929 | 0.697 | 25.37 | 0.653 | 0.812 | 0 | 0 | 3 | 0 | 0 | 7.1 | `02c46d` |
| states | False | 50.0 | 3.929 | 0.697 | 25.37 | 0.653 | 0.812 | 0 | 0 | 3 | 0 | 0 | 5.8 | `02c46d` |
| states | False | None | 3.929 | 0.697 | 25.37 | 0.653 | 0.812 | 0 | 0 | 3 | 0 | 0 | 6.7 | `02c46d` |
| districts | True | 0.0 | 4.519 | 0.527 | 25.92 | 0.907 | 0.687 | 0 | 0 | 54 | 0 | 0 | 6.1 | `df64c3` |
| districts | True | 1.0 | 4.519 | 0.527 | 25.92 | 0.907 | 0.687 | 0 | 0 | 54 | 0 | 0 | 4.6 | `df64c3` |
| districts | True | 2.0 | 4.519 | 0.527 | 25.92 | 0.907 | 0.687 | 0 | 0 | 54 | 0 | 0 | 4.2 | `df64c3` |
| districts | True | 5.0 | 4.519 | 0.527 | 25.92 | 0.907 | 0.687 | 0 | 0 | 54 | 0 | 0 | 19.2 | `df64c3` |
| districts | True | 50.0 | 4.519 | 0.527 | 25.92 | 0.907 | 0.687 | 0 | 0 | 54 | 0 | 0 | 4.4 | `df64c3` |
| districts | True | None | 4.519 | 0.527 | 25.92 | 0.907 | 0.687 | 0 | 0 | 54 | 0 | 0 | 6.0 | `df64c3` |
| districts | False | 0.0 | 7.434 | 0.502 | 33.13 | 0.907 | 0.858 | 0 | 0 | 15 | 0 | 0 | 5.1 | `1f0801` |
| districts | False | 1.0 | 7.286 | 0.485 | 33.92 | 0.907 | 0.857 | 0 | 0 | 14 | 0 | 0 | 5.2 | `485616` |
| districts | False | 2.0 | 7.286 | 0.485 | 33.92 | 0.907 | 0.857 | 0 | 0 | 14 | 0 | 0 | 5.4 | `485616` |
| districts | False | 5.0 | 7.286 | 0.485 | 33.92 | 0.907 | 0.857 | 0 | 0 | 14 | 0 | 0 | 5.3 | `485616` |
| districts | False | 50.0 | 7.286 | 0.485 | 33.92 | 0.907 | 0.857 | 0 | 0 | 14 | 0 | 0 | 5.3 | `485616` |
| districts | False | None | 7.286 | 0.485 | 33.92 | 0.907 | 0.857 | 0 | 0 | 14 | 0 | 0 | 3.5 | `485616` |
| world | True | 0.0 | 3.851 | 0.544 | 27.69 | 0.907 | 0.420 | 0 | 0 | 96 | 5 | 11 | 1.8 | `0360cc` |
| world | True | 1.0 | 3.851 | 0.544 | 27.69 | 0.907 | 0.420 | 0 | 0 | 96 | 5 | 11 | 1.8 | `0360cc` |
| world | True | 2.0 | 3.851 | 0.544 | 27.69 | 0.907 | 0.420 | 0 | 0 | 96 | 5 | 11 | 1.8 | `0360cc` |
| world | True | 5.0 | 3.851 | 0.544 | 27.69 | 0.907 | 0.420 | 0 | 0 | 96 | 5 | 11 | 1.9 | `0360cc` |
| world | True | 50.0 | 3.851 | 0.544 | 27.69 | 0.907 | 0.420 | 0 | 0 | 96 | 5 | 11 | 1.8 | `0360cc` |
| world | True | None | 3.851 | 0.544 | 27.69 | 0.907 | 0.420 | 0 | 0 | 96 | 5 | 11 | 1.9 | `0360cc` |
| world | False | 0.0 | 6.582 | 0.395 | 37.27 | 0.907 | 0.542 | 2 | 0 | 34 | 1 | 18 | 3.7 | `2944bb` |
| world | False | 1.0 | 6.582 | 0.395 | 37.27 | 0.907 | 0.542 | 2 | 0 | 34 | 1 | 18 | 3.7 | `2944bb` |
| world | False | 2.0 | 6.582 | 0.395 | 37.27 | 0.907 | 0.542 | 2 | 0 | 34 | 1 | 18 | 3.7 | `2944bb` |
| world | False | 5.0 | 6.582 | 0.395 | 37.27 | 0.907 | 0.542 | 2 | 0 | 34 | 1 | 18 | 3.7 | `2944bb` |
| world | False | 50.0 | 6.582 | 0.395 | 37.27 | 0.907 | 0.542 | 2 | 0 | 34 | 1 | 18 | 3.7 | `2944bb` |
| world | False | None | 6.582 | 0.395 | 37.27 | 0.907 | 0.542 | 2 | 0 | 34 | 1 | 18 | 3.6 | `2944bb` |


## gap_bridge_mult

| case | morph | value | disp | adj | dir | pp | iou | noncontig | split | unassigned_core | enclosed | short | wall_s | fp |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| states_uniform | True | 0.0 | 1.526 | 0.725 | 28.32 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 0.8 | `d4bfd1` |
| states_uniform | True | 1.0 | 1.526 | 0.725 | 28.32 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 0.8 | `d4bfd1` |
| states_uniform | True | 2.0 | 1.526 | 0.725 | 28.32 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 0.8 | `d4bfd1` |
| states_uniform | True | 20.0 | 1.526 | 0.725 | 28.32 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 0.9 | `d4bfd1` |
| states_uniform | True | None | 1.526 | 0.725 | 28.32 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 0.8 | `d4bfd1` |
| states_uniform | False | 0.0 | 2.238 | 0.523 | 34.23 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `db2447` |
| states_uniform | False | 1.0 | 2.238 | 0.523 | 34.23 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `db2447` |
| states_uniform | False | 2.0 | 2.238 | 0.523 | 34.23 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `db2447` |
| states_uniform | False | 20.0 | 2.238 | 0.523 | 34.23 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.1 | `db2447` |
| states_uniform | False | None | 2.238 | 0.523 | 34.23 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `db2447` |
| states_uniform_sq | True | 0.0 | 0.745 | 0.459 | 24.82 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 1.0 | `02f6d0` |
| states_uniform_sq | True | 1.0 | 0.745 | 0.459 | 24.82 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 0.9 | `02f6d0` |
| states_uniform_sq | True | 2.0 | 0.745 | 0.459 | 24.82 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 0.9 | `02f6d0` |
| states_uniform_sq | True | 20.0 | 0.745 | 0.459 | 24.82 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 0.9 | `02f6d0` |
| states_uniform_sq | True | None | 0.745 | 0.459 | 24.82 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 1.0 | `02f6d0` |
| states_uniform_sq | False | 0.0 | 1.583 | 0.468 | 30.20 | 0.785 | 0.801 | 0 | 0 | 1 | 0 | 0 | 1.2 | `0fae83` |
| states_uniform_sq | False | 1.0 | 1.583 | 0.468 | 30.20 | 0.785 | 0.801 | 0 | 0 | 1 | 0 | 0 | 1.2 | `0fae83` |
| states_uniform_sq | False | 2.0 | 1.583 | 0.468 | 30.20 | 0.785 | 0.801 | 0 | 0 | 1 | 0 | 0 | 1.2 | `0fae83` |
| states_uniform_sq | False | 20.0 | 1.583 | 0.468 | 30.20 | 0.785 | 0.801 | 0 | 0 | 1 | 0 | 0 | 1.2 | `0fae83` |
| states_uniform_sq | False | None | 1.583 | 0.468 | 30.20 | 0.785 | 0.801 | 0 | 0 | 1 | 0 | 0 | 1.2 | `0fae83` |
| states | True | 0.0 | 2.099 | 0.798 | 17.11 | 0.653 | 0.687 | 0 | 0 | 19 | 0 | 0 | 1.3 | `febe8e` |
| states | True | 1.0 | 2.099 | 0.798 | 17.11 | 0.653 | 0.687 | 0 | 0 | 19 | 0 | 0 | 1.2 | `febe8e` |
| states | True | 2.0 | 2.099 | 0.798 | 17.11 | 0.653 | 0.687 | 0 | 0 | 19 | 0 | 0 | 1.2 | `febe8e` |
| states | True | 20.0 | 2.099 | 0.798 | 17.11 | 0.653 | 0.687 | 0 | 0 | 19 | 0 | 0 | 1.2 | `febe8e` |
| states | True | None | 2.099 | 0.798 | 17.11 | 0.653 | 0.687 | 0 | 0 | 19 | 0 | 0 | 1.3 | `febe8e` |
| states | False | 0.0 | 3.929 | 0.697 | 25.37 | 0.653 | 0.812 | 0 | 0 | 3 | 0 | 0 | 4.9 | `02c46d` |
| states | False | 1.0 | 3.929 | 0.697 | 25.37 | 0.653 | 0.812 | 0 | 0 | 3 | 0 | 0 | 5.4 | `02c46d` |
| states | False | 2.0 | 3.929 | 0.697 | 25.37 | 0.653 | 0.812 | 0 | 0 | 3 | 0 | 0 | 11.5 | `02c46d` |
| states | False | 20.0 | 3.929 | 0.697 | 25.37 | 0.653 | 0.812 | 0 | 0 | 3 | 0 | 0 | 7.4 | `02c46d` |
| states | False | None | 3.929 | 0.697 | 25.37 | 0.653 | 0.812 | 0 | 0 | 3 | 0 | 0 | 6.7 | `02c46d` |
| districts | True | 0.0 | 4.519 | 0.527 | 25.92 | 0.907 | 0.687 | 0 | 0 | 54 | 0 | 0 | 3.9 | `df64c3` |
| districts | True | 1.0 | 4.519 | 0.527 | 25.92 | 0.907 | 0.687 | 0 | 0 | 54 | 0 | 0 | 4.1 | `df64c3` |
| districts | True | 2.0 | 4.519 | 0.527 | 25.92 | 0.907 | 0.687 | 0 | 0 | 54 | 0 | 0 | 4.0 | `df64c3` |
| districts | True | 20.0 | 4.519 | 0.527 | 25.92 | 0.907 | 0.687 | 0 | 0 | 54 | 0 | 0 | 4.1 | `df64c3` |
| districts | True | None | 4.519 | 0.527 | 25.92 | 0.907 | 0.687 | 0 | 0 | 54 | 0 | 0 | 6.0 | `df64c3` |
| districts | False | 0.0 | 7.286 | 0.485 | 33.92 | 0.907 | 0.857 | 0 | 0 | 14 | 0 | 0 | 5.3 | `485616` |
| districts | False | 1.0 | 7.286 | 0.485 | 33.92 | 0.907 | 0.857 | 0 | 0 | 14 | 0 | 0 | 5.4 | `485616` |
| districts | False | 2.0 | 7.286 | 0.485 | 33.92 | 0.907 | 0.857 | 0 | 0 | 14 | 0 | 0 | 5.3 | `485616` |
| districts | False | 20.0 | 7.286 | 0.485 | 33.92 | 0.907 | 0.857 | 0 | 0 | 14 | 0 | 0 | 5.3 | `485616` |
| districts | False | None | 7.286 | 0.485 | 33.92 | 0.907 | 0.857 | 0 | 0 | 14 | 0 | 0 | 3.5 | `485616` |
| world | True | 0.0 | 3.851 | 0.544 | 27.69 | 0.907 | 0.420 | 0 | 0 | 96 | 5 | 11 | 1.9 | `0360cc` |
| world | True | 1.0 | 3.851 | 0.544 | 27.69 | 0.907 | 0.420 | 0 | 0 | 96 | 5 | 11 | 1.8 | `0360cc` |
| world | True | 2.0 | 3.851 | 0.544 | 27.69 | 0.907 | 0.420 | 0 | 0 | 96 | 5 | 11 | 1.9 | `0360cc` |
| world | True | 20.0 | 3.851 | 0.544 | 27.69 | 0.907 | 0.420 | 0 | 0 | 96 | 5 | 11 | 1.8 | `0360cc` |
| world | True | None | 3.851 | 0.544 | 27.69 | 0.907 | 0.420 | 0 | 0 | 96 | 5 | 11 | 1.9 | `0360cc` |
| world | False | 0.0 | 6.582 | 0.395 | 37.27 | 0.907 | 0.542 | 2 | 0 | 34 | 1 | 18 | 4.1 | `2944bb` |
| world | False | 1.0 | 6.582 | 0.395 | 37.27 | 0.907 | 0.542 | 2 | 0 | 34 | 1 | 18 | 3.6 | `2944bb` |
| world | False | 2.0 | 6.582 | 0.395 | 37.27 | 0.907 | 0.542 | 2 | 0 | 34 | 1 | 18 | 3.7 | `2944bb` |
| world | False | 20.0 | 6.582 | 0.395 | 37.27 | 0.907 | 0.542 | 2 | 0 | 34 | 1 | 18 | 3.6 | `2944bb` |
| world | False | None | 6.582 | 0.395 | 37.27 | 0.907 | 0.542 | 2 | 0 | 34 | 1 | 18 | 3.6 | `2944bb` |


## disconnected_score_weight

| case | morph | value | disp | adj | dir | pp | iou | noncontig | split | unassigned_core | enclosed | short | wall_s | fp |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| states_uniform | True | 0 | 1.526 | 0.725 | 28.32 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 0.9 | `d4bfd1` |
| states_uniform | True | 1 | 1.526 | 0.725 | 28.32 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 0.8 | `d4bfd1` |
| states_uniform | True | 10 | 1.526 | 0.725 | 28.32 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 0.9 | `d4bfd1` |
| states_uniform | True | 1000 | 1.526 | 0.725 | 28.32 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 0.8 | `d4bfd1` |
| states_uniform | True | None | 1.526 | 0.725 | 28.32 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 0.8 | `d4bfd1` |
| states_uniform | False | 0 | 2.238 | 0.523 | 34.23 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `db2447` |
| states_uniform | False | 1 | 2.238 | 0.523 | 34.23 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `db2447` |
| states_uniform | False | 10 | 2.238 | 0.523 | 34.23 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `db2447` |
| states_uniform | False | 1000 | 2.238 | 0.523 | 34.23 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `db2447` |
| states_uniform | False | None | 2.238 | 0.523 | 34.23 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `db2447` |
| states_uniform_sq | True | 0 | 0.745 | 0.459 | 24.82 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 0.9 | `02f6d0` |
| states_uniform_sq | True | 1 | 0.745 | 0.459 | 24.82 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 0.8 | `02f6d0` |
| states_uniform_sq | True | 10 | 0.745 | 0.459 | 24.82 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 0.9 | `02f6d0` |
| states_uniform_sq | True | 1000 | 0.745 | 0.459 | 24.82 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 0.9 | `02f6d0` |
| states_uniform_sq | True | None | 0.745 | 0.459 | 24.82 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 1.0 | `02f6d0` |
| states_uniform_sq | False | 0 | 1.583 | 0.468 | 30.20 | 0.785 | 0.801 | 0 | 0 | 1 | 0 | 0 | 1.3 | `0fae83` |
| states_uniform_sq | False | 1 | 1.583 | 0.468 | 30.20 | 0.785 | 0.801 | 0 | 0 | 1 | 0 | 0 | 1.2 | `0fae83` |
| states_uniform_sq | False | 10 | 1.583 | 0.468 | 30.20 | 0.785 | 0.801 | 0 | 0 | 1 | 0 | 0 | 1.2 | `0fae83` |
| states_uniform_sq | False | 1000 | 1.583 | 0.468 | 30.20 | 0.785 | 0.801 | 0 | 0 | 1 | 0 | 0 | 1.2 | `0fae83` |
| states_uniform_sq | False | None | 1.583 | 0.468 | 30.20 | 0.785 | 0.801 | 0 | 0 | 1 | 0 | 0 | 1.2 | `0fae83` |
| states | True | 0 | 2.099 | 0.798 | 17.11 | 0.653 | 0.687 | 0 | 0 | 19 | 0 | 0 | 1.3 | `febe8e` |
| states | True | 1 | 2.099 | 0.798 | 17.11 | 0.653 | 0.687 | 0 | 0 | 19 | 0 | 0 | 1.3 | `febe8e` |
| states | True | 10 | 2.099 | 0.798 | 17.11 | 0.653 | 0.687 | 0 | 0 | 19 | 0 | 0 | 1.3 | `febe8e` |
| states | True | 1000 | 2.099 | 0.798 | 17.11 | 0.653 | 0.687 | 0 | 0 | 19 | 0 | 0 | 1.2 | `febe8e` |
| states | True | None | 2.099 | 0.798 | 17.11 | 0.653 | 0.687 | 0 | 0 | 19 | 0 | 0 | 1.3 | `febe8e` |
| states | False | 0 | 3.929 | 0.697 | 25.37 | 0.653 | 0.812 | 0 | 0 | 3 | 0 | 0 | 7.1 | `02c46d` |
| states | False | 1 | 3.929 | 0.697 | 25.37 | 0.653 | 0.812 | 0 | 0 | 3 | 0 | 0 | 4.2 | `02c46d` |
| states | False | 10 | 3.929 | 0.697 | 25.37 | 0.653 | 0.812 | 0 | 0 | 3 | 0 | 0 | 4.6 | `02c46d` |
| states | False | 1000 | 3.929 | 0.697 | 25.37 | 0.653 | 0.812 | 0 | 0 | 3 | 0 | 0 | 6.4 | `02c46d` |
| states | False | None | 3.929 | 0.697 | 25.37 | 0.653 | 0.812 | 0 | 0 | 3 | 0 | 0 | 6.7 | `02c46d` |
| districts | True | 0 | 4.519 | 0.527 | 25.92 | 0.907 | 0.687 | 0 | 0 | 54 | 0 | 0 | 16.7 | `df64c3` |
| districts | True | 1 | 4.519 | 0.527 | 25.92 | 0.907 | 0.687 | 0 | 0 | 54 | 0 | 0 | 4.2 | `df64c3` |
| districts | True | 10 | 4.519 | 0.527 | 25.92 | 0.907 | 0.687 | 0 | 0 | 54 | 0 | 0 | 3.9 | `df64c3` |
| districts | True | 1000 | 4.519 | 0.527 | 25.92 | 0.907 | 0.687 | 0 | 0 | 54 | 0 | 0 | 4.0 | `df64c3` |
| districts | True | None | 4.519 | 0.527 | 25.92 | 0.907 | 0.687 | 0 | 0 | 54 | 0 | 0 | 6.0 | `df64c3` |
| districts | False | 0 | 7.286 | 0.485 | 33.92 | 0.907 | 0.857 | 0 | 0 | 14 | 0 | 0 | 4.8 | `485616` |
| districts | False | 1 | 7.286 | 0.485 | 33.92 | 0.907 | 0.857 | 0 | 0 | 14 | 0 | 0 | 3.7 | `485616` |
| districts | False | 10 | 7.286 | 0.485 | 33.92 | 0.907 | 0.857 | 0 | 0 | 14 | 0 | 0 | 3.6 | `485616` |
| districts | False | 1000 | 7.286 | 0.485 | 33.92 | 0.907 | 0.857 | 0 | 0 | 14 | 0 | 0 | 3.4 | `485616` |
| districts | False | None | 7.286 | 0.485 | 33.92 | 0.907 | 0.857 | 0 | 0 | 14 | 0 | 0 | 3.5 | `485616` |
| world | True | 0 | 3.851 | 0.544 | 27.69 | 0.907 | 0.420 | 0 | 0 | 96 | 5 | 11 | 1.9 | `0360cc` |
| world | True | 1 | 3.851 | 0.544 | 27.69 | 0.907 | 0.420 | 0 | 0 | 96 | 5 | 11 | 1.8 | `0360cc` |
| world | True | 10 | 3.851 | 0.544 | 27.69 | 0.907 | 0.420 | 0 | 0 | 96 | 5 | 11 | 1.9 | `0360cc` |
| world | True | 1000 | 3.851 | 0.544 | 27.69 | 0.907 | 0.420 | 0 | 0 | 96 | 5 | 11 | 1.8 | `0360cc` |
| world | True | None | 3.851 | 0.544 | 27.69 | 0.907 | 0.420 | 0 | 0 | 96 | 5 | 11 | 1.9 | `0360cc` |
| world | False | 0 | 6.582 | 0.395 | 37.27 | 0.907 | 0.542 | 2 | 0 | 34 | 1 | 18 | 3.7 | `2944bb` |
| world | False | 1 | 6.582 | 0.395 | 37.27 | 0.907 | 0.542 | 2 | 0 | 34 | 1 | 18 | 3.6 | `2944bb` |
| world | False | 10 | 6.582 | 0.395 | 37.27 | 0.907 | 0.542 | 2 | 0 | 34 | 1 | 18 | 3.6 | `2944bb` |
| world | False | 1000 | 6.582 | 0.395 | 37.27 | 0.907 | 0.542 | 2 | 0 | 34 | 1 | 18 | 3.7 | `2944bb` |
| world | False | None | 6.582 | 0.395 | 37.27 | 0.907 | 0.542 | 2 | 0 | 34 | 1 | 18 | 3.6 | `2944bb` |


## swap_repair_passes

| case | morph | value | disp | adj | dir | pp | iou | noncontig | split | unassigned_core | enclosed | short | wall_s | fp |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| states_uniform | True | 0 | 1.526 | 0.725 | 28.32 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 0.8 | `d4bfd1` |
| states_uniform | True | 1 | 1.526 | 0.725 | 28.32 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 0.9 | `d4bfd1` |
| states_uniform | True | 2 | 1.526 | 0.725 | 28.32 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 0.8 | `d4bfd1` |
| states_uniform | True | 5 | 1.526 | 0.725 | 28.32 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 0.8 | `d4bfd1` |
| states_uniform | True | 30 | 1.526 | 0.725 | 28.32 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 0.8 | `d4bfd1` |
| states_uniform | True | None | 1.526 | 0.725 | 28.32 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 0.8 | `d4bfd1` |
| states_uniform | False | 0 | 2.238 | 0.523 | 34.23 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `db2447` |
| states_uniform | False | 1 | 2.238 | 0.523 | 34.23 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `db2447` |
| states_uniform | False | 2 | 2.238 | 0.523 | 34.23 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `db2447` |
| states_uniform | False | 5 | 2.238 | 0.523 | 34.23 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `db2447` |
| states_uniform | False | 30 | 2.238 | 0.523 | 34.23 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `db2447` |
| states_uniform | False | None | 2.238 | 0.523 | 34.23 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `db2447` |
| states_uniform_sq | True | 0 | 0.745 | 0.459 | 24.82 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 0.9 | `02f6d0` |
| states_uniform_sq | True | 1 | 0.745 | 0.459 | 24.82 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 0.9 | `02f6d0` |
| states_uniform_sq | True | 2 | 0.745 | 0.459 | 24.82 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 0.9 | `02f6d0` |
| states_uniform_sq | True | 5 | 0.745 | 0.459 | 24.82 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 0.9 | `02f6d0` |
| states_uniform_sq | True | 30 | 0.745 | 0.459 | 24.82 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 0.8 | `02f6d0` |
| states_uniform_sq | True | None | 0.745 | 0.459 | 24.82 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 1.0 | `02f6d0` |
| states_uniform_sq | False | 0 | 1.583 | 0.468 | 30.20 | 0.785 | 0.801 | 0 | 0 | 1 | 0 | 0 | 1.2 | `0fae83` |
| states_uniform_sq | False | 1 | 1.583 | 0.468 | 30.20 | 0.785 | 0.801 | 0 | 0 | 1 | 0 | 0 | 1.2 | `0fae83` |
| states_uniform_sq | False | 2 | 1.583 | 0.468 | 30.20 | 0.785 | 0.801 | 0 | 0 | 1 | 0 | 0 | 1.2 | `0fae83` |
| states_uniform_sq | False | 5 | 1.583 | 0.468 | 30.20 | 0.785 | 0.801 | 0 | 0 | 1 | 0 | 0 | 1.2 | `0fae83` |
| states_uniform_sq | False | 30 | 1.583 | 0.468 | 30.20 | 0.785 | 0.801 | 0 | 0 | 1 | 0 | 0 | 1.2 | `0fae83` |
| states_uniform_sq | False | None | 1.583 | 0.468 | 30.20 | 0.785 | 0.801 | 0 | 0 | 1 | 0 | 0 | 1.2 | `0fae83` |
| states | True | 0 | 2.099 | 0.798 | 17.11 | 0.653 | 0.687 | 0 | 0 | 19 | 0 | 0 | 1.2 | `febe8e` |
| states | True | 1 | 2.099 | 0.798 | 17.11 | 0.653 | 0.687 | 0 | 0 | 19 | 0 | 0 | 1.3 | `febe8e` |
| states | True | 2 | 2.099 | 0.798 | 17.11 | 0.653 | 0.687 | 0 | 0 | 19 | 0 | 0 | 1.2 | `febe8e` |
| states | True | 5 | 2.099 | 0.798 | 17.11 | 0.653 | 0.687 | 0 | 0 | 19 | 0 | 0 | 1.3 | `febe8e` |
| states | True | 30 | 2.099 | 0.798 | 17.11 | 0.653 | 0.687 | 0 | 0 | 19 | 0 | 0 | 1.2 | `febe8e` |
| states | True | None | 2.099 | 0.798 | 17.11 | 0.653 | 0.687 | 0 | 0 | 19 | 0 | 0 | 1.3 | `febe8e` |
| states | False | 0 | 4.123 | 0.761 | 20.36 | 0.653 | 0.812 | 5 | 0 | 3 | 0 | 0 | 1.5 | `322788` |
| states | False | 1 | 3.907 | 0.752 | 22.02 | 0.653 | 0.812 | 4 | 0 | 3 | 0 | 0 | 4.2 | `49692f` |
| states | False | 2 | 3.907 | 0.734 | 22.02 | 0.653 | 0.812 | 3 | 0 | 3 | 0 | 0 | 7.1 | `5d74da` |
| states | False | 5 | 3.929 | 0.697 | 25.37 | 0.653 | 0.812 | 0 | 0 | 3 | 0 | 0 | 6.9 | `02c46d` |
| states | False | 30 | 3.929 | 0.697 | 25.37 | 0.653 | 0.812 | 0 | 0 | 3 | 0 | 0 | 7.0 | `02c46d` |
| states | False | None | 3.929 | 0.697 | 25.37 | 0.653 | 0.812 | 0 | 0 | 3 | 0 | 0 | 6.7 | `02c46d` |
| districts | True | 0 | 4.531 | 0.529 | 25.54 | 0.907 | 0.687 | 0 | 8 | 54 | 0 | 0 | 3.8 | `76942e` |
| districts | True | 1 | 4.519 | 0.527 | 25.84 | 0.907 | 0.687 | 0 | 1 | 54 | 0 | 0 | 4.9 | `ba709f` |
| districts | True | 2 | 4.519 | 0.527 | 25.92 | 0.907 | 0.687 | 0 | 0 | 54 | 0 | 0 | 3.8 | `df64c3` |
| districts | True | 5 | 4.519 | 0.527 | 25.92 | 0.907 | 0.687 | 0 | 0 | 54 | 0 | 0 | 3.7 | `df64c3` |
| districts | True | 30 | 4.519 | 0.527 | 25.92 | 0.907 | 0.687 | 0 | 0 | 54 | 0 | 0 | 3.9 | `df64c3` |
| districts | True | None | 4.519 | 0.527 | 25.92 | 0.907 | 0.687 | 0 | 0 | 54 | 0 | 0 | 6.0 | `df64c3` |
| districts | False | 0 | 7.264 | 0.485 | 33.18 | 0.907 | 0.857 | 0 | 12 | 14 | 0 | 0 | 3.3 | `5fbe23` |
| districts | False | 1 | 7.232 | 0.498 | 33.17 | 0.907 | 0.857 | 0 | 4 | 14 | 0 | 0 | 3.4 | `47247c` |
| districts | False | 2 | 7.232 | 0.490 | 33.51 | 0.907 | 0.857 | 0 | 3 | 14 | 0 | 0 | 3.4 | `2cba0e` |
| districts | False | 5 | 7.286 | 0.483 | 33.86 | 0.907 | 0.857 | 0 | 2 | 14 | 0 | 0 | 3.5 | `55b75a` |
| districts | False | 30 | 7.286 | 0.485 | 33.92 | 0.907 | 0.857 | 0 | 0 | 14 | 0 | 0 | 3.5 | `485616` |
| districts | False | None | 7.286 | 0.485 | 33.92 | 0.907 | 0.857 | 0 | 0 | 14 | 0 | 0 | 3.5 | `485616` |
| world | True | 0 | 3.927 | 0.580 | 27.62 | 0.907 | 0.420 | 4 | 0 | 96 | 5 | 11 | 1.8 | `e592d2` |
| world | True | 1 | 3.851 | 0.544 | 27.95 | 0.907 | 0.420 | 1 | 0 | 96 | 5 | 11 | 1.8 | `a3ca0b` |
| world | True | 2 | 3.851 | 0.544 | 27.69 | 0.907 | 0.420 | 0 | 0 | 96 | 5 | 11 | 1.9 | `0360cc` |
| world | True | 5 | 3.851 | 0.544 | 27.69 | 0.907 | 0.420 | 0 | 0 | 96 | 5 | 11 | 1.8 | `0360cc` |
| world | True | 30 | 3.851 | 0.544 | 27.69 | 0.907 | 0.420 | 0 | 0 | 96 | 5 | 11 | 1.9 | `0360cc` |
| world | True | None | 3.851 | 0.544 | 27.69 | 0.907 | 0.420 | 0 | 0 | 96 | 5 | 11 | 1.9 | `0360cc` |
| world | False | 0 | 6.582 | 0.402 | 37.77 | 0.907 | 0.542 | 5 | 0 | 34 | 1 | 18 | 1.5 | `b8e4da` |
| world | False | 1 | 6.582 | 0.399 | 37.27 | 0.907 | 0.542 | 4 | 0 | 34 | 1 | 18 | 2.1 | `85a26d` |
| world | False | 2 | 6.582 | 0.395 | 37.27 | 0.907 | 0.542 | 3 | 0 | 34 | 1 | 18 | 2.6 | `369517` |
| world | False | 5 | 6.582 | 0.395 | 37.27 | 0.907 | 0.542 | 2 | 0 | 34 | 1 | 18 | 3.6 | `2944bb` |
| world | False | 30 | 6.582 | 0.395 | 37.27 | 0.907 | 0.542 | 2 | 0 | 34 | 1 | 18 | 3.7 | `2944bb` |
| world | False | None | 6.582 | 0.395 | 37.27 | 0.907 | 0.542 | 2 | 0 | 34 | 1 | 18 | 3.6 | `2944bb` |


## ring_swapback_max_hops

| case | morph | value | disp | adj | dir | pp | iou | noncontig | split | unassigned_core | enclosed | short | wall_s | fp |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| states_uniform | True | 0 | 1.402 | 0.761 | 25.80 | 0.907 | 0.694 | 0 | 0 | 6 | 0 | 0 | 0.8 | `c20252` |
| states_uniform | True | 1 | 1.320 | 0.780 | 24.82 | 0.907 | 0.688 | 0 | 0 | 6 | 0 | 0 | 0.9 | `8037bc` |
| states_uniform | True | 2 | 1.320 | 0.780 | 24.82 | 0.907 | 0.688 | 0 | 0 | 6 | 0 | 0 | 0.8 | `8037bc` |
| states_uniform | True | 4 | 1.465 | 0.752 | 27.53 | 0.907 | 0.708 | 0 | 0 | 5 | 0 | 0 | 0.8 | `e2f48b` |
| states_uniform | True | 8 | 1.526 | 0.725 | 28.32 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 0.8 | `d4bfd1` |
| states_uniform | True | 32 | 1.526 | 0.725 | 28.32 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 0.8 | `d4bfd1` |
| states_uniform | True | None | 1.526 | 0.725 | 28.32 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 0.8 | `d4bfd1` |
| states_uniform | False | 0 | 1.456 | 0.743 | 27.82 | 0.907 | 0.735 | 0 | 0 | 7 | 0 | 0 | 1.0 | `fadbdb` |
| states_uniform | False | 1 | 1.456 | 0.734 | 28.44 | 0.907 | 0.749 | 0 | 0 | 5 | 0 | 0 | 1.0 | `c619d7` |
| states_uniform | False | 2 | 1.456 | 0.734 | 26.47 | 0.907 | 0.748 | 0 | 0 | 4 | 0 | 0 | 1.0 | `602e49` |
| states_uniform | False | 4 | 1.467 | 0.706 | 26.47 | 0.907 | 0.714 | 0 | 0 | 4 | 0 | 0 | 1.0 | `6dc984` |
| states_uniform | False | 8 | 1.555 | 0.615 | 30.92 | 0.907 | 0.758 | 0 | 0 | 2 | 0 | 0 | 1.0 | `611b32` |
| states_uniform | False | 32 | 2.238 | 0.523 | 34.23 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `db2447` |
| states_uniform | False | None | 2.238 | 0.523 | 34.23 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `db2447` |
| states_uniform_sq | True | 0 | 0.787 | 0.532 | 25.77 | 0.785 | 0.660 | 0 | 0 | 15 | 0 | 0 | 0.9 | `2c21ec` |
| states_uniform_sq | True | 1 | 0.787 | 0.550 | 25.16 | 0.785 | 0.692 | 0 | 0 | 12 | 0 | 0 | 0.8 | `831827` |
| states_uniform_sq | True | 2 | 0.778 | 0.532 | 25.16 | 0.785 | 0.689 | 0 | 0 | 11 | 0 | 0 | 0.9 | `c7c020` |
| states_uniform_sq | True | 4 | 0.699 | 0.514 | 22.28 | 0.785 | 0.674 | 0 | 0 | 11 | 0 | 0 | 1.1 | `d494b6` |
| states_uniform_sq | True | 8 | 0.745 | 0.459 | 24.82 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 1.3 | `02f6d0` |
| states_uniform_sq | True | 32 | 0.745 | 0.459 | 24.82 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 0.9 | `02f6d0` |
| states_uniform_sq | True | None | 0.745 | 0.459 | 24.82 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 1.0 | `02f6d0` |
| states_uniform_sq | False | 0 | 1.763 | 0.514 | 25.68 | 0.785 | 0.679 | 0 | 0 | 9 | 2 | 0 | 1.2 | `f987b6` |
| states_uniform_sq | False | 1 | 1.753 | 0.514 | 25.68 | 0.785 | 0.722 | 0 | 0 | 6 | 0 | 0 | 1.2 | `0dff83` |
| states_uniform_sq | False | 2 | 1.752 | 0.514 | 29.64 | 0.785 | 0.781 | 0 | 0 | 3 | 0 | 0 | 1.2 | `a61142` |
| states_uniform_sq | False | 4 | 1.752 | 0.495 | 30.70 | 0.785 | 0.779 | 0 | 0 | 3 | 0 | 0 | 1.2 | `c7e2d6` |
| states_uniform_sq | False | 8 | 1.583 | 0.468 | 30.20 | 0.785 | 0.801 | 0 | 0 | 1 | 0 | 0 | 1.2 | `0fae83` |
| states_uniform_sq | False | 32 | 1.583 | 0.468 | 30.20 | 0.785 | 0.801 | 0 | 0 | 1 | 0 | 0 | 1.2 | `0fae83` |
| states_uniform_sq | False | None | 1.583 | 0.468 | 30.20 | 0.785 | 0.801 | 0 | 0 | 1 | 0 | 0 | 1.2 | `0fae83` |
| states | True | 0 | 2.119 | 0.798 | 14.27 | 0.653 | 0.682 | 0 | 0 | 23 | 1 | 0 | 1.2 | `e8f351` |
| states | True | 1 | 2.119 | 0.807 | 14.39 | 0.653 | 0.690 | 0 | 0 | 22 | 0 | 0 | 1.2 | `b1e5c3` |
| states | True | 2 | 2.119 | 0.807 | 14.39 | 0.653 | 0.695 | 0 | 0 | 22 | 0 | 0 | 1.2 | `68cbd7` |
| states | True | 4 | 2.077 | 0.798 | 14.78 | 0.653 | 0.691 | 0 | 0 | 22 | 0 | 0 | 1.2 | `ae2869` |
| states | True | 8 | 2.095 | 0.798 | 14.78 | 0.653 | 0.684 | 0 | 0 | 21 | 0 | 0 | 1.2 | `4df76d` |
| states | True | 32 | 2.099 | 0.798 | 17.11 | 0.653 | 0.687 | 0 | 0 | 19 | 0 | 0 | 1.2 | `febe8e` |
| states | True | None | 2.099 | 0.798 | 17.11 | 0.653 | 0.687 | 0 | 0 | 19 | 0 | 0 | 1.3 | `febe8e` |
| states | False | 0 | 3.971 | 0.688 | 26.14 | 0.653 | 0.784 | 0 | 0 | 12 | 0 | 0 | 1.5 | `ebef5e` |
| states | False | 1 | 3.678 | 0.697 | 26.50 | 0.653 | 0.809 | 0 | 0 | 7 | 0 | 0 | 7.1 | `7d53d5` |
| states | False | 2 | 3.907 | 0.697 | 26.81 | 0.653 | 0.806 | 0 | 0 | 6 | 0 | 0 | 7.0 | `e9ef72` |
| states | False | 4 | 3.907 | 0.697 | 26.74 | 0.653 | 0.808 | 0 | 0 | 5 | 0 | 0 | 6.6 | `0b3d53` |
| states | False | 8 | 3.907 | 0.697 | 26.28 | 0.653 | 0.811 | 0 | 0 | 4 | 0 | 0 | 6.5 | `5527de` |
| states | False | 32 | 3.929 | 0.697 | 25.37 | 0.653 | 0.812 | 0 | 0 | 3 | 0 | 0 | 5.0 | `02c46d` |
| states | False | None | 3.929 | 0.697 | 25.37 | 0.653 | 0.812 | 0 | 0 | 3 | 0 | 0 | 6.7 | `02c46d` |
| districts | True | 0 | 4.468 | 0.532 | 25.74 | 0.907 | 0.689 | 0 | 2 | 55 | 2 | 0 | 3.8 | `1805d8` |
| districts | True | 1 | 4.448 | 0.542 | 25.84 | 0.907 | 0.690 | 0 | 1 | 55 | 0 | 0 | 4.2 | `1ce942` |
| districts | True | 2 | 4.455 | 0.537 | 26.08 | 0.907 | 0.689 | 0 | 0 | 55 | 0 | 0 | 5.8 | `f73812` |
| districts | True | 4 | 4.483 | 0.526 | 26.61 | 0.907 | 0.691 | 0 | 0 | 54 | 0 | 0 | 5.8 | `27530f` |
| districts | True | 8 | 4.497 | 0.521 | 26.61 | 0.907 | 0.683 | 0 | 0 | 55 | 0 | 0 | 5.9 | `46d677` |
| districts | True | 32 | 4.550 | 0.510 | 26.91 | 0.907 | 0.692 | 0 | 0 | 53 | 0 | 0 | 6.4 | `709785` |
| districts | True | None | 4.519 | 0.527 | 25.92 | 0.907 | 0.687 | 0 | 0 | 54 | 0 | 0 | 6.0 | `df64c3` |
| districts | False | 0 | 6.994 | 0.488 | 33.85 | 0.907 | 0.837 | 0 | 2 | 38 | 2 | 0 | 3.4 | `e0e765` |
| districts | False | 1 | 6.939 | 0.490 | 34.66 | 0.907 | 0.853 | 0 | 0 | 23 | 1 | 0 | 3.9 | `827a3f` |
| districts | False | 2 | 6.939 | 0.489 | 34.72 | 0.907 | 0.848 | 0 | 0 | 22 | 1 | 0 | 3.8 | `6d0af0` |
| districts | False | 4 | 6.960 | 0.484 | 34.96 | 0.907 | 0.850 | 0 | 0 | 21 | 1 | 0 | 3.8 | `8a5939` |
| districts | False | 8 | 6.971 | 0.491 | 35.19 | 0.907 | 0.852 | 0 | 0 | 18 | 0 | 0 | 4.2 | `b33849` |
| districts | False | 32 | 7.459 | 0.464 | 34.38 | 0.907 | 0.867 | 0 | 1 | 12 | 0 | 0 | 3.5 | `ca3fd5` |
| districts | False | None | 7.286 | 0.485 | 33.92 | 0.907 | 0.857 | 0 | 0 | 14 | 0 | 0 | 3.5 | `485616` |
| world | True | 0 | 3.722 | 0.603 | 24.44 | 0.907 | 0.427 | 2 | 0 | 104 | 7 | 11 | 1.6 | `753b93` |
| world | True | 1 | 3.708 | 0.625 | 26.45 | 0.907 | 0.425 | 1 | 0 | 102 | 6 | 11 | 1.6 | `ef40cd` |
| world | True | 2 | 3.709 | 0.619 | 25.79 | 0.907 | 0.418 | 1 | 0 | 103 | 6 | 11 | 1.8 | `a6b666` |
| world | True | 4 | 3.708 | 0.599 | 25.18 | 0.907 | 0.422 | 0 | 0 | 98 | 4 | 11 | 2.0 | `730871` |
| world | True | 8 | 3.851 | 0.541 | 27.69 | 0.907 | 0.424 | 0 | 0 | 95 | 4 | 11 | 1.8 | `819ab0` |
| world | True | 32 | 3.798 | 0.541 | 27.95 | 0.907 | 0.421 | 0 | 0 | 96 | 5 | 11 | 1.8 | `602eb8` |
| world | True | None | 3.851 | 0.544 | 27.69 | 0.907 | 0.420 | 0 | 0 | 96 | 5 | 11 | 1.9 | `0360cc` |
| world | False | 0 | 6.395 | 0.405 | 35.02 | 0.907 | 0.521 | 4 | 0 | 75 | 5 | 18 | 3.6 | `97b2c6` |
| world | False | 1 | 6.395 | 0.422 | 35.42 | 0.907 | 0.535 | 2 | 0 | 51 | 2 | 18 | 3.0 | `284806` |
| world | False | 2 | 6.395 | 0.415 | 36.11 | 0.907 | 0.535 | 2 | 0 | 45 | 2 | 18 | 3.2 | `ab3674` |
| world | False | 4 | 6.361 | 0.412 | 36.00 | 0.907 | 0.532 | 2 | 0 | 41 | 1 | 18 | 3.0 | `a22e0e` |
| world | False | 8 | 6.361 | 0.399 | 37.77 | 0.907 | 0.537 | 2 | 0 | 36 | 1 | 18 | 3.1 | `cb5dfe` |
| world | False | 32 | 6.753 | 0.392 | 38.32 | 0.907 | 0.540 | 2 | 0 | 34 | 1 | 18 | 3.3 | `dcb8d7` |
| world | False | None | 6.582 | 0.395 | 37.27 | 0.907 | 0.542 | 2 | 0 | 34 | 1 | 18 | 3.6 | `2944bb` |


## distance_x_outside

| case | morph | value | disp | adj | dir | pp | iou | noncontig | split | unassigned_core | enclosed | short | wall_s | fp |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| states_uniform | True | None | 1.526 | 0.725 | 28.32 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 0.8 | `d4bfd1` |
| states_uniform | True | dw=0.25,op=0.0 | 1.402 | 0.780 | 24.62 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 1.0 | `ce0e0f` |
| states_uniform | True | dw=0.25,op=0.5 | 1.562 | 0.716 | 31.17 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 1.1 | `cffa59` |
| states_uniform | True | dw=0.25,op=1.0 | 1.504 | 0.725 | 29.32 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 1.2 | `d7b9da` |
| states_uniform | True | dw=0.25,op=2.0 | 1.504 | 0.596 | 33.17 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 1.3 | `f97ce5` |
| states_uniform | True | dw=0.25,op=4.0 | 1.529 | 0.670 | 29.80 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 1.3 | `4b6de4` |
| states_uniform | True | dw=1.0,op=0.0 | 1.337 | 0.771 | 21.17 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 1.3 | `22582a` |
| states_uniform | True | dw=1.0,op=0.5 | 1.526 | 0.716 | 26.83 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 1.3 | `e37ae5` |
| states_uniform | True | dw=1.0,op=2.0 | 1.504 | 0.569 | 38.58 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 1.3 | `ab65c7` |
| states_uniform | True | dw=1.0,op=4.0 | 1.529 | 0.560 | 31.17 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 1.3 | `7e1c68` |
| states_uniform | True | dw=4.0,op=0.0 | 1.402 | 0.761 | 23.74 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 1.3 | `43e2a9` |
| states_uniform | True | dw=4.0,op=0.5 | 1.320 | 0.771 | 21.89 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 1.3 | `891bc8` |
| states_uniform | True | dw=4.0,op=1.0 | 1.320 | 0.706 | 27.62 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 1.3 | `6bf7fc` |
| states_uniform | True | dw=4.0,op=2.0 | 1.504 | 0.550 | 35.70 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 1.3 | `3510fe` |
| states_uniform | True | dw=4.0,op=4.0 | 1.529 | 0.679 | 26.07 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 1.3 | `06f7f1` |
| states_uniform | False | None | 2.238 | 0.523 | 34.23 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `db2447` |
| states_uniform | False | dw=0.25,op=0.0 | 2.241 | 0.633 | 33.48 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.1 | `3bef16` |
| states_uniform | False | dw=0.25,op=0.5 | 2.373 | 0.550 | 41.93 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `c2a1d3` |
| states_uniform | False | dw=0.25,op=1.0 | 1.855 | 0.514 | 41.29 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `851b70` |
| states_uniform | False | dw=0.25,op=2.0 | 2.651 | 0.688 | 26.47 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `2746cd` |
| states_uniform | False | dw=0.25,op=4.0 | 1.945 | 0.578 | 34.23 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `5a5550` |
| states_uniform | False | dw=1.0,op=0.0 | 2.305 | 0.642 | 26.47 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `d6b44d` |
| states_uniform | False | dw=1.0,op=0.5 | 2.365 | 0.514 | 33.26 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `9fab23` |
| states_uniform | False | dw=1.0,op=2.0 | 2.690 | 0.688 | 29.81 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `3685aa` |
| states_uniform | False | dw=1.0,op=4.0 | 2.305 | 0.633 | 26.47 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `c7b93e` |
| states_uniform | False | dw=4.0,op=0.0 | 2.651 | 0.596 | 29.08 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `e5c15a` |
| states_uniform | False | dw=4.0,op=0.5 | 2.554 | 0.651 | 29.81 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `d970d6` |
| states_uniform | False | dw=4.0,op=1.0 | 2.260 | 0.514 | 39.33 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `361add` |
| states_uniform | False | dw=4.0,op=2.0 | 2.250 | 0.523 | 39.35 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `733a93` |
| states_uniform | False | dw=4.0,op=4.0 | 2.241 | 0.596 | 28.69 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `9a5ae8` |
| states_uniform_sq | True | None | 0.745 | 0.459 | 24.82 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 1.0 | `02f6d0` |
| states_uniform_sq | True | dw=0.25,op=0.0 | 0.854 | 0.578 | 33.48 | 0.785 | 0.701 | 0 | 0 | 10 | 0 | 0 | 0.9 | `11e211` |
| states_uniform_sq | True | dw=0.25,op=0.5 | 0.854 | 0.578 | 33.48 | 0.785 | 0.701 | 0 | 0 | 10 | 0 | 0 | 0.9 | `11e211` |
| states_uniform_sq | True | dw=0.25,op=1.0 | 0.766 | 0.440 | 36.42 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 0.9 | `cb5b0c` |
| states_uniform_sq | True | dw=0.25,op=2.0 | 0.766 | 0.440 | 36.42 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 1.0 | `cb5b0c` |
| states_uniform_sq | True | dw=0.25,op=4.0 | 0.854 | 0.431 | 36.75 | 0.785 | 0.659 | 0 | 0 | 11 | 0 | 0 | 1.0 | `8e1b32` |
| states_uniform_sq | True | dw=1.0,op=0.0 | 0.786 | 0.569 | 24.82 | 0.785 | 0.701 | 0 | 0 | 10 | 0 | 0 | 0.9 | `cc5407` |
| states_uniform_sq | True | dw=1.0,op=0.5 | 0.786 | 0.569 | 24.82 | 0.785 | 0.701 | 0 | 0 | 10 | 0 | 0 | 1.1 | `cc5407` |
| states_uniform_sq | True | dw=1.0,op=2.0 | 0.745 | 0.459 | 24.82 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 1.8 | `02f6d0` |
| states_uniform_sq | True | dw=1.0,op=4.0 | 0.877 | 0.450 | 32.32 | 0.785 | 0.659 | 0 | 0 | 11 | 0 | 0 | 0.8 | `bc5369` |
| states_uniform_sq | True | dw=4.0,op=0.0 | 0.808 | 0.587 | 22.47 | 0.785 | 0.701 | 0 | 0 | 10 | 0 | 0 | 0.8 | `e407c9` |
| states_uniform_sq | True | dw=4.0,op=0.5 | 0.808 | 0.587 | 22.47 | 0.785 | 0.701 | 0 | 0 | 10 | 0 | 0 | 6.7 | `e407c9` |
| states_uniform_sq | True | dw=4.0,op=1.0 | 0.789 | 0.514 | 25.80 | 0.785 | 0.669 | 0 | 0 | 10 | 0 | 0 | 0.9 | `6f7246` |
| states_uniform_sq | True | dw=4.0,op=2.0 | 0.766 | 0.459 | 24.82 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 3.6 | `94f4c7` |
| states_uniform_sq | True | dw=4.0,op=4.0 | 0.877 | 0.450 | 32.32 | 0.785 | 0.659 | 0 | 0 | 11 | 0 | 0 | 0.9 | `64549a` |
| states_uniform_sq | False | None | 1.583 | 0.468 | 30.20 | 0.785 | 0.801 | 0 | 0 | 1 | 0 | 0 | 1.2 | `0fae83` |
| states_uniform_sq | False | dw=0.25,op=0.0 | 1.193 | 0.532 | 31.56 | 0.785 | 0.793 | 0 | 0 | 1 | 0 | 0 | 1.2 | `47566c` |
| states_uniform_sq | False | dw=0.25,op=0.5 | 1.311 | 0.495 | 29.27 | 0.785 | 0.793 | 0 | 0 | 1 | 0 | 0 | 1.2 | `0cc2d6` |
| states_uniform_sq | False | dw=0.25,op=1.0 | 1.502 | 0.459 | 29.42 | 0.785 | 0.801 | 0 | 0 | 1 | 0 | 0 | 1.2 | `5e73b6` |
| states_uniform_sq | False | dw=0.25,op=2.0 | 1.294 | 0.404 | 33.48 | 0.785 | 0.789 | 0 | 0 | 1 | 0 | 0 | 1.2 | `31ab9c` |
| states_uniform_sq | False | dw=0.25,op=4.0 | 1.507 | 0.330 | 40.04 | 0.785 | 0.798 | 0 | 0 | 1 | 0 | 0 | 1.2 | `00a081` |
| states_uniform_sq | False | dw=1.0,op=0.0 | 1.252 | 0.514 | 20.61 | 0.785 | 0.789 | 0 | 0 | 1 | 0 | 0 | 1.2 | `e658eb` |
| states_uniform_sq | False | dw=1.0,op=0.5 | 1.408 | 0.486 | 31.68 | 0.785 | 0.793 | 0 | 0 | 1 | 0 | 0 | 1.2 | `0c0e98` |
| states_uniform_sq | False | dw=1.0,op=2.0 | 1.502 | 0.468 | 29.64 | 0.785 | 0.789 | 0 | 0 | 1 | 0 | 0 | 1.2 | `f91ff5` |
| states_uniform_sq | False | dw=1.0,op=4.0 | 1.704 | 0.385 | 34.25 | 0.785 | 0.784 | 0 | 0 | 1 | 0 | 0 | 1.2 | `163d72` |
| states_uniform_sq | False | dw=4.0,op=0.0 | 1.272 | 0.459 | 32.38 | 0.785 | 0.793 | 0 | 0 | 1 | 0 | 0 | 1.2 | `293604` |
| states_uniform_sq | False | dw=4.0,op=0.5 | 1.188 | 0.413 | 33.99 | 0.785 | 0.793 | 0 | 0 | 1 | 0 | 0 | 1.2 | `aeb1ec` |
| states_uniform_sq | False | dw=4.0,op=1.0 | 1.188 | 0.404 | 33.17 | 0.785 | 0.793 | 0 | 0 | 1 | 0 | 0 | 1.2 | `2faab1` |
| states_uniform_sq | False | dw=4.0,op=2.0 | 1.507 | 0.440 | 26.14 | 0.785 | 0.789 | 0 | 0 | 1 | 0 | 0 | 1.2 | `a73946` |
| states_uniform_sq | False | dw=4.0,op=4.0 | 1.526 | 0.440 | 29.64 | 0.785 | 0.786 | 0 | 0 | 1 | 0 | 0 | 1.2 | `17a5af` |
| states | True | None | 2.099 | 0.798 | 17.11 | 0.653 | 0.687 | 0 | 0 | 19 | 0 | 0 | 1.3 | `febe8e` |
| states | True | dw=0.25,op=0.0 | 2.368 | 0.780 | 14.93 | 0.666 | 0.698 | 0 | 0 | 17 | 0 | 0 | 1.2 | `8d8dfd` |
| states | True | dw=0.25,op=0.5 | 2.379 | 0.771 | 15.42 | 0.666 | 0.685 | 0 | 0 | 18 | 0 | 0 | 1.2 | `856e26` |
| states | True | dw=0.25,op=1.0 | 2.255 | 0.771 | 18.52 | 0.653 | 0.688 | 0 | 0 | 19 | 0 | 0 | 1.2 | `b9ec78` |
| states | True | dw=0.25,op=2.0 | 2.555 | 0.670 | 20.50 | 0.653 | 0.691 | 0 | 0 | 17 | 0 | 0 | 1.2 | `c9f433` |
| states | True | dw=0.25,op=4.0 | 2.814 | 0.789 | 18.50 | 0.653 | 0.691 | 0 | 0 | 17 | 0 | 0 | 4.5 | `c55cca` |
| states | True | dw=1.0,op=0.0 | 2.555 | 0.817 | 14.27 | 0.666 | 0.699 | 0 | 0 | 17 | 0 | 0 | 1.2 | `0c6853` |
| states | True | dw=1.0,op=0.5 | 2.562 | 0.826 | 14.93 | 0.666 | 0.684 | 0 | 0 | 19 | 0 | 0 | 1.2 | `07a773` |
| states | True | dw=1.0,op=2.0 | 2.576 | 0.743 | 15.31 | 0.653 | 0.694 | 0 | 0 | 17 | 0 | 0 | 1.2 | `53ecf8` |
| states | True | dw=1.0,op=4.0 | 2.576 | 0.706 | 17.15 | 0.653 | 0.675 | 0 | 0 | 18 | 0 | 0 | 1.2 | `115a9e` |
| states | True | dw=4.0,op=0.0 | 2.387 | 0.817 | 13.40 | 0.653 | 0.699 | 0 | 0 | 17 | 0 | 0 | 1.2 | `d195f9` |
| states | True | dw=4.0,op=0.5 | 2.387 | 0.798 | 14.45 | 0.653 | 0.684 | 0 | 0 | 19 | 0 | 0 | 1.2 | `dccac5` |
| states | True | dw=4.0,op=1.0 | 2.495 | 0.771 | 14.78 | 0.653 | 0.682 | 0 | 0 | 18 | 0 | 0 | 1.2 | `b115e7` |
| states | True | dw=4.0,op=2.0 | 3.032 | 0.642 | 15.89 | 0.653 | 0.681 | 0 | 0 | 18 | 0 | 0 | 1.2 | `c68bd1` |
| states | True | dw=4.0,op=4.0 | 2.525 | 0.725 | 15.36 | 0.653 | 0.677 | 0 | 0 | 18 | 0 | 0 | 1.2 | `9ee88a` |
| states | False | None | 3.929 | 0.697 | 25.37 | 0.653 | 0.812 | 0 | 0 | 3 | 0 | 0 | 6.7 | `02c46d` |
| states | False | dw=0.25,op=0.0 | 4.176 | 0.679 | 23.26 | 0.680 | 0.850 | 0 | 0 | 0 | 0 | 0 | 1.1 | `9cca12` |
| states | False | dw=0.25,op=0.5 | 4.757 | 0.615 | 30.19 | 0.653 | 0.851 | 0 | 0 | 0 | 0 | 0 | 1.1 | `269bbe` |
| states | False | dw=0.25,op=1.0 | 4.277 | 0.651 | 26.56 | 0.680 | 0.815 | 0 | 0 | 3 | 0 | 0 | 1.3 | `cc5db3` |
| states | False | dw=0.25,op=2.0 | 4.465 | 0.679 | 24.95 | 0.666 | 0.845 | 0 | 0 | 0 | 0 | 0 | 1.2 | `a012ab` |
| states | False | dw=0.25,op=4.0 | 3.590 | 0.642 | 24.98 | 0.680 | 0.827 | 0 | 0 | 1 | 0 | 0 | 1.1 | `eed0c9` |
| states | False | dw=1.0,op=0.0 | 4.112 | 0.697 | 22.09 | 0.680 | 0.852 | 0 | 0 | 0 | 0 | 0 | 1.1 | `52f7e1` |
| states | False | dw=1.0,op=0.5 | 4.259 | 0.725 | 20.65 | 0.653 | 0.834 | 0 | 0 | 3 | 0 | 0 | 1.3 | `a3f021` |
| states | False | dw=1.0,op=2.0 | 4.277 | 0.661 | 24.16 | 0.653 | 0.851 | 0 | 0 | 0 | 0 | 0 | 1.0 | `ad8bce` |
| states | False | dw=1.0,op=4.0 | 4.112 | 0.670 | 22.93 | 0.653 | 0.829 | 0 | 0 | 1 | 0 | 0 | 13.9 | `d52306` |
| states | False | dw=4.0,op=0.0 | 3.117 | 0.743 | 20.50 | 0.653 | 0.804 | 0 | 0 | 5 | 0 | 0 | 1.0 | `6a040e` |
| states | False | dw=4.0,op=0.5 | 3.352 | 0.716 | 20.50 | 0.666 | 0.815 | 0 | 0 | 4 | 0 | 0 | 1.0 | `b038fd` |
| states | False | dw=4.0,op=1.0 | 3.541 | 0.642 | 18.85 | 0.653 | 0.799 | 0 | 0 | 5 | 0 | 0 | 1.0 | `9800dd` |
| states | False | dw=4.0,op=2.0 | 3.544 | 0.642 | 22.69 | 0.653 | 0.770 | 0 | 0 | 6 | 0 | 0 | 1.0 | `06f27e` |
| states | False | dw=4.0,op=4.0 | 4.096 | 0.725 | 20.65 | 0.653 | 0.794 | 0 | 0 | 4 | 0 | 0 | 4.8 | `491c69` |
| districts | True | None | 4.519 | 0.527 | 25.92 | 0.907 | 0.687 | 0 | 0 | 54 | 0 | 0 | 6.0 | `df64c3` |
| districts | True | dw=0.25,op=0.0 | 4.641 | 0.544 | 30.87 | 0.907 | 0.700 | 0 | 0 | 51 | 0 | 0 | 6.0 | `7e3f66` |
| districts | True | dw=0.25,op=0.5 | 5.211 | 0.532 | 33.18 | 0.907 | 0.719 | 0 | 0 | 45 | 0 | 0 | 7.3 | `493eb6` |
| districts | True | dw=0.25,op=1.0 | 4.808 | 0.499 | 34.26 | 0.907 | 0.690 | 0 | 1 | 52 | 0 | 0 | 8.0 | `6a486c` |
| districts | True | dw=0.25,op=2.0 | 4.877 | 0.488 | 34.78 | 0.907 | 0.703 | 0 | 1 | 50 | 0 | 0 | 13.3 | `a0d6b4` |
| districts | True | dw=0.25,op=4.0 | 5.133 | 0.453 | 35.72 | 0.907 | 0.694 | 0 | 2 | 51 | 1 | 0 | 4.4 | `8d8d04` |
| districts | True | dw=1.0,op=0.0 | 4.621 | 0.552 | 28.34 | 0.907 | 0.698 | 0 | 0 | 51 | 1 | 0 | 3.8 | `0e8329` |
| districts | True | dw=1.0,op=0.5 | 4.874 | 0.572 | 28.40 | 0.907 | 0.708 | 0 | 0 | 49 | 0 | 0 | 3.9 | `6576b6` |
| districts | True | dw=1.0,op=2.0 | 4.986 | 0.511 | 31.85 | 0.907 | 0.709 | 0 | 0 | 48 | 1 | 0 | 4.2 | `8587df` |
| districts | True | dw=1.0,op=4.0 | 5.067 | 0.487 | 32.79 | 0.907 | 0.713 | 0 | 1 | 47 | 1 | 0 | 5.0 | `aab07e` |
| districts | True | dw=4.0,op=0.0 | 4.678 | 0.569 | 25.29 | 0.907 | 0.698 | 0 | 0 | 50 | 0 | 0 | 6.3 | `5a12fe` |
| districts | True | dw=4.0,op=0.5 | 4.647 | 0.578 | 24.85 | 0.907 | 0.693 | 0 | 0 | 54 | 0 | 0 | 6.0 | `551b0e` |
| districts | True | dw=4.0,op=1.0 | 4.611 | 0.541 | 25.05 | 0.907 | 0.687 | 0 | 0 | 54 | 1 | 0 | 6.5 | `30454e` |
| districts | True | dw=4.0,op=2.0 | 4.999 | 0.505 | 29.07 | 0.907 | 0.706 | 0 | 2 | 49 | 2 | 0 | 6.6 | `f51806` |
| districts | True | dw=4.0,op=4.0 | 4.896 | 0.463 | 33.85 | 0.907 | 0.690 | 0 | 0 | 52 | 0 | 0 | 6.5 | `03b002` |
| districts | False | None | 7.286 | 0.485 | 33.92 | 0.907 | 0.857 | 0 | 0 | 14 | 0 | 0 | 3.5 | `485616` |
| districts | False | dw=0.25,op=0.0 | 6.526 | 0.484 | 38.69 | 0.907 | 0.843 | 0 | 0 | 14 | 0 | 0 | 3.3 | `b0a5d2` |
| districts | False | dw=0.25,op=0.5 | 7.251 | 0.425 | 42.41 | 0.907 | 0.887 | 0 | 1 | 10 | 0 | 0 | 10.1 | `089099` |
| districts | False | dw=0.25,op=1.0 | 6.814 | 0.460 | 37.91 | 0.907 | 0.869 | 0 | 1 | 14 | 0 | 0 | 3.7 | `a6ed7f` |
| districts | False | dw=0.25,op=2.0 | 7.259 | 0.406 | 40.42 | 0.907 | 0.890 | 0 | 0 | 10 | 0 | 0 | 5.2 | `fb76ec` |
| districts | False | dw=0.25,op=4.0 | 7.491 | 0.422 | 43.72 | 0.907 | 0.878 | 0 | 3 | 12 | 0 | 0 | 10.1 | `37a381` |
| districts | False | dw=1.0,op=0.0 | 7.396 | 0.485 | 35.57 | 0.907 | 0.850 | 0 | 1 | 12 | 0 | 0 | 4.2 | `6ae019` |
| districts | False | dw=1.0,op=0.5 | 7.280 | 0.473 | 36.13 | 0.907 | 0.874 | 0 | 1 | 12 | 0 | 0 | 5.8 | `1d7c28` |
| districts | False | dw=1.0,op=2.0 | 7.634 | 0.455 | 36.39 | 0.907 | 0.888 | 0 | 1 | 10 | 1 | 0 | 3.8 | `b7566a` |
| districts | False | dw=1.0,op=4.0 | 7.868 | 0.453 | 35.72 | 0.907 | 0.881 | 0 | 2 | 10 | 1 | 0 | 5.9 | `8db2a9` |
| districts | False | dw=4.0,op=0.0 | 6.180 | 0.543 | 27.43 | 0.907 | 0.778 | 0 | 1 | 27 | 0 | 0 | 3.5 | `e7ee64` |
| districts | False | dw=4.0,op=0.5 | 6.345 | 0.491 | 30.15 | 0.907 | 0.807 | 0 | 0 | 28 | 0 | 0 | 3.7 | `9ccf59` |
| districts | False | dw=4.0,op=1.0 | 6.862 | 0.518 | 29.02 | 0.907 | 0.829 | 0 | 1 | 23 | 0 | 0 | 3.3 | `b40262` |
| districts | False | dw=4.0,op=2.0 | 6.957 | 0.488 | 31.96 | 0.907 | 0.823 | 0 | 2 | 19 | 0 | 0 | 11.8 | `74cc40` |
| districts | False | dw=4.0,op=4.0 | 7.858 | 0.467 | 32.57 | 0.907 | 0.857 | 0 | 0 | 13 | 0 | 0 | 3.5 | `36c507` |
| world | True | None | 3.851 | 0.544 | 27.69 | 0.907 | 0.420 | 0 | 0 | 96 | 5 | 11 | 1.9 | `0360cc` |
| world | True | dw=0.25,op=0.0 | 3.426 | 0.614 | 33.06 | 0.907 | 0.414 | 0 | 0 | 95 | 1 | 6 | 1.7 | `4959bc` |
| world | True | dw=0.25,op=0.5 | 3.574 | 0.630 | 30.82 | 0.907 | 0.406 | 0 | 0 | 96 | 1 | 5 | 1.7 | `32b330` |
| world | True | dw=0.25,op=1.0 | 4.099 | 0.510 | 34.84 | 0.907 | 0.435 | 2 | 0 | 94 | 2 | 11 | 2.0 | `8d4734` |
| world | True | dw=0.25,op=2.0 | 4.234 | 0.468 | 36.86 | 0.907 | 0.435 | 1 | 0 | 103 | 8 | 12 | 2.3 | `9955a0` |
| world | True | dw=0.25,op=4.0 | 4.234 | 0.406 | 37.24 | 0.907 | 0.434 | 2 | 0 | 103 | 6 | 11 | 2.0 | `562bc7` |
| world | True | dw=1.0,op=0.0 | 3.301 | 0.631 | 26.46 | 0.907 | 0.411 | 0 | 0 | 97 | 1 | 6 | 1.7 | `2c7538` |
| world | True | dw=1.0,op=0.5 | 3.536 | 0.621 | 26.62 | 0.907 | 0.407 | 0 | 0 | 97 | 2 | 5 | 1.7 | `9e0f4c` |
| world | True | dw=1.0,op=2.0 | 4.253 | 0.490 | 30.97 | 0.907 | 0.436 | 1 | 0 | 103 | 6 | 14 | 1.8 | `26ec7e` |
| world | True | dw=1.0,op=4.0 | 4.367 | 0.487 | 34.08 | 0.907 | 0.434 | 1 | 0 | 103 | 6 | 11 | 1.7 | `13bad6` |
| world | True | dw=4.0,op=0.0 | 3.509 | 0.588 | 24.41 | 0.907 | 0.414 | 0 | 0 | 94 | 0 | 6 | 1.6 | `e955c1` |
| world | True | dw=4.0,op=0.5 | 3.351 | 0.631 | 19.48 | 0.907 | 0.399 | 0 | 0 | 99 | 1 | 6 | 1.8 | `7374fc` |
| world | True | dw=4.0,op=1.0 | 3.487 | 0.521 | 26.46 | 0.907 | 0.401 | 0 | 0 | 100 | 2 | 11 | 1.9 | `9ebaa1` |
| world | True | dw=4.0,op=2.0 | 4.270 | 0.484 | 32.28 | 0.907 | 0.427 | 0 | 0 | 100 | 5 | 13 | 2.0 | `a85853` |
| world | True | dw=4.0,op=4.0 | 4.443 | 0.495 | 29.57 | 0.907 | 0.432 | 2 | 0 | 101 | 9 | 12 | 3.0 | `8240b6` |
| world | False | None | 6.582 | 0.395 | 37.27 | 0.907 | 0.542 | 2 | 0 | 34 | 1 | 18 | 3.6 | `2944bb` |
| world | False | dw=0.25,op=0.0 | 6.430 | 0.397 | 38.79 | 0.907 | 0.535 | 0 | 0 | 29 | 0 | 18 | 1.5 | `364cd5` |
| world | False | dw=0.25,op=0.5 | 6.456 | 0.430 | 37.97 | 0.907 | 0.522 | 1 | 0 | 32 | 0 | 17 | 1.6 | `b8c42d` |
| world | False | dw=0.25,op=1.0 | 6.333 | 0.302 | 47.07 | 0.907 | 0.546 | 2 | 0 | 34 | 0 | 20 | 2.7 | `ea5923` |
| world | False | dw=0.25,op=2.0 | 8.402 | 0.265 | 54.62 | 0.907 | 0.506 | 2 | 0 | 28 | 0 | 18 | 1.7 | `099534` |
| world | False | dw=0.25,op=4.0 | 10.281 | 0.214 | 59.20 | 0.907 | 0.474 | 4 | 0 | 31 | 2 | 18 | 3.7 | `ef8ea9` |
| world | False | dw=1.0,op=0.0 | 7.934 | 0.511 | 29.31 | 0.907 | 0.523 | 0 | 0 | 32 | 1 | 17 | 1.7 | `8a7e7a` |
| world | False | dw=1.0,op=0.5 | 6.781 | 0.419 | 34.18 | 0.907 | 0.539 | 2 | 0 | 34 | 1 | 17 | 3.6 | `b6735d` |
| world | False | dw=1.0,op=2.0 | 7.636 | 0.340 | 41.70 | 0.907 | 0.531 | 2 | 0 | 29 | 1 | 18 | 4.9 | `0489d0` |
| world | False | dw=1.0,op=4.0 | 10.066 | 0.286 | 48.15 | 0.907 | 0.483 | 3 | 0 | 33 | 2 | 18 | 4.1 | `f7db9b` |
| world | False | dw=4.0,op=0.0 | 5.574 | 0.552 | 28.12 | 0.907 | 0.544 | 1 | 0 | 46 | 1 | 20 | 2.5 | `2934c7` |
| world | False | dw=4.0,op=0.5 | 4.855 | 0.557 | 25.06 | 0.907 | 0.553 | 2 | 0 | 48 | 1 | 20 | 7.0 | `9c35cc` |
| world | False | dw=4.0,op=1.0 | 5.311 | 0.557 | 24.06 | 0.907 | 0.559 | 2 | 0 | 48 | 1 | 21 | 5.6 | `7c5150` |
| world | False | dw=4.0,op=2.0 | 6.284 | 0.403 | 33.02 | 0.907 | 0.552 | 1 | 0 | 41 | 1 | 19 | 2.0 | `7666a7` |
| world | False | dw=4.0,op=4.0 | 8.346 | 0.330 | 32.33 | 0.907 | 0.494 | 2 | 0 | 28 | 0 | 17 | 2.4 | `b54ba3` |


## extra_tile_rings

| case | morph | value | disp | adj | dir | pp | iou | noncontig | split | unassigned_core | enclosed | short | wall_s | fp |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| states_uniform | True | 0 | 1.303 | 0.807 | 20.62 | 0.907 | 0.723 | 0 | 0 | 8 | 0 | 0 | 1.3 | `40e37a` |
| states_uniform | True | 2 | 1.767 | 0.651 | 29.00 | 0.907 | 0.663 | 0 | 0 | 8 | 0 | 0 | 1.3 | `0b4e7f` |
| states_uniform | True | 3 | 1.191 | 0.661 | 23.02 | 0.907 | 0.730 | 0 | 0 | 7 | 0 | 0 | 1.4 | `e0607f` |
| states_uniform | True | 5 | 1.772 | 0.505 | 39.03 | 0.907 | 0.613 | 0 | 0 | 8 | 0 | 0 | 1.4 | `37d31a` |
| states_uniform | True | None | 1.526 | 0.725 | 28.32 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 0.8 | `d4bfd1` |
| states_uniform | False | 0 | 2.277 | 0.706 | 24.30 | 0.907 | 0.808 | 0 | 0 | 0 | 0 | 0 | 1.0 | `7c0290` |
| states_uniform | False | 2 | 1.834 | 0.578 | 30.19 | 0.907 | 0.713 | 0 | 0 | 0 | 0 | 0 | 1.0 | `45fd4a` |
| states_uniform | False | 3 | 2.089 | 0.413 | 39.39 | 0.907 | 0.762 | 0 | 0 | 2 | 0 | 0 | 1.1 | `2b19fd` |
| states_uniform | False | 5 | 1.862 | 0.413 | 33.72 | 0.907 | 0.640 | 0 | 0 | 3 | 0 | 0 | 1.1 | `644655` |
| states_uniform | False | None | 2.238 | 0.523 | 34.23 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `db2447` |
| states_uniform_sq | True | 0 | 0.791 | 0.596 | 15.95 | 0.785 | 0.681 | 0 | 0 | 11 | 0 | 0 | 0.9 | `f8430f` |
| states_uniform_sq | True | 2 | 1.467 | 0.367 | 34.04 | 0.785 | 0.703 | 0 | 0 | 11 | 0 | 0 | 0.9 | `fe0c34` |
| states_uniform_sq | True | 3 | 0.824 | 0.450 | 26.47 | 0.785 | 0.655 | 0 | 0 | 12 | 1 | 0 | 4.1 | `888a6f` |
| states_uniform_sq | True | 5 | 1.075 | 0.422 | 24.15 | 0.785 | 0.589 | 0 | 0 | 14 | 0 | 0 | 1.3 | `8f92d6` |
| states_uniform_sq | True | None | 0.745 | 0.459 | 24.82 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 1.0 | `02f6d0` |
| states_uniform_sq | False | 0 | 1.468 | 0.514 | 30.20 | 0.785 | 0.779 | 0 | 0 | 0 | 0 | 0 | 1.2 | `fde096` |
| states_uniform_sq | False | 2 | 1.353 | 0.431 | 28.89 | 0.785 | 0.779 | 0 | 0 | 0 | 0 | 0 | 1.3 | `6a3fdb` |
| states_uniform_sq | False | 3 | 1.057 | 0.312 | 34.21 | 0.785 | 0.619 | 0 | 0 | 6 | 0 | 0 | 1.3 | `79bbe5` |
| states_uniform_sq | False | 5 | 1.028 | 0.422 | 33.19 | 0.785 | 0.655 | 0 | 0 | 8 | 0 | 0 | 1.3 | `f38146` |
| states_uniform_sq | False | None | 1.583 | 0.468 | 30.20 | 0.785 | 0.801 | 0 | 0 | 1 | 0 | 0 | 1.2 | `0fae83` |
| states | True | 0 | 2.485 | 0.798 | 17.42 | 0.666 | 0.693 | 0 | 0 | 19 | 0 | 0 | 1.1 | `efdecc` |
| states | True | 2 | 2.683 | 0.706 | 19.93 | 0.666 | 0.643 | 1 | 0 | 21 | 0 | 0 | 1.2 | `e5bd26` |
| states | True | 3 | 2.667 | 0.706 | 17.53 | 0.653 | 0.640 | 1 | 0 | 28 | 0 | 0 | 1.5 | `bea857` |
| states | True | 5 | 2.610 | 0.596 | 20.16 | 0.666 | 0.651 | 1 | 0 | 22 | 0 | 0 | 1.4 | `1e6369` |
| states | True | None | 2.099 | 0.798 | 17.11 | 0.653 | 0.687 | 0 | 0 | 19 | 0 | 0 | 1.3 | `febe8e` |
| states | False | 0 | 4.865 | 0.752 | 24.30 | 0.680 | 0.882 | 0 | 0 | 0 | 0 | 1 | 1.1 | `bce61e` |
| states | False | 2 | 3.558 | 0.734 | 20.32 | 0.653 | 0.793 | 0 | 0 | 3 | 0 | 0 | 1.3 | `ff79ed` |
| states | False | 3 | 3.057 | 0.651 | 22.44 | 0.653 | 0.720 | 4 | 0 | 9 | 0 | 0 | 2.0 | `463715` |
| states | False | 5 | 2.913 | 0.560 | 28.49 | 0.653 | 0.634 | 0 | 0 | 23 | 0 | 0 | 3.3 | `b07fa5` |
| states | False | None | 3.929 | 0.697 | 25.37 | 0.653 | 0.812 | 0 | 0 | 3 | 0 | 0 | 6.7 | `02c46d` |
| districts | True | 0 | 4.801 | 0.542 | 24.58 | 0.907 | 0.717 | 0 | 0 | 51 | 1 | 0 | 5.5 | `620940` |
| districts | True | 2 | 4.937 | 0.510 | 30.05 | 0.907 | 0.697 | 0 | 0 | 54 | 2 | 0 | 7.3 | `f2d126` |
| districts | True | 3 | 4.970 | 0.378 | 40.10 | 0.907 | 0.624 | 0 | 5 | 67 | 1 | 0 | 26.1 | `9756a3` |
| districts | True | 5 | 4.524 | 0.415 | 37.69 | 0.907 | 0.628 | 0 | 3 | 80 | 1 | 0 | 41.3 | `d177a3` |
| districts | True | None | 4.519 | 0.527 | 25.92 | 0.907 | 0.687 | 0 | 0 | 54 | 0 | 0 | 6.0 | `df64c3` |
| districts | False | 0 | 7.894 | 0.466 | 36.94 | 0.907 | 0.906 | 0 | 1 | 2 | 0 | 0 | 14.9 | `4e2769` |
| districts | False | 2 | 8.293 | 0.406 | 39.50 | 0.907 | 0.890 | 0 | 1 | 8 | 0 | 0 | 5.0 | `5618a0` |
| districts | False | 3 | 5.548 | 0.357 | 42.37 | 0.907 | 0.638 | 0 | 6 | 42 | 1 | 0 | 16.9 | `62915d` |
| districts | False | 5 | 4.622 | 0.298 | 49.95 | 0.907 | 0.561 | 0 | 6 | 70 | 0 | 0 | 23.6 | `0f4ce2` |
| districts | False | None | 7.286 | 0.485 | 33.92 | 0.907 | 0.857 | 0 | 0 | 14 | 0 | 0 | 3.5 | `485616` |
| world | True | 0 | 3.048 | 0.654 | 22.94 | 0.907 | 0.418 | 0 | 0 | 100 | 4 | 24 | 1.4 | `3f167f` |
| world | True | 2 | 4.346 | 0.437 | 40.29 | 0.907 | 0.417 | 1 | 0 | 94 | 2 | 17 | 2.5 | `72f293` |
| world | True | 3 | 4.764 | 0.363 | 39.47 | 0.907 | 0.390 | 3 | 0 | 115 | 2 | 13 | 3.6 | `a0df99` |
| world | True | 5 | 4.425 | 0.332 | 39.13 | 0.907 | 0.338 | 6 | 0 | 129 | 1 | 15 | 3.0 | `ec3da2` |
| world | True | None | 3.851 | 0.544 | 27.69 | 0.907 | 0.420 | 0 | 0 | 96 | 5 | 11 | 1.9 | `0360cc` |
| world | False | 0 | 7.723 | 0.404 | 36.43 | 0.907 | 0.525 | 3 | 0 | 36 | 1 | 30 | 5.8 | `8ed05f` |
| world | False | 2 | 8.494 | 0.346 | 41.67 | 0.907 | 0.508 | 4 | 0 | 36 | 1 | 23 | 23.0 | `27664e` |
| world | False | 3 | 5.128 | 0.381 | 38.95 | 0.907 | 0.477 | 4 | 0 | 63 | 1 | 25 | 10.0 | `f7de96` |
| world | False | 5 | 4.078 | 0.356 | 38.33 | 0.907 | 0.414 | 1 | 0 | 68 | 0 | 28 | 9.9 | `37f3ce` |
| world | False | None | 6.582 | 0.395 | 37.27 | 0.907 | 0.542 | 2 | 0 | 34 | 1 | 18 | 3.6 | `2944bb` |


## min_overlap_frac

| case | morph | value | disp | adj | dir | pp | iou | noncontig | split | unassigned_core | enclosed | short | wall_s | fp |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| states_uniform | True | 0.02 | 1.464 | 0.661 | 29.08 | 0.907 | 0.715 | 0 | 0 | 4 | 0 | 0 | 1.4 | `de083e` |
| states_uniform | True | 0.25 | 1.896 | 0.688 | 26.83 | 0.907 | 0.750 | 0 | 0 | 10 | 0 | 0 | 1.4 | `b3b72a` |
| states_uniform | True | 0.5 | 1.697 | 0.789 | 28.32 | 0.907 | 0.720 | 0 | 0 | 17 | 0 | 0 | 1.4 | `89cdfd` |
| states_uniform | True | 0.75 | 1.457 | 0.752 | 20.84 | 0.907 | 0.688 | 0 | 0 | 26 | 0 | 0 | 1.4 | `ece4a3` |
| states_uniform | True | 1.0 | 2.713 | 0.596 | 28.49 | 0.907 | 0.391 | 0 | 0 | 85 | 0 | 0 | 1.9 | `59e2a3` |
| states_uniform | True | None | 1.526 | 0.725 | 28.32 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 0.8 | `d4bfd1` |
| states_uniform | False | 0.02 | 2.264 | 0.486 | 30.20 | 0.907 | 0.774 | 0 | 0 | 0 | 0 | 0 | 1.0 | `a99596` |
| states_uniform | False | 0.25 | 2.296 | 0.642 | 33.48 | 0.907 | 0.775 | 0 | 0 | 9 | 0 | 0 | 1.7 | `03b68f` |
| states_uniform | False | 0.5 | 2.660 | 0.725 | 22.47 | 0.907 | 0.821 | 0 | 0 | 17 | 0 | 0 | 1.9 | `e69da9` |
| states_uniform | False | 0.75 | 3.539 | 0.615 | 31.39 | 0.907 | 0.783 | 0 | 0 | 21 | 0 | 0 | 1.1 | `bbd227` |
| states_uniform | False | 1.0 | 5.774 | 0.376 | 44.38 | 0.907 | 0.485 | 0 | 0 | 77 | 0 | 0 | 1.2 | `6af1c4` |
| states_uniform | False | None | 2.238 | 0.523 | 34.23 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `db2447` |
| states_uniform_sq | True | 0.02 | 0.884 | 0.523 | 25.77 | 0.785 | 0.723 | 0 | 0 | 6 | 0 | 0 | 18.7 | `5769b8` |
| states_uniform_sq | True | 0.25 | 0.636 | 0.560 | 15.92 | 0.785 | 0.653 | 0 | 0 | 15 | 0 | 0 | 1.5 | `bd4501` |
| states_uniform_sq | True | 0.5 | 0.927 | 0.569 | 16.17 | 0.785 | 0.650 | 0 | 0 | 16 | 0 | 0 | 0.9 | `cc35af` |
| states_uniform_sq | True | 0.75 | 0.811 | 0.560 | 19.32 | 0.785 | 0.675 | 0 | 0 | 32 | 0 | 0 | 1.4 | `98bec9` |
| states_uniform_sq | True | 1.0 | 1.861 | 0.505 | 24.39 | 0.785 | 0.739 | 0 | 0 | 51 | 0 | 0 | 1.5 | `0bf511` |
| states_uniform_sq | True | None | 0.745 | 0.459 | 24.82 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 1.0 | `02f6d0` |
| states_uniform_sq | False | 0.02 | 1.063 | 0.495 | 26.47 | 0.785 | 0.780 | 0 | 0 | 3 | 0 | 0 | 0.9 | `95ffe5` |
| states_uniform_sq | False | 0.25 | 1.489 | 0.431 | 36.42 | 0.785 | 0.816 | 0 | 0 | 5 | 0 | 0 | 1.0 | `66bd22` |
| states_uniform_sq | False | 0.5 | 2.014 | 0.514 | 25.16 | 0.785 | 0.798 | 0 | 0 | 15 | 0 | 0 | 1.0 | `01e1e5` |
| states_uniform_sq | False | 0.75 | 1.930 | 0.541 | 25.92 | 0.785 | 0.829 | 0 | 0 | 26 | 0 | 0 | 5.3 | `b8465f` |
| states_uniform_sq | False | 1.0 | 2.708 | 0.468 | 29.00 | 0.785 | 0.774 | 0 | 0 | 42 | 0 | 0 | 1.3 | `804977` |
| states_uniform_sq | False | None | 1.583 | 0.468 | 30.20 | 0.785 | 0.801 | 0 | 0 | 1 | 0 | 0 | 1.2 | `0fae83` |
| states | True | 0.02 | 2.743 | 0.725 | 18.19 | 0.653 | 0.684 | 0 | 0 | 15 | 0 | 0 | 1.2 | `c523b9` |
| states | True | 0.25 | 2.443 | 0.798 | 18.10 | 0.666 | 0.704 | 0 | 0 | 23 | 0 | 0 | 2.2 | `1a3993` |
| states | True | 0.5 | 2.815 | 0.798 | 13.29 | 0.680 | 0.667 | 0 | 0 | 47 | 0 | 0 | 2.5 | `d1e93e` |
| states | True | 0.75 | 2.894 | 0.826 | 16.85 | 0.653 | 0.660 | 1 | 0 | 62 | 0 | 0 | 3.2 | `443331` |
| states | True | 1.0 | 3.700 | 0.523 | 11.58 | 0.680 | 0.369 | 0 | 0 | 243 | 4 | 0 | 7.4 | `320c6b` |
| states | True | None | 2.099 | 0.798 | 17.11 | 0.653 | 0.687 | 0 | 0 | 19 | 0 | 0 | 1.3 | `febe8e` |
| states | False | 0.02 | 3.568 | 0.706 | 19.72 | 0.653 | 0.812 | 0 | 0 | 4 | 0 | 0 | 1.6 | `e8fcfd` |
| states | False | 0.25 | 4.556 | 0.780 | 20.57 | 0.653 | 0.826 | 0 | 0 | 9 | 0 | 0 | 1.9 | `194282` |
| states | False | 0.5 | 4.902 | 0.725 | 18.73 | 0.680 | 0.884 | 0 | 0 | 28 | 0 | 0 | 1.5 | `f50acc` |
| states | False | 0.75 | 5.552 | 0.688 | 18.85 | 0.653 | 0.877 | 0 | 0 | 41 | 0 | 0 | 1.7 | `2c0571` |
| states | False | 1.0 | 6.394 | 0.651 | 25.18 | 0.653 | 0.741 | 0 | 0 | 101 | 2 | 0 | 3.6 | `858bde` |
| states | False | None | 3.929 | 0.697 | 25.37 | 0.653 | 0.812 | 0 | 0 | 3 | 0 | 0 | 6.7 | `02c46d` |
| districts | True | 0.02 | 4.691 | 0.505 | 31.33 | 0.907 | 0.701 | 0 | 1 | 44 | 0 | 0 | 13.6 | `4eb10a` |
| districts | True | 0.25 | 4.848 | 0.520 | 28.26 | 0.907 | 0.708 | 0 | 0 | 69 | 1 | 0 | 6.2 | `7ee753` |
| districts | True | 0.5 | 5.392 | 0.541 | 28.22 | 0.907 | 0.714 | 0 | 1 | 85 | 0 | 0 | 6.0 | `c768f4` |
| districts | True | 0.75 | 5.747 | 0.550 | 27.92 | 0.907 | 0.693 | 0 | 2 | 123 | 1 | 0 | 6.4 | `8a405d` |
| districts | True | 1.0 | 6.893 | 0.452 | 30.71 | 0.907 | 0.598 | 0 | 3 | 282 | 0 | 0 | 10.1 | `de71d3` |
| districts | True | None | 4.519 | 0.527 | 25.92 | 0.907 | 0.687 | 0 | 0 | 54 | 0 | 0 | 6.0 | `df64c3` |
| districts | False | 0.02 | 6.925 | 0.457 | 36.45 | 0.907 | 0.819 | 0 | 0 | 6 | 0 | 0 | 18.0 | `c77b9a` |
| districts | False | 0.25 | 7.620 | 0.478 | 36.72 | 0.907 | 0.888 | 0 | 1 | 25 | 0 | 0 | 10.7 | `103e57` |
| districts | False | 0.5 | 8.765 | 0.445 | 36.90 | 0.907 | 0.926 | 0 | 2 | 54 | 1 | 0 | 9.9 | `c5c7ad` |
| districts | False | 0.75 | 9.271 | 0.457 | 36.25 | 0.907 | 0.922 | 0 | 2 | 80 | 0 | 0 | 64.3 | `68de91` |
| districts | False | 1.0 | 10.997 | 0.470 | 34.92 | 0.907 | 0.829 | 0 | 3 | 155 | 0 | 0 | 60.5 | `30fa02` |
| districts | False | None | 7.286 | 0.485 | 33.92 | 0.907 | 0.857 | 0 | 0 | 14 | 0 | 0 | 3.5 | `485616` |
| world | True | 0.02 | 4.751 | 0.485 | 33.53 | 0.907 | 0.403 | 1 | 0 | 54 | 5 | 12 | 2.5 | `625cdb` |
| world | True | 0.25 | 3.210 | 0.631 | 24.47 | 0.907 | 0.364 | 3 | 0 | 157 | 2 | 10 | 1.6 | `6f6f67` |
| world | True | 0.5 | 2.934 | 0.622 | 21.14 | 0.907 | 0.297 | 2 | 0 | 257 | 0 | 9 | 2.0 | `f224a9` |
| world | True | 0.75 | 3.171 | 0.564 | 21.98 | 0.907 | 0.268 | 2 | 0 | 354 | 1 | 20 | 3.3 | `71ff4a` |
| world | True | 1.0 | 5.180 | 0.443 | 21.12 | 0.907 | 0.209 | 2 | 0 | 1138 | 0 | 21 | 7.2 | `f9687a` |
| world | True | None | 3.851 | 0.544 | 27.69 | 0.907 | 0.420 | 0 | 0 | 96 | 5 | 11 | 1.9 | `0360cc` |
| world | False | 0.02 | 6.657 | 0.358 | 40.19 | 0.907 | 0.497 | 2 | 0 | 27 | 2 | 17 | 4.5 | `f0106e` |
| world | False | 0.25 | 5.845 | 0.419 | 32.47 | 0.907 | 0.654 | 2 | 0 | 112 | 0 | 27 | 4.8 | `db3974` |
| world | False | 0.5 | 7.907 | 0.431 | 31.61 | 0.907 | 0.656 | 1 | 0 | 180 | 0 | 25 | 1.3 | `bccd5d` |
| world | False | 0.75 | 8.334 | 0.452 | 31.67 | 0.907 | 0.523 | 3 | 0 | 282 | 0 | 33 | 6.2 | `161fd4` |
| world | False | 1.0 | 7.868 | 0.526 | 26.59 | 0.907 | 0.341 | 4 | 0 | 453 | 0 | 33 | 129.6 | `bfc253` |
| world | False | None | 6.582 | 0.395 | 37.27 | 0.907 | 0.542 | 2 | 0 | 34 | 1 | 18 | 3.6 | `2944bb` |


## spacing

| case | morph | value | disp | adj | dir | pp | iou | noncontig | split | unassigned_core | enclosed | short | wall_s | fp |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| states_uniform | True | 0.05 | 1.526 | 0.725 | 28.32 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 1.3 | `d4bfd1` |
| states_uniform | True | 0.2 | 1.526 | 0.725 | 28.32 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 1.3 | `d4bfd1` |
| states_uniform | True | 0.5 | 1.526 | 0.725 | 28.32 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 1.3 | `d4bfd1` |
| states_uniform | True | None | 1.526 | 0.725 | 28.32 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 0.8 | `d4bfd1` |
| states_uniform | False | 0.05 | 2.238 | 0.523 | 34.23 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `db2447` |
| states_uniform | False | 0.2 | 2.238 | 0.523 | 34.23 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `db2447` |
| states_uniform | False | 0.5 | 2.238 | 0.523 | 34.23 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `db2447` |
| states_uniform | False | None | 2.238 | 0.523 | 34.23 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `db2447` |
| states_uniform_sq | True | 0.05 | 0.745 | 0.459 | 24.82 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 0.8 | `02f6d0` |
| states_uniform_sq | True | 0.2 | 0.745 | 0.459 | 24.82 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 0.9 | `02f6d0` |
| states_uniform_sq | True | 0.5 | 0.745 | 0.459 | 24.82 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 0.8 | `02f6d0` |
| states_uniform_sq | True | None | 0.745 | 0.459 | 24.82 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 1.0 | `02f6d0` |
| states_uniform_sq | False | 0.05 | 1.583 | 0.468 | 30.20 | 0.785 | 0.801 | 0 | 0 | 1 | 0 | 0 | 0.9 | `0fae83` |
| states_uniform_sq | False | 0.2 | 1.583 | 0.468 | 30.20 | 0.785 | 0.801 | 0 | 0 | 1 | 0 | 0 | 0.9 | `0fae83` |
| states_uniform_sq | False | 0.5 | 1.583 | 0.468 | 30.20 | 0.785 | 0.801 | 0 | 0 | 1 | 0 | 0 | 1.0 | `0fae83` |
| states_uniform_sq | False | None | 1.583 | 0.468 | 30.20 | 0.785 | 0.801 | 0 | 0 | 1 | 0 | 0 | 1.2 | `0fae83` |
| states | True | 0.05 | 2.099 | 0.798 | 17.11 | 0.653 | 0.687 | 0 | 0 | 19 | 0 | 0 | 2.2 | `febe8e` |
| states | True | 0.2 | 2.099 | 0.798 | 17.11 | 0.653 | 0.687 | 0 | 0 | 19 | 0 | 0 | 1.9 | `febe8e` |
| states | True | 0.5 | 2.099 | 0.798 | 17.11 | 0.653 | 0.687 | 0 | 0 | 19 | 0 | 0 | 1.9 | `febe8e` |
| states | True | None | 2.099 | 0.798 | 17.11 | 0.653 | 0.687 | 0 | 0 | 19 | 0 | 0 | 1.3 | `febe8e` |
| states | False | 0.05 | 3.929 | 0.697 | 25.37 | 0.653 | 0.812 | 0 | 0 | 3 | 0 | 0 | 6.8 | `02c46d` |
| states | False | 0.2 | 3.929 | 0.697 | 25.37 | 0.653 | 0.812 | 0 | 0 | 3 | 0 | 0 | 6.8 | `02c46d` |
| states | False | 0.5 | 3.929 | 0.697 | 25.37 | 0.653 | 0.812 | 0 | 0 | 3 | 0 | 0 | 7.0 | `02c46d` |
| states | False | None | 3.929 | 0.697 | 25.37 | 0.653 | 0.812 | 0 | 0 | 3 | 0 | 0 | 6.7 | `02c46d` |
| districts | True | 0.05 | 4.519 | 0.527 | 25.92 | 0.907 | 0.687 | 0 | 0 | 54 | 0 | 0 | 4.3 | `df64c3` |
| districts | True | 0.2 | 4.519 | 0.527 | 25.92 | 0.907 | 0.687 | 0 | 0 | 54 | 0 | 0 | 4.2 | `df64c3` |
| districts | True | 0.5 | 4.519 | 0.527 | 25.92 | 0.907 | 0.687 | 0 | 0 | 54 | 0 | 0 | 6.0 | `df64c3` |
| districts | True | None | 4.519 | 0.527 | 25.92 | 0.907 | 0.687 | 0 | 0 | 54 | 0 | 0 | 6.0 | `df64c3` |
| districts | False | 0.05 | 7.286 | 0.485 | 33.92 | 0.907 | 0.857 | 0 | 0 | 14 | 0 | 0 | 4.8 | `485616` |
| districts | False | 0.2 | 7.286 | 0.485 | 33.92 | 0.907 | 0.857 | 0 | 0 | 14 | 0 | 0 | 5.4 | `485616` |
| districts | False | 0.5 | 7.286 | 0.485 | 33.92 | 0.907 | 0.857 | 0 | 0 | 14 | 0 | 0 | 5.0 | `485616` |
| districts | False | None | 7.286 | 0.485 | 33.92 | 0.907 | 0.857 | 0 | 0 | 14 | 0 | 0 | 3.5 | `485616` |
| world | True | 0.05 | 3.851 | 0.544 | 27.69 | 0.907 | 0.420 | 0 | 0 | 96 | 5 | 11 | 1.8 | `0360cc` |
| world | True | 0.2 | 3.851 | 0.544 | 27.69 | 0.907 | 0.420 | 0 | 0 | 96 | 5 | 11 | 1.9 | `0360cc` |
| world | True | 0.5 | 3.851 | 0.544 | 27.69 | 0.907 | 0.420 | 0 | 0 | 96 | 5 | 11 | 1.9 | `0360cc` |
| world | True | None | 3.851 | 0.544 | 27.69 | 0.907 | 0.420 | 0 | 0 | 96 | 5 | 11 | 1.9 | `0360cc` |
| world | False | 0.05 | 6.582 | 0.395 | 37.27 | 0.907 | 0.542 | 2 | 0 | 34 | 1 | 18 | 3.7 | `2944bb` |
| world | False | 0.2 | 6.582 | 0.395 | 37.27 | 0.907 | 0.542 | 2 | 0 | 34 | 1 | 18 | 3.9 | `2944bb` |
| world | False | 0.5 | 6.582 | 0.395 | 37.27 | 0.907 | 0.542 | 2 | 0 | 34 | 1 | 18 | 3.7 | `2944bb` |
| world | False | None | 6.582 | 0.395 | 37.27 | 0.907 | 0.542 | 2 | 0 | 34 | 1 | 18 | 3.6 | `2944bb` |


## tile_size

| case | morph | value | disp | adj | dir | pp | iou | noncontig | split | unassigned_core | enclosed | short | wall_s | fp |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| states_uniform | True | 0.8 | 1.495 | 0.761 | 20.84 | 0.907 | 0.650 | 0 | 0 | 26 | 0 | 0 | 1.4 | `38ccd4` |
| states_uniform | True | 0.9 | 1.492 | 0.761 | 19.25 | 0.907 | 0.666 | 0 | 0 | 12 | 0 | 0 | 1.3 | `db1591` |
| states_uniform | True | 1.0 | 1.526 | 0.725 | 28.32 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 1.3 | `d4bfd1` |
| states_uniform | True | 1.1 | 1.766 | 0.633 | 30.73 | 0.907 | 0.692 | 0 | 0 | 4 | 0 | 0 | 1.3 | `991105` |
| states_uniform | True | 1.25 | 1.401 | 0.725 | 27.62 | 0.907 | 0.713 | 0 | 0 | 4 | 0 | 0 | 1.2 | `da3b03` |
| states_uniform | True | None | 1.526 | 0.725 | 28.32 | 0.907 | 0.713 | 0 | 0 | 5 | 0 | 0 | 0.8 | `d4bfd1` |
| states_uniform | False | 0.8 | 3.235 | 0.716 | 26.83 | 0.907 | 0.826 | 0 | 0 | 19 | 0 | 0 | 1.1 | `ccfa8b` |
| states_uniform | False | 0.9 | 2.317 | 0.661 | 27.62 | 0.907 | 0.793 | 0 | 0 | 10 | 0 | 0 | 1.0 | `354b97` |
| states_uniform | False | 1.0 | 2.238 | 0.523 | 34.23 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `db2447` |
| states_uniform | False | 1.1 | 1.871 | 0.670 | 25.07 | 0.907 | 0.704 | 0 | 0 | 0 | 0 | 0 | 0.9 | `885b43` |
| states_uniform | False | 1.25 | 2.249 | 0.679 | 28.32 | 0.907 | 0.675 | 0 | 0 | 0 | 0 | 0 | 0.7 | `77c5f7` |
| states_uniform | False | None | 2.238 | 0.523 | 34.23 | 0.907 | 0.819 | 0 | 0 | 0 | 0 | 0 | 1.0 | `db2447` |
| states_uniform_sq | True | 0.8 | 0.968 | 0.550 | 19.41 | 0.785 | 0.675 | 0 | 0 | 32 | 0 | 0 | 0.9 | `b889a0` |
| states_uniform_sq | True | 0.9 | 0.817 | 0.560 | 18.26 | 0.785 | 0.718 | 0 | 0 | 17 | 0 | 0 | 1.3 | `e26812` |
| states_uniform_sq | True | 1.0 | 0.745 | 0.459 | 24.82 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 1.2 | `02f6d0` |
| states_uniform_sq | True | 1.1 | 0.734 | 0.578 | 26.74 | 0.785 | 0.690 | 0 | 0 | 7 | 0 | 0 | 1.3 | `3c4587` |
| states_uniform_sq | True | 1.25 | 1.096 | 0.532 | 20.61 | 0.785 | 0.730 | 0 | 0 | 3 | 0 | 0 | 1.3 | `40395d` |
| states_uniform_sq | True | None | 0.745 | 0.459 | 24.82 | 0.785 | 0.666 | 0 | 0 | 10 | 0 | 0 | 1.0 | `02f6d0` |
| states_uniform_sq | False | 0.8 | 1.658 | 0.514 | 24.80 | 0.785 | 0.858 | 0 | 0 | 25 | 0 | 0 | 0.8 | `501d86` |
| states_uniform_sq | False | 0.9 | 1.436 | 0.495 | 33.17 | 0.785 | 0.808 | 0 | 0 | 11 | 0 | 0 | 0.8 | `c57256` |
| states_uniform_sq | False | 1.0 | 1.583 | 0.468 | 30.20 | 0.785 | 0.801 | 0 | 0 | 1 | 0 | 0 | 0.7 | `0fae83` |
| states_uniform_sq | False | 1.1 | 1.146 | 0.505 | 20.85 | 0.785 | 0.752 | 0 | 0 | 0 | 0 | 0 | 0.6 | `2ed916` |
| states_uniform_sq | False | 1.25 | 1.574 | 0.459 | 25.80 | 0.785 | 0.717 | 0 | 0 | 0 | 0 | 0 | 0.7 | `5af3e5` |
| states_uniform_sq | False | None | 1.583 | 0.468 | 30.20 | 0.785 | 0.801 | 0 | 0 | 1 | 0 | 0 | 1.2 | `0fae83` |
| states | True | 0.8 | 3.382 | 0.752 | 14.42 | 0.680 | 0.635 | 0 | 0 | 90 | 0 | 0 | 2.1 | `f9b108` |
| states | True | 0.9 | 2.806 | 0.817 | 12.43 | 0.653 | 0.663 | 0 | 0 | 48 | 1 | 0 | 2.0 | `6550e3` |
| states | True | 1.0 | 2.099 | 0.798 | 17.11 | 0.653 | 0.687 | 0 | 0 | 19 | 0 | 0 | 1.8 | `febe8e` |
| states | True | 1.1 | 2.589 | 0.771 | 14.60 | 0.653 | 0.740 | 0 | 0 | 7 | 0 | 0 | 1.7 | `046785` |
| states | True | 1.25 | 2.585 | 0.798 | 14.93 | 0.653 | 0.730 | 0 | 0 | 1 | 0 | 1 | 1.6 | `f37b6d` |
| states | True | None | 2.099 | 0.798 | 17.11 | 0.653 | 0.687 | 0 | 0 | 19 | 0 | 0 | 1.3 | `febe8e` |
| states | False | 0.8 | 4.577 | 0.587 | 17.96 | 0.680 | 0.728 | 0 | 0 | 83 | 1 | 0 | 5.0 | `c0c737` |
| states | False | 0.9 | 5.240 | 0.734 | 20.06 | 0.653 | 0.883 | 0 | 0 | 36 | 1 | 0 | 1.3 | `6b6c26` |
| states | False | 1.0 | 3.929 | 0.697 | 25.37 | 0.653 | 0.812 | 0 | 0 | 3 | 0 | 0 | 5.4 | `02c46d` |
| states | False | 1.1 | 4.020 | 0.734 | 16.78 | 0.653 | 0.749 | 0 | 0 | 0 | 0 | 0 | 1.1 | `1c9a50` |
| states | False | 1.25 | 3.480 | 0.817 | 19.72 | 0.653 | 0.800 | 0 | 0 | 0 | 0 | 1 | 0.9 | `f2f0ac` |
| states | False | None | 3.929 | 0.697 | 25.37 | 0.653 | 0.812 | 0 | 0 | 3 | 0 | 0 | 6.7 | `02c46d` |
| districts | True | 0.8 | 5.373 | 0.538 | 26.68 | 0.907 | 0.538 | 0 | 0 | 258 | 2 | 0 | 6.3 | `b780d1` |
| districts | True | 0.9 | 5.799 | 0.551 | 29.13 | 0.907 | 0.692 | 0 | 1 | 122 | 0 | 0 | 7.8 | `33f3b1` |
| districts | True | 1.0 | 4.519 | 0.527 | 25.92 | 0.907 | 0.687 | 0 | 0 | 54 | 0 | 0 | 3.8 | `df64c3` |
| districts | True | 1.1 | 4.699 | 0.539 | 29.98 | 0.907 | 0.727 | 0 | 0 | 13 | 0 | 0 | 4.1 | `7b6d14` |
| districts | True | 1.25 | 3.596 | 0.667 | 32.43 | 0.907 | 0.733 | 0 | 0 | 4 | 0 | 57 | 3.6 | `d84727` |
| districts | True | None | 4.519 | 0.527 | 25.92 | 0.907 | 0.687 | 0 | 0 | 54 | 0 | 0 | 6.0 | `df64c3` |
| districts | False | 0.8 | 7.307 | 0.452 | 31.90 | 0.907 | 0.609 | 0 | 2 | 244 | 0 | 0 | 18.5 | `81b30e` |
| districts | False | 0.9 | 9.396 | 0.462 | 35.43 | 0.907 | 0.904 | 0 | 2 | 102 | 0 | 0 | 10.0 | `69ba10` |
| districts | False | 1.0 | 7.286 | 0.485 | 33.92 | 0.907 | 0.857 | 0 | 0 | 14 | 0 | 0 | 5.5 | `485616` |
| districts | False | 1.1 | 6.408 | 0.498 | 35.77 | 0.907 | 0.807 | 0 | 1 | 0 | 0 | 0 | 4.9 | `56a079` |
| districts | False | 1.25 | 4.217 | 0.560 | 34.08 | 0.907 | 0.825 | 0 | 0 | 0 | 0 | 62 | 4.1 | `aa296c` |
| districts | False | None | 7.286 | 0.485 | 33.92 | 0.907 | 0.857 | 0 | 0 | 14 | 0 | 0 | 3.5 | `485616` |
| world | True | 0.8 | 2.970 | 0.626 | 22.44 | 0.907 | 0.294 | 3 | 0 | 263 | 0 | 4 | 1.9 | `833e1a` |
| world | True | 0.9 | 3.456 | 0.617 | 24.08 | 0.907 | 0.364 | 5 | 0 | 160 | 2 | 7 | 1.7 | `def915` |
| world | True | 1.0 | 3.851 | 0.544 | 27.69 | 0.907 | 0.420 | 0 | 0 | 96 | 5 | 11 | 1.6 | `0360cc` |
| world | True | 1.1 | 4.103 | 0.534 | 33.41 | 0.907 | 0.388 | 0 | 0 | 52 | 0 | 16 | 1.2 | `66fddc` |
| world | True | 1.25 | 5.203 | 0.483 | 34.99 | 0.907 | 0.359 | 0 | 0 | 12 | 0 | 23 | 1.1 | `3f5916` |
| world | True | None | 3.851 | 0.544 | 27.69 | 0.907 | 0.420 | 0 | 0 | 96 | 5 | 11 | 1.9 | `0360cc` |
| world | False | 0.8 | 5.931 | 0.470 | 30.94 | 0.907 | 0.588 | 2 | 0 | 218 | 1 | 14 | 1.8 | `7dd68b` |
| world | False | 0.9 | 7.147 | 0.379 | 34.28 | 0.907 | 0.655 | 2 | 0 | 105 | 2 | 16 | 3.0 | `776230` |
| world | False | 1.0 | 6.582 | 0.395 | 37.27 | 0.907 | 0.542 | 2 | 0 | 34 | 1 | 18 | 4.1 | `2944bb` |
| world | False | 1.1 | 6.826 | 0.495 | 29.58 | 0.907 | 0.459 | 1 | 0 | 10 | 1 | 24 | 4.8 | `89e2bf` |
| world | False | 1.25 | 8.591 | 0.528 | 33.16 | 0.907 | 0.355 | 0 | 0 | 0 | 0 | 29 | 1.8 | `d46a6a` |
| world | False | None | 6.582 | 0.395 | 37.27 | 0.907 | 0.542 | 2 | 0 | 34 | 1 | 18 | 3.6 | `2944bb` |
