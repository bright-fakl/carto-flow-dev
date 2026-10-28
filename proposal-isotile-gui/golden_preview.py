"""Golden comparison of the preview strip: tile polygons of carto-flow's IsohedralTiling.generate (what the GUI calls
today) against isotile's fill_region, for the 81 types at their defaults and the 15 presets.

Call today (preview_strip.py 311):   tiling.generate(bounds=(-1, -0.3, 1, 0.3), n_tiles=100, margin=0.25, compute_adjacency=False)
Call after the port:                 tiling.fill_region((-1, -0.3, 1, 0.3), n_tiles=100, margin=0.25)

Compared, per case:
  window    the tiles that overlap the visible window (-1, -0.3, 1, 0.3) with positive area: the same set in both?
  polygon   for the tiles of the new set, the matched old polygon (centroid within 1e-3 of a tile size):
            largest symmetric-difference area, as a fraction of the tile area
  extra     tiles outside the margin region that the old call returns on top (not drawn)
  rotation  distinct (rotation mod 360, flip) values among the tiles of the window against n_aspects: the "aspect" color
            mode of the GUI colors by rotation, the new code can color by TileSet.aspect

Run: python golden_preview.py > golden_preview.txt
"""
from __future__ import annotations

import math
import os
import sys
import time
import warnings

import numpy as np
import shapely
from scipy.spatial import cKDTree

warnings.simplefilter("ignore")
import isotile  # noqa: E402
from isotile import IsohedralTiling as IT, get_type, tiling_types  # noqa: E402
from carto_flow.symbol_cartogram.tiling import IsohedralTiling as Old  # noqa: E402

BOUNDS = (-1.0, -0.3, 1.0, 0.3)
N_TILES, MARGIN = 100, 0.25
WINDOW = shapely.box(*BOUNDS)
EPS = 1e-9
MATCH_TOL = 1e-3  # centroids of the same tile differ by the spline sampling (100 points in carto-flow, max(100, 10 m) in isotile)


def window_tiles(polys) -> set[int]:
    a = np.array([p.intersection(WINDOW).area / p.area for p in polys])
    return set(np.flatnonzero(a > EPS).tolist())


def compare(label: str, old: Old, new: IT) -> dict:
    t0 = time.perf_counter()
    res = old.generate(bounds=BOUNDS, n_tiles=N_TILES, margin=MARGIN, compute_adjacency=False)
    t_old = time.perf_counter() - t0
    t0 = time.perf_counter()
    ts = new.fill_region(BOUNDS, n_tiles=N_TILES, margin=MARGIN)
    npoly = ts.polygons()
    t_new = time.perf_counter() - t0
    opoly = res.polygons
    oc = np.array([[p.centroid.x, p.centroid.y] for p in opoly])
    nc = np.array([[p.centroid.x, p.centroid.y] for p in npoly])
    size = math.sqrt(np.mean([p.area for p in npoly]))
    dist, j = cKDTree(oc).query(nc)
    matched = dist < MATCH_TOL * size
    diff = 0.0
    for i in np.flatnonzero(matched):
        a, b = npoly[i], opoly[j[i]]
        diff = max(diff, a.symmetric_difference(b).area / a.area)
    win_old = window_tiles(opoly)
    win_new = window_tiles(npoly)
    # window tiles compared by centroid
    # window tiles compared through the matching (an old tile is the match of a new tile)
    new_win_matched = {int(j[i]) for i in win_new if matched[i]}
    old_in = win_old
    new_in = new_win_matched if all(matched[i] for i in win_new) else {-1}
    # new window tiles that the old call lacks: do they reach into the window through their curves only?
    straight = ts.vertices()
    extra = [i for i in win_new if not matched[i] or int(j[i]) not in win_old]
    extra_curve_only = sum(shapely.Polygon(straight[i]).intersection(WINDOW).area <= EPS * shapely.Polygon(straight[i]).area for i in extra)
    rot = {(round(tr.rotation % 360, 6), tr.flipped) for k, tr in enumerate(res.transforms) if k in win_old}
    return {
        "case": label,
        "n_old": len(opoly),
        "n_new": len(npoly),
        "unmatched_new": int((~matched).sum()),
        "window_old": len(win_old),
        "window_new": len(win_new),
        "window_equal": old_in == new_in,
        "extra": len(extra),
        "extra_curve_only": int(extra_curve_only),
        "max_poly_diff": diff,
        "rotations": len(rot),
        "aspects": new.type.n_aspects,
        "t_old_ms": t_old * 1000,
        "t_new_ms": t_new * 1000,
    }


rows = []
for name in isotile.list_presets():
    o = Old.from_preset(name)
    rows.append(compare(f"preset {name}", o, IT.from_preset(name)))
for n in tiling_types():
    rows.append(compare(f"IH{n}", Old(n), IT(n)))

hdr = "case                      n_old n_new unmatched_new window(old/new) equal  max_poly_diff  rotations aspects  t_old_ms t_new_ms"
print(hdr)
for r in rows:
    print(
        f"{r['case']:25s} {r['n_old']:5d} {r['n_new']:5d} {r['unmatched_new']:13d} {r['window_old']:6d}/{r['window_new']:<6d} {str(r['window_equal']):5s} "
        f"{r['max_poly_diff']:13.2e} {r['rotations']:9d} {r['aspects']:7d} {r['t_old_ms']:9.1f} {r['t_new_ms']:8.1f}"
    )

pres, types = rows[:15], rows[15:]
print()
for label, grp in (("15 presets", pres), ("81 types", types)):
    print(
        f"{label}: window tiles only in the new set {sum(r['extra'] for r in grp)} (reaching in through curves only: {sum(r['extra_curve_only'] for r in grp)}); window tile sets equal {sum(r['window_equal'] for r in grp)} of {len(grp)}; "
        f"new tiles without an old match {sum(r['unmatched_new'] for r in grp)}; "
        f"largest polygon difference {max(r['max_poly_diff'] for r in grp):.2e} of a tile area; "
        f"cases with distinct rotations != n_aspects {sum(r['rotations'] != r['aspects'] for r in grp)}; "
        f"median time old {np.median([r['t_old_ms'] for r in grp]):.1f} ms, new {np.median([r['t_new_ms'] for r in grp]):.1f} ms"
    )
