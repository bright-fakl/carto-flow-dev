"""Cost of the isotile equivalent at large sizes, and of dense against sparse adjacency.

Measures, for IH7 and the curved preset scalloped_hexagon: isotile fill_region plus polygons plus lattice adjacency at
2,000 to 40,000 tiles (best of 3), the size of the sparse adjacency matrices against the dense boolean matrices that
carto-flow's TilingResult holds today, and the time of ``toarray``.

Run: python perf_isotile.py > perf_isotile.txt
"""

from __future__ import annotations

import time
import warnings

import isotile

BOUNDS = (-1.0, -1.0, 1.0, 1.0)


def best(fn, repeats=3):
    out, t = None, float("inf")
    for _ in range(repeats):
        t0 = time.perf_counter()
        out = fn()
        t = min(t, time.perf_counter() - t0)
    return out, t


def main() -> None:
    for name, make in (
        ("IH7", lambda: isotile.IsohedralTiling(7)),
        ("scalloped_hexagon", lambda: isotile.IsohedralTiling.from_preset("scalloped_hexagon")),
    ):
        print(name)
        print(f"  {'n_tiles':>8} {'tiles':>7} {'fill_region':>12} {'polygons':>10} {'adjacency x2':>13} {'sparse MB':>10} {'dense MB':>9} {'toarray x2':>11}")
        for n in (2000, 10000, 40000):
            ts, t_fill = best(lambda n=n: make().fill_region(BOUNDS, n_tiles=n))
            _, t_poly = best(lambda ts=ts: ts.polygons())
            (e, v), t_adj = best(lambda ts=ts: (ts.adjacency("edge"), ts.adjacency("vertex-only")))
            sparse_mb = sum(m.data.nbytes + m.indices.nbytes + m.indptr.nbytes for m in (e, v)) / 1e6
            dense_mb = 2 * len(ts) ** 2 / 1e6
            if len(ts) <= 12000:
                _, t_dense = best(lambda e=e, v=v: (e.toarray(), v.toarray()), repeats=2)
                t_dense = f"{t_dense:>10.3f}s"
            else:
                t_dense = f"{'-':>11}"
            print(f"  {n:>8} {len(ts):>7} {t_fill:>11.4f}s {t_poly:>9.3f}s {t_adj:>12.4f}s {sparse_mb:>10.2f} {dense_mb:>9.0f} {t_dense}")


if __name__ == "__main__":
    warnings.simplefilter("ignore")
    main()
