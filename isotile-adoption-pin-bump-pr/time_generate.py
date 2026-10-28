"""Time of Tiling.generate for about 10,000 hexagons: python time_generate.py <label> (carto-flow first on PYTHONPATH). Best of 7."""
import sys
import time

from carto_flow.symbol_cartogram.tiling import HexagonTiling

for off in ((0.0, 0.0), (0.3, 0.6)):
    t = HexagonTiling().with_offset(off) if off != (0.0, 0.0) else HexagonTiling()
    times = []
    for _ in range(7):
        t0 = time.perf_counter()
        r = t.generate((0.0, 0.0, 100.0, 60.0), n_tiles=9800, margin=0.1)
        times.append(time.perf_counter() - t0)
    print(f"{sys.argv[1]}: offset {off}: {r.n_tiles} tiles, best {min(times):.3f} s, median {sorted(times)[3]:.3f} s")
