"""Compare the two edge-curve symmetry rules: carto-flow's IsohedralTiling._enforce_edge_symmetry and the UI's
enforce_curve_symmetry (isohedral-tiling-ui, utils/symmetry.py), plus the three spline interpolations.

Run: ``uv run --project /home/fakl/carto-flow python symmetry_compare.py``
"""

from __future__ import annotations

import importlib.util
import warnings

import numpy as np
from carto_flow.symbol_cartogram.tiling import IsohedralTiling
from tactile import EdgeShape

UI_SYMMETRY = "/home/fakl/isohedral-tiling-ui/src/isohedral_tiling_ui/utils/symmetry.py"
UI_SPLINE = "/home/fakl/isohedral-tiling-ui/src/isohedral_tiling_ui/utils/spline_cache.py"


def load(path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def same(a, b) -> bool:
    return len(a) == len(b) and np.allclose(np.array(a), np.array(b), atol=1e-12)


def main() -> None:
    warnings.simplefilter("ignore")
    ui = load(UI_SYMMETRY, "ui_symmetry")
    spline = load(UI_SPLINE, "ui_spline")
    carto = IsohedralTiling(10)  # any instance; the method does not use the type
    rng = np.random.default_rng(0)
    n = 400
    print(f"symmetry rule: {n} random raw curves per case (k interior points, y uniform in [-0.3, 0.3])")
    for shape in (EdgeShape.S, EdgeShape.U):
        agree = 0
        for _ in range(n):
            k = int(rng.integers(1, 6))
            x = np.sort(rng.uniform(0.05, 0.95, k))
            pts = [(0.0, 0.0), *zip(x.tolist(), rng.uniform(-0.3, 0.3, k).tolist(), strict=True), (1.0, 0.0)]
            agree += same(carto._enforce_edge_symmetry(pts, shape), ui.enforce_curve_symmetry(pts, shape))
        print(f"  {shape.name}, x increasing: identical point lists in {agree} of {n}")
    # a curve as the UI stores it: already symmetric, with first-half control points beyond x = 0.5
    s_curve = ui.enforce_curve_symmetry([(0, 0), (0.2, 0.1), (0.7, 0.15), (0.5, 0.0), (1, 0)], EdgeShape.S)
    print("  UI output for S with a first-half control point beyond x = 0.5:", np.round(s_curve, 3).tolist())
    again = carto._enforce_edge_symmetry(s_curve, EdgeShape.S)
    print("  carto-flow applied to that UI output:", np.round(again, 3).tolist())
    print("  unchanged by carto-flow:", same(s_curve, again))
    # interpolation: carto-flow fixed 100 points, UI max(100, 10 n) points, both parametric natural cubic splines
    pts = [(0.0, 0.0), (0.2, 0.1), (0.5, 0.0), (0.8, -0.1), (1.0, 0.0)]
    a = carto._interpolate_curve(pts)
    b = spline.interpolate_spline(pts)
    print(
        f"interpolation of {len(pts)} points: carto-flow {len(a)} points, UI {len(b)} points; same curve at the "
        f"common parameters: {np.allclose(np.array(a), np.array(b), atol=1e-12)}"
    )
    pts = [(0.0, 0.0), *[(0.05 * i + 0.02, 0.1 * (-1) ** i) for i in range(1, 19)], (1.0, 0.0)]
    a = carto._interpolate_curve(pts)
    b = spline.interpolate_spline(pts)
    print(f"interpolation of {len(pts)} points: carto-flow {len(a)} points, UI {len(b)} points")
    clamp = ui.interpolate_curve(pts, 20, "spline")
    print(f"UI symmetry.interpolate_curve (clamped x-spline, not used by the UI code paths): {len(clamp)} points")


if __name__ == "__main__":
    main()
