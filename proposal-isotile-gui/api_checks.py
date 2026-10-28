"""Checks of the isotile API claims of the page (section 1): each line printed is one claim and its result.

Run: python api_checks.py > api_checks.txt   (isotile origin/main, carto-flow 2.0.0 checkout for the comparison)
"""
from __future__ import annotations

import json
import os
import sys
import warnings

sys.path.insert(0, os.environ["GUI_SRC"])  # the GUI at eb7b79e (git archive), read only

import numpy as np
import isotile
from isotile import IsohedralTiling as IT, check_prototile, enforce_symmetry, interpolate, get_type, tiling_types

warnings.simplefilter("ignore")


def say(claim: str, value) -> None:
    print(f"{claim}: {value}")


# --- TileSet.aspect, colors, edge_outlines, transforms -----------------------------------------------
t = IT(28)
ts = t.fill_region((-1, -0.3, 1, 0.3), n_tiles=100, margin=0.25)
say("TileSet fields", [f for f in ("cell", "aspect", "transforms") if hasattr(ts, f)])
say("n tiles / aspects in set / n_aspects of IH28", (len(ts), sorted(set(ts.aspect.tolist())), t.type.n_aspects))
say("colors() dtype/shape/values", (ts.colors().dtype, ts.colors().shape, sorted(set(ts.colors().tolist()))))
say("edge_outlines: n edges, points per edge (straight)", (len(t.edge_outlines()), [len(e) for e in t.edge_outlines()]))
c = IT.from_preset("wavy_square")
say("edge_outlines: points per edge (wavy_square)", [len(e) for e in c.edge_outlines()])
say("edges[i] fields", [f for f in ("index", "shape_id", "shape", "reversed", "curve") if hasattr(c.edges[0], f)])

# --- edge_outlines replaces tactile.mul(shape.T, P) + shape.rev ----------------------------------------
from carto_flow.symbol_cartogram.tiling import IsohedralTiling as Old  # noqa: E402
from tactile import Point as P, mul  # noqa: E402


def old_curve_polylines(tiling):
    """prototile_editor.py 909 to 955: one polyline per edge, from the private _ih.shapes and tactile.mul."""
    from isohedral_tiling_ui.utils.spline_cache import interpolate_spline

    lines = []
    for shape_info in tiling._ih.shapes:
        raw = tiling._edge_curves.get(shape_info.id) or [(0, 0), (1, 0)]
        mode = tiling._edge_curve_modes.get(shape_info.id, "spline")
        curve = interpolate_spline([tuple(p) for p in raw]) if mode == "spline" and len(raw) >= 3 else [tuple(p) for p in raw]
        pts = [mul(shape_info.T, P(x, y)) for x, y in curve]
        if shape_info.rev:
            pts = pts[::-1]
        lines.append([(p.x, p.y) for p in pts])
    return lines


worst = 0.0
for name in isotile.list_presets():
    o = Old.from_preset(name)
    n = IT.from_preset(name)
    old_lines = old_curve_polylines(o)
    new_lines = n.edge_outlines()
    # the GUI draws one polyline per shape, in the direction of the edge; compare the point sets per edge
    for a, b in zip(old_lines, new_lines, strict=True):
        a, b = np.array(a), np.array(b)
        if len(a) != len(b):
            worst = max(worst, 1e9)
        else:
            worst = max(worst, float(np.abs(a - b).max()))
say("edge_outlines vs the GUI's _update_edge_curves, 15 presets, largest coordinate difference", f"{worst:.3g}")

# --- vertices vs _ih.vertices ---------------------------------------------------------------------------
worst = 0.0
for n_ in tiling_types():
    o = Old(n_)
    nv = IT(n_).vertices
    ov = np.array([(v.x, v.y) for v in o._ih.vertices])
    worst = max(worst, float(np.abs(ov - nv).max()))
say("vertices vs _ih.vertices, 81 types at defaults, largest difference", f"{worst:.3g}")

# --- info(): keys and values equal to carto-flow's type_info ---------------------------------------------
diff_keys, diff_aff = 0, 0
for n_ in tiling_types():
    a, b = Old.type_info(n_), IT(n_).info()
    if set(a) - set(b):
        diff_keys += 1
    for pa, pb in zip(a["parameters"], b["parameters"], strict=True):
        va = {(x["vertex"], round(x["dx_dp"], 3), round(x["dy_dp"], 3)) for x in pa["affected_vertices"]}
        vb = {(x["vertex"], round(x["dx_dp"], 3), round(x["dy_dp"], 3)) for x in pb["affected_vertices"]}
        if va != vb:
            diff_aff += 1
say("info(): types whose carto-flow type_info has a key that isotile's info() lacks (of 81)", diff_keys)
say("info(): parameters whose affected_vertices differ (3 decimals)", diff_aff)
say("info() extra keys", sorted(set(IT(28).info()) - set(Old.type_info(28))))

