# Per-value tables

All world tile budgets are given as `nominal / actual`: the fixture builds counts with
`max(1, round(pop / pop.sum() * budget))`, and the `max(1, ...)` floor raises the requested
total well above the nominal budget because 140 of 176 countries hold less than half a
tile's worth of population. Nominal 300 requests 384; nominal 384 requests 460; nominal 800
requests 848; nominal 1500 requests 1527.

## Where tiles are lost, by input (clean main a095187)

| input | budget nominal / actual | morph | short | zero | cross-component overwrites | empty-pool components | non-contiguous | unassigned core | seconds |
|---|---|---|---|---|---|---|---|---|---|
| africa | 150 / 159 | True | 0 | 0 | 0 | 0 | 0 | 8 | 1.5 |
| africa | 150 / 159 | False | 0 | 0 | 0 | 0 | 0 | 5 | 0.2 |
| africa | 300 / 306 | True | 0 | 0 | 0 | 0 | 0 | 8 | 0.5 |
| africa | 300 / 306 | False | 0 | 0 | 0 | 0 | 0 | 7 | 0.6 |
| world | 384 / 460 | True | 8 | 6 | 8 | 2 | 1 | 25 | 3.7 |
| world | 384 / 460 | False | 18 | 14 | 7 | 13 | 3 | 55 | 14.7 |
| world_mainland | 384 / 446 | True | 0 | 0 | 0 | 0 | 1 | 13 | 3.3 |
| world_mainland | 384 / 446 | False | 0 | 0 | 0 | 0 | 5 | 23 | 5.8 |
| world | 800 / 848 | True | 6 | 3 | 3 | 3 | 6 | 32 | 55.3 |
| world | 1500 / 1527 | True | 6 | 2 | 6 | 2 | 7 | 49 | 72.4 |
| world_mainland | 800 / 831 | True | 0 | 0 | 0 | 0 | 4 | 30 | 5.8 |
| world_mainland | 1500 / 1511 | True | 0 | 0 | 0 | 0 | 8 | 33 | 25.3 |

## `swap_repair_passes` (world 800 nominal / 848 actual; districts)

Fingerprint is the full per-region set of assigned tile centroids plus the tile size;
two values sharing a fingerprint produced a byte-identical placement.


### districts, morph=False

| value | seconds | non-contiguous regions | split groups | regions short | unassigned core | fingerprint |
|---|---|---|---|---|---|---|
| 0 | 4.0 | 0 | 12 | 0 | 14 | `36213bd1a2f06d70` |
| 1 | 3.9 | 0 | 4 | 0 | 14 | `71929043be8f1e8b` |
| 2 | 3.8 | 0 | 3 | 0 | 14 | `b15185d7d0b9a96d` |
| 3 | 4.0 | 0 | 2 | 0 | 14 | `13d2dc3ba20158b6` |
| 5 | 4.2 | 0 | 2 | 0 | 14 | `5e99c1018043e1c4` |
| 10 | 4.0 | 0 | 0 | 0 | 14 | `b34667996c9cfeed` |

### districts, morph=True

| value | seconds | non-contiguous regions | split groups | regions short | unassigned core | fingerprint |
|---|---|---|---|---|---|---|
| 0 | 7.3 | 0 | 8 | 0 | 10 | `51392d27fd964089` |
| 1 | 4.5 | 0 | 1 | 0 | 10 | `c81f164260d8d0db` |
| 2 | 4.6 | 0 | 0 | 0 | 10 | `72cd3f2aa88537ba` |
| 3 | 5.0 | 0 | 0 | 0 | 10 | `72cd3f2aa88537ba` |
| 5 | 6.6 | 0 | 0 | 0 | 10 | `72cd3f2aa88537ba` |
| 10 | 4.5 | 0 | 0 | 0 | 10 | `72cd3f2aa88537ba` |

### world, morph=False

| value | seconds | non-contiguous regions | split groups | regions short | unassigned core | fingerprint |
|---|---|---|---|---|---|---|
| 0 | 19.2 | 10 | 0 | 17 | 81 | `e933550a60ebc262` |
| 1 | 26.3 | 5 | 0 | 17 | 81 | `10074b4721b03e36` |
| 2 | 28.4 | 4 | 0 | 17 | 81 | `54f434ebfcdb3b13` |
| 3 | 29.7 | 4 | 0 | 17 | 81 | `54f434ebfcdb3b13` |
| 5 | 33.0 | 4 | 0 | 17 | 81 | `54f434ebfcdb3b13` |
| 10 | 35.9 | 4 | 0 | 17 | 81 | `54f434ebfcdb3b13` |

### world, morph=True

| value | seconds | non-contiguous regions | split groups | regions short | unassigned core | fingerprint |
|---|---|---|---|---|---|---|
| 0 | 8.8 | 16 | 0 | 6 | 32 | `d075b91256ef1a48` |
| 1 | 11.9 | 8 | 0 | 6 | 32 | `ec357e77d8a44bed` |
| 2 | 15.4 | 7 | 0 | 6 | 32 | `20725dbfa586abf4` |
| 3 | 18.9 | 7 | 0 | 6 | 32 | `eb95ba40c258bc28` |
| 5 | 29.9 | 7 | 0 | 6 | 32 | `ea4f1b4d7d0178a7` |
| 10 | 38.3 | 6 | 0 | 6 | 32 | `ba7120159c505530` |

## `ring_swapback_max_hops`


### districts, morph=False

