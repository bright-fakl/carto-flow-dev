"""Wall time and profile of the mosaic layout on the 432 congressional districts (one tile count per district, grouped by state).

Run with the sources of the current main and with the copy that holds the wrapper prototype on PYTHONPATH:

    PYTHONPATH=<src> python mosaic_time.py <label>

Prints the wall time, the tile count and, for the mosaic functions among the 14 largest cumulative times of cProfile,
the number of calls and the cumulative seconds (the profiler slows the run).
"""

from __future__ import annotations

import cProfile
import io
import pstats
import sys
import time
import warnings


def main(label: str) -> None:
    from carto_flow.data import load_us_census
    from carto_flow.symbol_cartogram import create_layout
    from carto_flow.symbol_cartogram.layouts.mosaic import MosaicLayout

    districts = load_us_census(population=True, level="congressional_district").reset_index(drop=True)
    profiler = cProfile.Profile()
    t0 = time.perf_counter()
    profiler.enable()
    result = create_layout(districts, group_by="State Name", layout=MosaicLayout(tiling="hexagon", morph=False), show_progress=False)
    profiler.disable()
    print(f"{label}: districts, mosaic hexagon, morph=False: {time.perf_counter() - t0:.1f} s, {result.tiling_result.n_tiles} lattice tiles")
    out = io.StringIO()
    pstats.Stats(profiler, stream=out).sort_stats("cumulative").print_stats(14)
    for line in out.getvalue().splitlines():
        if "layouts/mosaic" in line:
            fields = line.split()
            where = line.replace("\\", "/").split("layouts/")[-1].strip()
            print(f"  ncalls {fields[0]:>6}  cumulative {fields[3]:>7} s  {where}")


if __name__ == "__main__":
    warnings.simplefilter("ignore")
    main(sys.argv[1])