# --- find_types, list_presets -----------------------------------------------------------------------------
say("find_types(num_vertices=4, has_customizable_edges=True) equal", Old.find_types(num_vertices=4, has_customizable_edges=True) == isotile.find_types(num_vertices=4, has_customizable_edges=True))
say("list_presets equal keys", set(Old.list_presets()) == set(isotile.list_presets()))

# --- safe_ranges --------------------------------------------------------------------------------------------
ends = [(n_, k, e) for n_ in tiling_types() for k, row in enumerate(get_type(n_).safe_ranges) for e in row]
say("safe_ranges: ends / infinite ends / types with a parameter", (len(ends), sum(1 for *_, e in ends if not np.isfinite(e)), sum(1 for n_ in tiling_types() if get_type(n_).n_params)))
fin = [e for *_, e in ends if np.isfinite(e)]
say("safe_ranges: finite ends min / max", (min(fin), max(fin)))
n_params_total = sum(get_type(n_).n_params for n_ in tiling_types())
inside01 = 0
for n_ in tiling_types():
    ty = get_type(n_)
    for k in range(ty.n_params):
        lo, hi = ty.safe_ranges[k]
        if lo <= 0.0 and hi >= 1.0:
            inside01 += 1
say("parameters in 81 types / with [0, 1] inside safe_range", (n_params_total, inside01))

# --- the GUI's sliders [0, 1]: how often is a state invalid -------------------------------------------------
rng = np.random.default_rng(0)
tot = bad = 0
per_type_bad = {}
for n_ in tiling_types():
    ty = get_type(n_)
    if not ty.n_params:
        continue
    b = 0
    for _ in range(200):
        p = rng.uniform(0, 1, ty.n_params)
        if not check_prototile(n_, p).valid:
            b += 1
    per_type_bad[n_] = b / 200
    tot += 200
    bad += b
say("random parameters in [0,1]^k (200 per type, 55 types with parameters): invalid fraction", f"{bad / tot:.3f}")
say("types with at least 50% invalid", sum(1 for v in per_type_bad.values() if v >= 0.5))
say("types with 0% invalid", sum(1 for v in per_type_bad.values() if v == 0))

# --- slider range [0, 1] against safe_range (one-parameter slices, others at defaults) -----------------------
narrow = wide = 0
for n_ in tiling_types():
    ty = get_type(n_)
    for k in range(ty.n_params):
        lo, hi = ty.safe_ranges[k]
        if lo > 0.0 or hi < 1.0:
            narrow += 1  # part of the slider [0, 1] is invalid with the other parameters at their defaults
        if (np.isfinite(lo) and lo < 0.0) or (np.isfinite(hi) and hi > 1.0):
            wide += 1  # a finite end beyond [0, 1]: valid values exist outside [0, 1] that the GUI never offers
say("parameters whose safe_range cuts the slider [0, 1] / with a finite safe_range end beyond [0, 1]", (narrow, wide))

# --- immutability and the edit calls ------------------------------------------------------------------------------
t = IT(41)
say("with_parameters exists", hasattr(t, "with_parameters"))
say("parameters setter exists (the tiling is mutable)", isinstance(IT.parameters, property) and IT.parameters.fset is not None)
t2 = t.with_edge_curves({0: [(0, 0), (0.25, 0.1), (0.5, 0), (0.75, -0.1), (1, 0)]})
say("with_edge_curves returns a new object; the old keeps its curves", (t2 is not t, t.edge_curves == {}, sorted(t2.edge_curves)))
t3 = t2.with_edge_curves(t2.edge_curves)
say("with_edge_curves(curves) without modes resets modes to spline", t3.edge_curve_modes)
t4 = IT(41, edge_curves=t2.edge_curves, edge_curve_modes={0: "linear"})
say("modes kept when passed", t4.with_edge_curves(t4.edge_curves, t4.edge_curve_modes).edge_curve_modes)
try:
    t.with_edge_curves({0: [(0, 0), (0.5, 0.2), (1, 0)]}, {1: "linear"})
except ValueError as e:
    say("mode for an id without a curve raises", e)
i_edge = [k for k, s_ in enumerate(get_type(41).shape_types) if s_ == "I"]
say("IH41 shape ids of I edges", i_edge)
with_i = [n_ for n_ in tiling_types() if "I" in get_type(n_).shape_types]
say("types with an I edge shape (of 81)", len(with_i))
t5 = IT(with_i[0])
sid_i = [k for k, s_ in enumerate(t5.type.shape_types) if s_ == "I"]
say(f"IH{with_i[0]} shape types", t5.type.shape_types)
try:
    IT(with_i[0], edge_curves={sid_i[0]: [(0, 0), (0.5, 0.1), (1, 0)]})
except ValueError as e:
    say("curve on an I edge raises", e)
try:
    check_prototile(with_i[0], edge_curves={sid_i[0]: [(0, 0), (0.5, 0.1), (1, 0)]})