| value | seconds | non-contiguous regions | split groups | regions short | unassigned core | fingerprint |
|---|---|---|---|---|---|---|
| 0 | 3.6 | 0 | 2 | 0 | 38 | `7c8c25f1716d51a2` |
| 1 | 4.4 | 0 | 0 | 0 | 23 | `89bdc539df290821` |
| 2 | 4.2 | 0 | 0 | 0 | 22 | `a14b44e666ef2668` |
| 4 | 3.9 | 0 | 0 | 0 | 21 | `b1b62f64b2fdc91e` |
| 8 | 4.5 | 0 | 0 | 0 | 18 | `540ee4ad0196b9b5` |
| 16 | 3.7 | 0 | 0 | 0 | 14 | `b34667996c9cfeed` |
| 32 | 3.8 | 0 | 1 | 0 | 12 | `80692fad1d580342` |

### districts, morph=True

| value | seconds | non-contiguous regions | split groups | regions short | unassigned core | fingerprint |
|---|---|---|---|---|---|---|
| 0 | 4.7 | 0 | 2 | 0 | 30 | `80e5ff5cd30caeff` |
| 1 | 4.4 | 0 | 1 | 0 | 13 | `c6bbada1e7414d25` |
| 2 | 4.2 | 0 | 0 | 0 | 13 | `5cd61136df298703` |
| 4 | 4.3 | 0 | 0 | 0 | 10 | `4eb52d4896faa5ea` |
| 8 | 4.2 | 0 | 0 | 0 | 11 | `3fefc13ab8506861` |
| 16 | 4.5 | 0 | 0 | 0 | 10 | `72cd3f2aa88537ba` |
| 32 | 4.5 | 0 | 0 | 0 | 9 | `6309302b542ee727` |

### world, morph=False

| value | seconds | non-contiguous regions | split groups | regions short | unassigned core | fingerprint |
|---|---|---|---|---|---|---|
| 0 | 3.9 | 7 | 0 | 17 | 142 | `fced109fcb374474` |
| 1 | 4.1 | 6 | 0 | 17 | 107 | `f8929184920a303d` |
| 2 | 3.8 | 6 | 0 | 17 | 98 | `9477703758907e97` |
| 4 | 4.0 | 5 | 0 | 17 | 89 | `c3186565457d5025` |
| 8 | 5.7 | 4 | 0 | 17 | 86 | `dbaf6701ae5f00f4` |
| 16 | 14.2 | 4 | 0 | 17 | 81 | `54f434ebfcdb3b13` |
| 32 | 22.6 | 4 | 0 | 17 | 80 | `18559a15eac373d1` |

### world, morph=True

| value | seconds | non-contiguous regions | split groups | regions short | unassigned core | fingerprint |
|---|---|---|---|---|---|---|
| 0 | 4.3 | 9 | 0 | 6 | 135 | `c5ec65a3f034e479` |
| 1 | 5.3 | 6 | 0 | 6 | 73 | `d190bf98b4fcd73e` |
| 2 | 4.8 | 6 | 0 | 6 | 60 | `355b965ef904f6d7` |
| 4 | 6.0 | 7 | 0 | 6 | 51 | `0ce130279fbebcf0` |
| 8 | 7.2 | 6 | 0 | 6 | 37 | `8facd017be14db32` |
| 16 | 10.5 | 6 | 0 | 6 | 32 | `ba7120159c505530` |
| 32 | 14.3 | 7 | 0 | 6 | 25 | `ce20821539c36f09` |

## Contiguity repair: heap operations and the pre-check

Captured `repair_contiguity` call from world 800 nominal / 848 actual tiles, morph=True
(842 slots, 173 units, mean lattice degree 5.13).

| max_passes | library seconds | with pre-check | speedup | `slot_of` identical | heap pops | pops in calls that yielded nothing | enumeration calls | yielded nothing | provably unreachable | pre-check skips |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 5.0 | 0.06 | 81x | True | 1,482,211 | 1,468,147 | 22 | 11 | 11 | 11 |
| 2 | 10.6 | 0.10 | 110x | True | 2,959,350 | 2,936,294 | 36 | 21 | 21 | 21 |
| 3 | 11.0 | 0.08 | 143x | True | 4,436,303 | 4,404,441 | 48 | 31 | 31 | 31 |
| 5 | 19.8 | 0.11 | 176x | True | 7,384,414 | 7,340,735 | 72 | 51 | 51 | 51 |
| 10 | 30.5 | 0.23 | 132x | True | 11,807,758 | 11,745,176 | 107 | 80 | 80 | 80 |

## `min_one_tile_per_region` off vs on (on top of the disjoint-pool fix)

| input | budget nominal / actual | morph | off: short / zero | on: short / zero | off: non-contig | on: non-contig | fingerprint changed |
|---|---|---|---|---|---|---|---|
| africa | 150 | False | 0 / 0 | 0 / 0 | 0 | 0 | False |
| africa | 150 | True | 0 / 0 | 0 / 0 | 0 | 0 | False |
| districts | 0 | False | 0 / 0 | 0 / 0 | 0 | 0 | False |
| districts | 0 | True | 0 / 0 | 0 / 0 | 0 | 0 | False |
| states | 0 | False | 0 / 0 | 0 / 0 | 0 | 0 | False |
| states | 0 | True | 0 / 0 | 0 / 0 | 0 | 0 | False |
| world | 384 | False | 13 / 13 | 0 / 0 | 3 | 1 | True |
| world | 384 | True | 2 / 2 | 0 / 0 | 2 | 2 | True |
| world | 800 | False | 11 / 11 | 0 / 0 | 3 | 4 | True |
| world | 800 | True | 3 / 3 | 0 / 0 | 3 | 3 | True |
| world_mainland | 384 | False | 0 / 0 | 0 / 0 | 5 | 5 | False |
| world_mainland | 384 | True | 0 / 0 | 0 / 0 | 1 | 1 | False |
