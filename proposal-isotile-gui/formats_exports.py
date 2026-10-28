"""Export tab and file formats: the Python snippet, saved designs of the old GUI loaded by isotile, SVG and GeoJSON.

1. The snippet for isotile's API is generated for a few designs (editor_model.python_snippet), executed, and the tiling it
   builds is compared with the design.
2. Files: what the old GUI writes (load_save.py `_save_config`, version 1.0 with modes; preview_strip.py
   `_generate_config_json`, version 1.0 without modes) for the 81 types, the 15 presets and 300 random edited designs is read by
   isotile.from_dict; the outcome is counted, and the geometry is compared with what the old GUI would draw from the same file.
3. SVG and GeoJSON from isotile outlines (no shapely needed) against the old exports (preview_strip.py 486 to 515 and 567 to 589),
   tile for tile.

Run: python formats_exports.py > formats_exports.txt   (GUI_SRC set; writes snippet_example.py and example.svg/.geojson)
"""
from __future__ import annotations

import json
import math
import os
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, os.environ["GUI_SRC"])
sys.path.insert(0, str(HERE))
warnings.simplefilter("ignore")
import isotile  # noqa: E402
from isotile import IsohedralTiling as IT, enforce_symmetry, get_type, tiling_types  # noqa: E402
from carto_flow.symbol_cartogram.tiling import IsohedralTiling as Old  # noqa: E402
import editor_model as em  # noqa: E402

rng = np.random.default_rng(7)

print("== 1: the Python snippet ==")
d = em.Draft.from_tiling(IT.from_preset("arrow_quad"))
code = em.python_snippet(d)
(HERE / "snippet_example.py").write_text(code + "\nprint(len(outlines), 'tiles')\n")
print(code)
ns: dict = {}
exec(code + "\nprint(len(outlines), 'tiles')", ns)  # noqa: S102
ok = np.allclose(ns["tiling"].prototile(), d.tiling().prototile())
print("snippet rebuilds the same prototile:", ok)
for name in isotile.list_presets():
    dd = em.Draft.from_tiling(IT.from_preset(name))
    nss: dict = {}
    exec(em.python_snippet(dd), nss)  # noqa: S102
    assert np.allclose(nss["tiling"].prototile(), dd.tiling().prototile()), name
print("snippet executed and equal for all 15 presets")


def gui_save_config(type_number, parameters, curves, modes, description="x"):
    """load_save.py _save_config (version 1.0, with modes, description, metadata)."""
    return {
        "version": "1.0",
        "tiling_type": type_number,
        "parameters": list(parameters),
        "edge_curves": {str(k): [list(p) for p in v] for k, v in curves.items()},
        "edge_curve_modes": {str(k): v for k, v in modes.items()},
        "description": description,
        "metadata": {"created": datetime.now(timezone.utc).isoformat()},
    }


def gui_export_json(type_number, parameters, curves, modes):
    """preview_strip.py _generate_config_json: no edge_curve_modes, no description."""
    return {
        "version": "1.0",
        "tiling_type": type_number,
        "parameters": list(parameters),
        "edge_curves": {str(k): [list(p) for p in v] for k, v in curves.items()},
        "metadata": {"created": datetime.now(timezone.utc).isoformat()},
    }


print("\n== 2: files written by the old GUI, read by isotile ==")
designs = []
for n in tiling_types():
    o = Old(n)
    designs.append((f"IH{n}", n, list(o._ih.parameters), {}, {}))
for name in isotile.list_presets():
    o = Old.from_preset(name)
    designs.append((f"preset {name}", o._type, list(o._ih.parameters), dict(o._edge_curves), dict(o._edge_curve_modes)))
