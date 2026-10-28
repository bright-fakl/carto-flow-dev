"""Cost of the isotile calls per interaction of the editor, against the current implementation where there is one.

Each timing is the mean of 5 calls, best of 2 batches, in milliseconds, per case; the table prints the median and
the largest over the cases. Cases: the 15 presets (curves) and the 81 types at their defaults (no curves) and 81 types
with a scalloped curve on every curvable shape id.

Run: python perf_events.py > perf_events.txt      (scratch venv with isotile and carto-flow 2.0.0, GUI_SRC set)
"""
from __future__ import annotations

import os
import statistics
import sys
import time
import warnings

import numpy as np

sys.path.insert(0, os.environ["GUI_SRC"])
warnings.simplefilter("ignore")
import isotile  # noqa: E402
from isotile import IsohedralTiling as IT, check_prototile, enforce_symmetry, interpolate, get_type, tiling_types  # noqa: E402
from carto_flow.symbol_cartogram.tiling import IsohedralTiling as Old  # noqa: E402
from isohedral_tiling_ui.utils.spline_cache import interpolate_spline  # noqa: E402
from isohedral_tiling_ui.utils.symmetry import enforce_curve_symmetry  # noqa: E402
from tactile import EdgeShape  # noqa: E402

PREVIEW = dict(bounds=(-1, -0.3, 1, 0.3), n_tiles=100, margin=0.25)
EXPORT = lambda n: dict(bounds=(-2, -2, 2, 2), n_tiles=n, margin=0.0)  # noqa: E731


def timeit(fn, repeat=5) -> float:
    best = []
    for _ in range(2):
        t0 = time.perf_counter()
        for _ in range(repeat):
            fn()
        best.append((time.perf_counter() - t0) / repeat * 1000)
    return min(best)


def scalloped(t) -> dict:
    return {i: isotile.edge_curve_preset("bump", s, 0.08).tolist() for i, s in enumerate(t.shape_types) if s != "I"}


cases: dict[str, list[tuple[str, dict]]] = {"presets": [], "types_straight": [], "types_curved": []}
for name in isotile.list_presets():
    cases["presets"].append((name, IT.from_preset(name)))
for n in tiling_types():
    cases["types_straight"].append((f"IH{n}", IT(n)))
    t = get_type(n)
    c = scalloped(t)
    if c and isotile.check_prototile(n, edge_curves=c).valid:
        cases["types_curved"].append((f"IH{n}c", IT(n, edge_curves=c)))
def interpolate_spline_cache_miss(points):
    from isohedral_tiling_ui.utils import spline_cache

    return spline_cache.interpolate_spline_cached.__wrapped__(tuple(points))


print("cases:", {k: len(v) for k, v in cases.items()})


def report(label, fn_by_case):
    out = {}
    for group, items in cases.items():
        vals = [timeit(lambda f=fn_by_case, t=t: f(t)) for _, t in items]
        out[group] = (statistics.median(vals), max(vals))
    print(f"{label:62s}" + "".join(f"  {g}: med {m:7.3f} max {x:8.3f}" for g, (m, x) in out.items()))


print("\n== isotile calls (ms) ==")
report("check_prototile(type, params, curves, modes)", lambda t: check_prototile(t.type, t.parameters, edge_curves=t.edge_curves or None, edge_curve_modes=t.edge_curve_modes or None))
report("IsohedralTiling(type, params, curves, modes) constructor", lambda t: IT(t.type, t.parameters, edge_curves=t.edge_curves, edge_curve_modes=t.edge_curve_modes))
report("t.with_edge_curves(curves, modes)", lambda t: t.with_edge_curves(t.edge_curves, t.edge_curve_modes))
report("t.parameters = p (setter, mutating)", lambda t: setattr(t, "parameters", t.parameters))
report("info()", lambda t: t.info())
report("edge_outlines()", lambda t: t.edge_outlines())
report("prototile()", lambda t: t.prototile())
report("fill_region preview (100 tiles, margin 0.25) + outlines", lambda t: t.fill_region(**PREVIEW).outlines())
for n in (50, 100, 200):
    report(f"fill_region export {n} tiles, bounds (-2,-2,2,2) + outlines", lambda t, n=n: t.fill_region(**EXPORT(n)).outlines())
report("fill_region preview, polygons() (shapely)", lambda t: t.fill_region(**PREVIEW).polygons())
report("fill_region preview + colors() + aspect", lambda t: (lambda s: (s.colors(), s.aspect))(t.fill_region(**PREVIEW)))

print("\n== curve editing on one curve (ms, 5 and 21 control points) ==")
rng = np.random.default_rng(1)
for m in (5, 11, 21):
    pts = np.column_stack([np.linspace(0, 1, m), rng.normal(0, 0.05, m)])
    pts[[0, -1], 1] = 0
    lst = [tuple(p) for p in pts]
    for shape, shp in (("J", EdgeShape.J), ("U", EdgeShape.U), ("S", EdgeShape.S)):
        a = timeit(lambda: enforce_symmetry(pts, shape), 200)
        b = timeit(lambda: enforce_curve_symmetry(lst, shp), 200)
        print(f"enforce_symmetry {shape} m={m:2d}: isotile {a:.4f}  GUI utils/symmetry.py {b:.4f}")
    a = timeit(lambda: interpolate(pts), 200)
    interpolate_spline.__globals__["interpolate_spline_cached"].cache_clear()
    b = timeit(lambda: (interpolate_spline_cache_miss(lst)), 200)
    c = timeit(lambda: interpolate_spline(lst), 200)
    print(f"spline m={m:2d}: isotile.interpolate {a:.4f}  GUI spline (cache miss) {b:.4f}  GUI spline (cache hit) {c:.4f}")
