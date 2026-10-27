"""Where does carto-flow's IsohedralTiling.generate spend its time, and what does isotile need for the same task?

Part 1: time of the current generate (adjacency off) at several tile counts, for a straight hexagon (IH7) and a
curved preset (scalloped_hexagon), to fit the growth exponent. Part 2: cProfile of generate at one size, top functions
by own time. Part 3: the isotile equivalent (fill_region, polygons, lattice adjacency) at the same sizes.

Run: python profile_generate.py > profile_generate.txt   (scratch venv with carto-flow and isotile installed)
"""

from __future__ import annotations

import cProfile
import io
import math
import pstats
import sys
import time
import warnings

import numpy as np
from carto_flow.symbol_cartogram.tiling import IsohedralTiling as Old
from isotile import IsohedralTiling as New

BOUNDS = (-1.0, -1.0, 1.0, 1.0)


def old_time(make, n, adjacency=False):
    t = make()
    t0 = time.perf_counter()
    r = t.generate(bounds=BOUNDS, n_tiles=n, margin=0.0, compute_adjacency=adjacency)
    return time.perf_counter() - t0, r.n_tiles


def new_time(make, n, adjacency=False, repeats=3):
    best = math.inf
    for _ in range(repeats):
        t0 = time.perf_counter()
        ts = make().fill_region(BOUNDS, n_tiles=n)
        polys = ts.polygons()
        if adjacency:
            ts.adjacency("edge")
            ts.adjacency("vertex-only")
        best = min(best, time.perf_counter() - t0)
    return best, len(polys)


def main() -> None:
    cases = {
        "IH7 (hexagon, 6 vertices)": (lambda: Old(7), lambda: New(7)),
        "scalloped_hexagon (curved, 594 vertices per tile)": (lambda: Old.from_preset("scalloped_hexagon"), lambda: New.from_preset("scalloped_hexagon")),
    }
    sizes = [250, 500, 1000, 2000, 4000]
    print("Part 1: wall time in seconds, current generate (compute_adjacency=False, margin 0), one run each\n")
    for name, (mo, mn) in cases.items():
        print(name)
        times = []
        print(f"  {'n_tiles':>8} {'returned':>9} {'old generate':>13} {'old per tile':>13} {'isotile (best of 3)':>20}")
        for n in sizes:
            dt, k = old_time(mo, n)
            nt, nk = new_time(mn, n)
            times.append((k, dt))
            print(f"  {n:>8} {k:>9} {dt:>12.2f}s {dt / k * 1e3:>11.2f}ms {nt:>19.4f}s")
            sys.stdout.flush()
        ks = np.log([k for k, _ in times[1:]])
        ds = np.log([d for _, d in times[1:]])
        slope = np.polyfit(ks, ds, 1)[0]
        print(f"  growth exponent (log-log fit over the last four sizes): {slope:.2f}")
        k10 = 10000
        pred = math.exp(np.polyval(np.polyfit(ks, ds, 1), math.log(k10)))
        print(f"  extrapolation to {k10} tiles: {pred:.0f} s")
        print()

    print("Part 2: cProfile of the current generate, IH7, n_tiles 2000, top functions by own time\n")
    t = Old(7)
    pr = cProfile.Profile()
    pr.enable()
    r = t.generate(bounds=BOUNDS, n_tiles=2000, margin=0.0, compute_adjacency=False)
    pr.disable()
    out = io.StringIO()
    st = pstats.Stats(pr, stream=out).sort_stats("tottime")
    st.print_stats(12)
    print(f"returned {r.n_tiles} tiles")
    print(out.getvalue())
    out = io.StringIO()
    pstats.Stats(pr, stream=out).sort_stats("cumulative").print_stats(14)
    print("by cumulative time:")
    print(out.getvalue())

    print("Part 3: current generate with adjacency, and isotile with adjacency\n")
    print(f"  {'n_tiles':>8} {'old generate+adjacency':>24} {'isotile fill_region+polygons+adjacency':>40}")
    for n in (500, 1000, 2000):
        dt, k = old_time(lambda: Old(7), n, adjacency=True)
        nt, nk = new_time(lambda: New(7), n, adjacency=True)
        print(f"  {n:>8} {dt:>23.2f}s {nt:>39.4f}s   (tiles {k} / {nk})")


if __name__ == "__main__":
    warnings.simplefilter("ignore")
    main()
