"""Proof of concept, part 2: the 15 isohedral presets and the 81 types, old IsohedralTiling against isotile.

Compared per preset (carto-flow's curves and parameters passed to isotile, so that only the tiling code differs):
tile polygons, edge and vertex-only adjacency (carto-flow: shared vertices within 0.01 tile sizes; isotile: lattice
table), area centroids against the isotile straight centroid, and the data of the presets themselves.
Then all 81 types at the defaults.

Run: python poc_presets.py > poc_presets.txt   (scratch venv with carto-flow and isotile installed)
"""

from __future__ import annotations

import warnings

import isotile
import isotile.presets as P
import numpy as np
import shapely
from carto_flow.symbol_cartogram.tiling import IsohedralTiling as Old
from isotile import IsohedralTiling as New
from scipy.spatial import cKDTree
from shapely.geometry import Polygon

BOUNDS = (-1.0, -1.0, 1.0, 1.0)
MARGIN = 0.1
N_TILES = 100


def vertex_gap(a: np.ndarray, b: np.ndarray) -> float:
    d = np.linalg.norm(a[:, None] - b[None], axis=2)
    return float(max(d.min(axis=1).max(), d.min(axis=0).max()))


def compare(label: str, old_tiling: Old, new_tiling: New) -> dict:
    res = old_tiling.generate(bounds=BOUNDS, n_tiles=N_TILES, margin=MARGIN)
    s = res.tile_size
    tiles = new_tiling.fill_region(BOUNDS, n_tiles=N_TILES, margin=MARGIN)
    polys = tiles.polygons()
    c_new = np.array([[p.centroid.x, p.centroid.y] for p in polys])
    c_old = np.array([[p.centroid.x, p.centroid.y] for p in res.polygons])
    dist, j = cKDTree(c_new).query(c_old)
    matched = dist < 0.05 * s  # the curved centroids differ slightly when the sample counts differ
    ci = np.flatnonzero(matched)
    li = j[ci]
    if not len(ci):
        raise RuntimeError(f"{label}: no tile of the old class has an isotile tile at the same centroid")
    gap = max(vertex_gap(np.array(res.polygons[i].exterior.coords[:-1]), np.array(polys[k].exterior.coords[:-1])) for i, k in zip(ci, li, strict=True)) / s
    e_new = tiles.adjacency("edge")[li][:, li].toarray()
    v_new = tiles.adjacency("vertex-only")[li][:, li].toarray()
    e_old = np.asarray(res.adjacency)[np.ix_(ci, ci)]
    v_old = np.asarray(res.vertex_adjacency)[np.ix_(ci, ci)]
    straight = tiles.centroids
    shift = np.linalg.norm(straight[li] - c_new[li], axis=1) / s
    return {
        "case": label,
        "old": len(res.polygons),
        "cover": len(tiles),
        "matched": int(matched.sum()),
        "vertex_gap": gap,
        "edge_old_only": int((e_old & ~e_new).sum() // 2),
        "edge_new_only": int((~e_old & e_new).sum() // 2),
        "vertex_diff": int((v_new != v_old).sum() // 2),
        "centroid_shift_max": float(shift.max()),
        "n_base_vertices": f"{res.n_base_vertices}/{new_tiling.type.n_vertices}",
    }


def main() -> None:
    rows = []
    for name, p in Old._PRESETS.items():
        old = Old.from_preset(name)
        kwargs = {"tiling_type": p["tiling_type"]}
        if "parameters" in p:
            kwargs["parameters"] = p["parameters"]
        new = New(
            p["tiling_type"],
            p.get("parameters"),
            edge_curves=p.get("edge_curves"),
            edge_curve_modes=p.get("edge_curve_modes"),
        )
        rows.append(compare(name, old, new))
    cols = [k for k in rows[0] if k != "case"]
    print("15 presets, carto-flow data passed to both; region (-1,-1,1,1), margin 0.1, n_tiles 100\n")
    print(f"{'preset':<22}" + "".join(f"{k:>20}" for k in cols))
    for r in rows:
        print(f"{r['case']:<22}" + "".join(f"{r[k]:>20.3g}" if isinstance(r[k], float) else f"{r[k]:>20}" for k in cols))

    print("\nPreset data: carto-flow's preset against isotile's preset (same name)")
    for name, p in Old._PRESETS.items():
        q = P.preset_arguments(name)
        diffs = []
        if p["tiling_type"] != q["tiling_type"]:
            diffs.append("type")
        pa, pb = p.get("parameters"), q.get("parameters")
        if (pa is None) != (pb is None) or (pa is not None and not np.allclose(pa, pb)):
            diffs.append("parameters")
        ea, eb = p.get("edge_curves") or {}, q.get("edge_curves") or {}
        if set(ea) != set(eb):
            diffs.append("curve ids")
        else:
            diffs += [f"curve {k}" for k in ea if len(ea[k]) != len(eb[k]) or not np.allclose(ea[k], eb[k])]
        if diffs:
            print(f"  {name}: differs in {', '.join(diffs)}")
    print("  (all other presets: equal; explicit 'spline' modes of carto-flow are isotile's default)")

    # all 81 types at the defaults
    print("\nAll 81 types at the defaults, region (-1,-1,1,1), margin 0.1, n_tiles 100:")
    tot = dict(old=0, cover=0, matched=0, e_old=0, e_new=0, v=0)
    bad_count = []
    lacking = []
    worst = 0.0
    for number in isotile.tiling_types():
        r = compare(f"IH{number}", Old(number), New(number))
        tot["old"] += r["old"]
        tot["cover"] += r["cover"]
        tot["matched"] += r["matched"]
        tot["e_old"] += r["edge_old_only"]
        tot["e_new"] += r["edge_new_only"]
        tot["v"] += r["vertex_diff"]
        worst = max(worst, r["vertex_gap"])
        if r["cover"] > r["matched"]:
            lacking.append((number, r["cover"] - r["matched"], r["cover"]))
        if r["old"] != r["cover"]:
            bad_count.append((number, r["old"], r["cover"]))
    print(f"  old tiles {tot['old']}, isotile tiles {tot['cover']}, matched {tot['matched']}, largest vertex gap {worst:.1e} tile sizes, "
          f"edge pairs only in old {tot['e_old']}, only in isotile {tot['e_new']}, vertex-only differences {tot['v']}")
    print(f"  types whose tile counts differ (old, cover): {len(bad_count)} of 81, e.g. {bad_count[:5]}")
    print(
        f"  tiles that overlap the region and that the current IsohedralTiling.generate lacks: {sum(k for _, k, _ in lacking)} "
        f"of {tot['cover']} in {len(lacking)} of 81 types (type, missing, tiles): {lacking}"
    )


if __name__ == "__main__":
    warnings.simplefilter("ignore")
    main()