except ValueError as e:
    say("check_prototile with a curve on an I edge raises too", e)
try:
    IT(41, edge_curves={0: [(0.1, 0), (0.5, 0.1), (1, 0)]})
except ValueError as e:
    say("curve not starting at (0, 0) raises", e)
try:
    IT(41, edge_curves={9: [(0, 0), (1, 0)]})
except ValueError as e:
    say("unknown shape id raises", e)

# --- the report while dragging --------------------------------------------------------------------------------------
bow = {0: [(0, 0), (0.8, 0.5), (0.2, 0.5), (1, 0)]}
r = check_prototile(41, edge_curves=bow, edge_curve_modes={0: "linear"})
say("bow in linear mode", (r.valid, r.bad_edges, r.message))
r = check_prototile(41, edge_curves=bow)
say("bow in spline mode", (r.valid, r.bad_edges, r.message))
hair = {0: [(0, 0), (0.3, 0.6), (0.45, 0.0), (0.6, 0.6), (1, 0)]}
r = check_prototile(41, edge_curves={0: [(0, 0), (0.45, 0.5), (0.5, 0.0), (0.55, 0.5), (1, 0)]})
say("narrow finger (hairpin) in spline mode", (r.valid, r.bad_edges, r.message))
r = check_prototile(41, [0.5, 0.5][:get_type(41).n_params], edge_curves={0: [(0, 0), (1, 0)]})
say("straight edge curve valid", r.valid)

# --- io -----------------------------------------------------------------------------------------------------------------
t = IT.from_preset("puzzle_piece")
d = t.to_dict()
say("to_dict keys", sorted(d))
say("version", d["version"])
old_file = {
    "version": "1.0",
    "tiling_type": 41,
    "parameters": [0.5, 0.5],
    "edge_curves": {"0": [[0, 0], [0.25, 0.1], [0.5, 0.0], [0.75, -0.1], [1, 0]]},
    "edge_curve_modes": {"0": "linear"},
    "description": "mine",
    "metadata": {"created": "2026-01-01T00:00:00+00:00"},
}
loaded = IT.from_dict(old_file)
say("GUI file 1.0 with modes, description and metadata loads; modes kept", loaded.edge_curve_modes)
old_file2 = dict(old_file, parameters=[], tiling_type=10)
say("GUI file with parameters [] for a type without parameters", IT.from_dict(old_file2 | {"edge_curves": {}, "edge_curve_modes": {}}).parameters.tolist())
try:
    IT.from_dict(dict(old_file, parameters=[0.5]))
except ValueError as e:
    say("wrong number of parameters raises", e)
try:
    IT.from_dict(dict(old_file, version="2.0"))
except ValueError as e:
    say("version 2.0 raises", e)
rt = IT.from_dict(json.loads(json.dumps(d)))
say("round trip equal curves", all(np.array_equal(rt.edge_curves[k], t.edge_curves[k]) for k in t.edge_curves))

# --- plotting helpers ---------------------------------------------------------------------------------------------------
import matplotlib  # noqa: E402

matplotlib.use("Agg")
from isotile.plot import plot_prototile, plot_tiles  # noqa: E402

ax = plot_prototile(t)
ax2 = plot_tiles(t.fill_region((0, 0, 4, 3), n_tiles=30), color="aspect")
say("plot helpers draw into given axes (module isotile.plot, not exported in isotile.__all__)", (type(ax).__name__, hasattr(isotile, "plot")))

# --- the GUI's spline against isotile.interpolate ---------------------------------------------------------------------
from isohedral_tiling_ui.utils.spline_cache import interpolate_spline  # noqa: E402

worst = 0.0
for m in (3, 4, 5, 8, 11, 21):
    for _ in range(20):
        pts = np.column_stack([np.sort(rng.uniform(0, 1, m)), rng.normal(0, 0.1, m)])
        pts[0], pts[-1] = (0, 0), (1, 0)
        a = np.array(interpolate_spline([tuple(p) for p in pts]))
        b = interpolate(pts, "spline")
        worst = max(worst, float(np.abs(a - b).max()) if a.shape == b.shape else 1e9)
say("GUI interpolate_spline vs isotile.interpolate, 120 random curves of 3 to 21 control points, largest difference", f"{worst:.3g}")
a = interpolate_spline([(0, 0), (1, 0)])
say("two control points: GUI / isotile", (a, interpolate([(0, 0), (1, 0)]).tolist()))

# --- descriptions of the parameters ----------------------------------------------------------------------------------------
same = sum(Old.type_info(n_)["parameters"][k]["description"] == IT(n_).info()["parameters"][k]["description"] for n_ in tiling_types() for k in range(get_type(n_).n_params))
say("parameter descriptions equal to carto-flow's type_info (of 128)", same)
say("edge descriptions equal (of 81 types)", sum([e["description"] for e in Old.type_info(n_)["edges"]] == [e["description"] for e in IT(n_).info()["edges"]] for n_ in tiling_types()))
