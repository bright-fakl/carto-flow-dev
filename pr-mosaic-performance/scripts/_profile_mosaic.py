"""Ad-hoc profiling script for mosaic layout performance work (perf/mosaic-calibration).

Not part of the test suite. Writes cProfile dumps + a text summary to
visual_checks/pr-mosaic-performance/profiles/{OUT_SUBDIR}/.
"""

from __future__ import annotations

import cProfile
import os
import pstats
import sys
import time
from pathlib import Path

sys.path.insert(0, "src")

SUBDIR = os.environ.get("PROFILE_SUBDIR", "after")
OUT = Path(f"/home/fakl/carto-flow/visual_checks/pr-mosaic-performance/profiles/{SUBDIR}")
OUT.mkdir(parents=True, exist_ok=True)


def profile_one(name: str, fn):
    pr = cProfile.Profile()
    t0 = time.perf_counter()
    pr.enable()
    result = fn()
    pr.disable()
    elapsed = time.perf_counter() - t0
    pr.dump_stats(str(OUT / f"{name}.prof"))
    stats = pstats.Stats(pr)
    stats.sort_stats("cumulative")
    with open(OUT / f"{name}.txt", "w") as f:
        f.write(f"wall_time={elapsed:.3f}s\n\n")
        import io

        buf = io.StringIO()
        stats.stream = buf
        stats.print_stats(40)
        f.write(buf.getvalue())
    print(f"{name}: {elapsed:.3f}s -> {OUT / (name + '.txt')}")
    return result, elapsed


def load_states():
    from carto_flow.data import load_us_states

    return load_us_states()


def load_districts():
    from carto_flow.data import load_us_census

    return load_us_census(level="congressional_district", population=True)


if __name__ == "__main__":
    states = load_states()
    if "Population" not in states.columns:
        try:
            from carto_flow.data import load_us_census

            states = load_us_census(level="state", population=True)
        except Exception as e:
            print("could not load state population:", e)

    districts = load_districts()

    import carto_flow.symbol_cartogram.layouts.mosaic as mosaic_mod
    from carto_flow.symbol_cartogram.api import create_layout

    timings = {}

    for tag, morph in [("states_morph", True), ("states_nomorph", False)]:

        def _run(morph=morph):
            return create_layout(
                states,
                "Population",
                layout=mosaic_mod.MosaicLayout(morph=morph),
                show_progress=False,
            )

        _, t = profile_one(tag, _run)
        timings[tag] = t

    for tag, morph in [("districts_morph", True), ("districts_nomorph", False)]:

        def _run(morph=morph):
            return create_layout(
                districts,
                "Population",
                layout=mosaic_mod.MosaicLayout(morph=morph),
                show_progress=False,
            )

        _, t = profile_one(tag, _run)
        timings[tag] = t

    for tag, morph in [("districts_grouped_morph", True), ("districts_grouped_nomorph", False)]:

        def _run(morph=morph):
            return create_layout(
                districts,
                "Population",
                group_by="State Name",
                layout=mosaic_mod.MosaicLayout(morph=morph),
                show_progress=False,
            )

        _, t = profile_one(tag, _run)
        timings[tag] = t

    import json

    (OUT / "timings.json").write_text(json.dumps(timings, indent=2))
    print("done", timings)
