"""Time of ``generate`` of the four families, current classes against the wrapper prototype.

Run twice, with the sources of the current main on PYTHONPATH and with the copy that holds the wrapper prototype
(``wrapper_proto.py``). One tile count of 1,000 and one of 5,000, adjacency off and on.

    PYTHONPATH=<src> python perf_wrapper.py <label>
"""

from __future__ import annotations

import sys
import time
import warnings

from carto_flow.symbol_cartogram import HexagonTiling, QuadrilateralTiling, SquareTiling, TriangleTiling


def main(label: str) -> None:
    print(f"{label}: seconds per generate call (best of 3)")
    print(f"{'class':<12}{'n_tiles':>8}{'tiles':>7}{'no adjacency':>14}{'with adjacency':>16}")
    for name, tiling in (
        ("square", SquareTiling()),
        ("hexagon", HexagonTiling()),
        ("triangle", TriangleTiling.equilateral()),
        ("quadrilateral", QuadrilateralTiling.parallelogram()),
    ):
        for n in (1000, 5000):
            times = []
            for adjacency in (False, True):
                best, tiles = float("inf"), 0
                for _ in range(3):
                    t0 = time.perf_counter()
                    tiles = tiling.generate(bounds=(-1, -1, 1, 1), n_tiles=n, compute_adjacency=adjacency).n_tiles
                    best = min(best, time.perf_counter() - t0)
                times.append(best)
            print(f"{name:<12}{n:>8}{tiles:>7}{times[0]:>13.3f}s{times[1]:>15.3f}s")


if __name__ == "__main__":
    warnings.simplefilter("ignore")
    main(sys.argv[1])