n_curved_random = 0
while n_curved_random < 300:
    n = int(rng.choice(tiling_types()))
    t = get_type(n)
    ids = [s for s, sh in enumerate(t.shape_types) if sh != "I"]
    if not ids:
        continue
    curves, modes = {}, {}
    for sid in ids:
        m = int(rng.integers(3, 8))
        pts = np.column_stack([np.linspace(0, 1, m), rng.normal(0, 0.12, m)])
        pts[[0, -1], 1] = 0
        curves[sid] = enforce_symmetry(pts, t.shape_types[sid]).tolist()
        modes[sid] = str(rng.choice(["spline", "linear"]))
    designs.append((f"random IH{n}", n, list(t.default_params), curves, modes))
    n_curved_random += 1

# files that the old GUI wrote and isotile.from_dict rejects for a reason other than an invalid outline
quirks = []
t41 = get_type(41)
quirks.append(("mode for a shape id without a curve", "orphan_mode", 41, list(t41.default_params), {0: [[0, 0], [0.5, 0.1], [1, 0]]}, {0: "spline", 1: "linear"}))
quirks.append(("parameters of the wrong length", "bad_params", 41, [0.5], {}, {}))
i_type = [n for n in tiling_types() if "I" in get_type(n).shape_types][0]
i_sid = get_type(i_type).shape_types.index("I")
quirks.append(("curve on a straight (I) edge", "i_edge", i_type, list(get_type(i_type).default_params), {i_sid: [[0, 0], [0.5, 0.1], [1, 0]]}, {}))
stats = {"ok": 0, "invalid_curves": 0, "other": 0}
by_group = {"types": [0, 0], "presets": [0, 0], "random curves": [0, 0]}  # read, rejected
geom_diff = []
modes_lost = 0
reasons: dict[str, int] = {}
for label, n, p, curves, modes in designs:
    for writer in (gui_save_config, gui_export_json):
        data = writer(n, p, curves, modes) if writer is gui_save_config else writer(n, p, curves, modes)
        data = json.loads(json.dumps(data))
        group = "types" if label.startswith("IH") else "presets" if label.startswith("preset") else "random curves"
        try:
            t = IT.from_dict(data)
            stats["ok"] += 1
            by_group[group][0] += 1
        except ValueError as e:
            by_group[group][1] += 1
            key = "invalid_curves" if "valid" in str(e) or "closer" in str(e) or "cross" in str(e) else "other"
            stats[key] += 1
            reasons[str(e)[:70]] = reasons.get(str(e)[:70], 0) + 1
            continue
        if writer is gui_export_json and any(m == "linear" for m in modes.values()):
            modes_lost += 1  # the export-dialog file has no modes: every curve is read as a spline
        if writer is gui_save_config and curves:
            import shapely

            o = Old(n, p, curves, modes)  # what the old GUI draws from the same data
            a = shapely.Polygon(o._build_prototile(o._edge_curve_modes).exterior.coords)
            b = shapely.Polygon(t.prototile())
            geom_diff.append(a.symmetric_difference(b).area / b.area)
print(f"{len(designs)} designs x 2 file kinds = {2 * len(designs)} files: read {stats['ok']}, rejected for invalid curves {stats['invalid_curves']}, other errors {stats['other']}")
for r, c in reasons.items():
    print(f"  {c:3d} x {r}")
print(f"files from the export dialog that lose a 'linear' mode on reading: {modes_lost}")
for g, (ok_, bad_) in by_group.items():
    print(f"  {g:14s}: read {ok_}, rejected {bad_}")
print(f"curved prototile of the old GUI vs isotile prototile(), {len(geom_diff)} curved designs read from the GUI save file: "
      f"symmetric difference of the polygons, largest {max(geom_diff):.3g} of the tile area, median {np.median(geom_diff):.3g}")

print("\nfiles the old GUI can write that isotile.from_dict rejects, and Draft.from_dict (editor_model) repairs:")
for label, _, n, p, curves, modes in quirks:
    data = json.loads(json.dumps(gui_save_config(n, p, curves, modes)))
    try:
        IT.from_dict(data)
        a = "read"
    except ValueError as e:
        a = f"ValueError: {str(e)[:70]}"
    d = em.Draft.from_dict(data)
    try:
        d.tiling()
        b = "read"
    except ValueError as e:
        b = f"ValueError: {str(e)[:70]}"
    print(f"  {label:38s} isotile.from_dict: {a};  Draft.from_dict + tiling(): {b}")

