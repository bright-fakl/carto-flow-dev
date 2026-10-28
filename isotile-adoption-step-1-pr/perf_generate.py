"""Time of IsohedralTiling.generate (IH7, with adjacency) and of the four families, best of 3 (2 for IH7 on old code).

    python perf_generate.py <label>
"""

import sys
import time
import warnings

warnings.simplefilter("ignore")
from carto_flow.symbol_cartogram.tiling import HexagonTiling, IsohedralTiling, QuadrilateralTiling, SquareTiling, TriangleTiling


def best(f, n=3):
    out = []
    for _ in range(n):
        t = time.perf_counter()
        r = f()
        out.append(time.perf_counter() - t)
    return min(out), r.n_tiles


for n in (2000, 4000):
    t, k = best(lambda: IsohedralTiling(7).generate((-1, -1, 1, 1), n_tiles=n, margin=0.0), 1)
    print(sys.argv[1], f"IH7 n_tiles={n}: {t:.3f} s, {k} tiles")
for name, tiling in (("square", SquareTiling()), ("hexagon", HexagonTiling()), ("triangle", TriangleTiling.equilateral()), ("quadrilateral", QuadrilateralTiling.parallelogram())):
    t0, k = best(lambda: tiling.generate((-1, -1, 1, 1), n_tiles=5000, compute_adjacency=False))
    t1, k = best(lambda: tiling.generate((-1, -1, 1, 1), n_tiles=5000))
    print(sys.argv[1], f"{name} n_tiles=5000: no adjacency {t0:.3f} s, adjacency {t1:.3f} s, {k} tiles")
