"""Memory of a TilingResult with about 10,000 tiles, with whichever carto-flow is first on PYTHONPATH.

    python memory_check.py <label> <hexagon|square> [n_tiles]

Prints, for one tiling: the number of tiles, the bytes held by ``adjacency`` and
``vertex_adjacency`` (``nbytes`` of a dense array; data, indices and indptr of a sparse one), the peak of Python and numpy
allocations during ``generate`` (``tracemalloc``), and the growth of the peak resident set size of the process caused by
``generate`` (``ru_maxrss``). Run each label and tiling in its own process: the peak resident set size is a high-water mark.
"""

from __future__ import annotations

import resource
import sys
import tracemalloc

import numpy as np


def matrix_bytes(m) -> int:
    if isinstance(m, np.ndarray):
        return int(m.nbytes)
    return int(m.data.nbytes + m.indices.nbytes + m.indptr.nbytes)


def main(label: str, name: str, n_tiles: int) -> None:
    from carto_flow.symbol_cartogram.tiling import HexagonTiling, SquareTiling

    HexagonTiling().generate((0.0, 0.0, 10.0, 10.0), n_tiles=50)  # imports and warm-up
    tiling = HexagonTiling() if name == "hexagon" else SquareTiling()
    rss_before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    tracemalloc.start()
    result = tiling.generate((0.0, 0.0, 100.0, 100.0), n_tiles=n_tiles)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    rss_after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    edge = matrix_bytes(result.adjacency)
    vertex = matrix_bytes(result.vertex_adjacency)
    print(
        f"[{label}] {name}: {result.n_tiles} tiles, type {type(result.adjacency).__name__}, "
        f"adjacency {edge / 1e6:.2f} MB, vertex_adjacency {vertex / 1e6:.2f} MB, "
        f"tracemalloc peak of generate {peak / 1e6:.1f} MB, peak RSS growth {(rss_after - rss_before) / 1e3:.1f} MB"
    )
    del result


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 10_000)