print("\n== 3: SVG and GeoJSON ==")
BOUNDS = (-2, -2, 2, 2)


def svg_new(t: IT, n_tiles: int, colors) -> str:
    ts = t.fill_region(BOUNDS, n_tiles=n_tiles, margin=0.1)
    out = ts.outlines()
    xmin, ymin, xmax, ymax = BOUNDS
    W = H = 800
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}px" height="{H}px" viewBox="0 0 {W} {H}">',
             f'<rect x="0" y="0" width="{W}" height="{H}" fill="white"/>']
    for k in range(len(ts)):
        sx = (out[k, :, 0] - xmin) / (xmax - xmin) * W
        sy = (ymax - out[k, :, 1]) / (ymax - ymin) * H
        pts = " ".join(f"{a:.3f},{b:.3f}" for a, b in zip(sx, sy))
        parts.append(f'<polygon points="{pts}" fill="{colors[k]}" stroke="#333333" stroke-width="0.5" opacity="0.85"/>')
    parts.append("</svg>")
    return "\n".join(parts)


def geojson_new(t: IT, n_tiles: int) -> dict:
    ts = t.fill_region(BOUNDS, n_tiles=n_tiles, margin=0.1)
    out = ts.outlines()
    col = ts.colors()
    feats = []
    for k in range(len(ts)):
        ring = np.vstack([out[k], out[k][:1]])
        feats.append({
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [ring.tolist()]},
            "properties": {"tile_index": k, "cell_u": int(ts.cell[k, 0]), "cell_v": int(ts.cell[k, 1]), "aspect": int(ts.aspect[k]), "color_index": int(col[k])},
        })
    return {"type": "FeatureCollection", "features": feats}


worst_geo, n_equal_sets, n_cases = 0.0, 0, 0
import shapely  # noqa: E402

for name in isotile.list_presets():
    o = Old.from_preset(name)
    t = IT.from_preset(name)
    for n_tiles in (50, 100, 200):
        res = o.generate(bounds=BOUNDS, n_tiles=n_tiles, compute_adjacency=False)  # margin 0.1 as the old export
        gj = geojson_new(t, n_tiles)
        newp = [shapely.Polygon(f["geometry"]["coordinates"][0]) for f in gj["features"]]
        oc = np.array([[p.centroid.x, p.centroid.y] for p in res.polygons])
        nc = np.array([[p.centroid.x, p.centroid.y] for p in newp])
        from scipy.spatial import cKDTree

        dist, j = cKDTree(oc).query(nc)
        size = math.sqrt(4.4 * 4.4 / n_tiles)
        matched = dist < 1e-3 * size
        inside = np.array([p.intersection(shapely.box(*BOUNDS)).area / p.area > 1e-9 for p in newp])
        n_cases += 1
        n_equal_sets += bool(matched[inside].all())
        for i in np.flatnonzero(matched):
            worst_geo = max(worst_geo, newp[i].symmetric_difference(res.polygons[j[i]]).area / newp[i].area)
print(f"GeoJSON tiles of the 15 presets at 50, 100 and 200 tiles ({n_cases} cases): every new tile that overlaps the square (-2,-2,2,2) has an old tile with the same centroid (1e-3 of a tile size) in {n_equal_sets} cases; "
      f"largest polygon difference {worst_geo:.2e} of a tile area")

t = IT.from_preset("puzzle_piece")
ts = t.fill_region(BOUNDS, n_tiles=100, margin=0.1)
palette = ["#9ecae1", "#fdd49e", "#a1d99b", "#d4b9da"]
svg = svg_new(t, 100, [palette[int(c) % 4] for c in ts.colors()])
(HERE / "example.svg").write_text(svg)
gj = geojson_new(t, 100)
(HERE / "example.geojson").write_text(json.dumps(gj))
print(f"example.svg {len(svg) / 1024:.0f} KiB, {len(ts)} tiles; example.geojson {len(json.dumps(gj)) / 1024:.0f} KiB")
