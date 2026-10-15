"""Mixed landmark geometry types (PR 136): US states with a point, a line, a polygon with a hole and a multipoint as landmarks.

    uv run python make_figures.py before   # in a checkout of main: records the error
    uv run python make_figures.py after    # in a checkout of the fix: runs and times the reconstruction
    uv run python make_figures.py plot     # writes fig_mixed.png and data/tables.md
"""
import json
import sys
import time
import warnings
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import LineString, MultiPoint, Point, Polygon

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
mode = sys.argv[1]


def landmarks(states):
    x, y = states.geometry.iloc[0].representative_point().coords[0]
    ring = [(x - 4e5, y - 4e5), (x + 4e5, y - 4e5), (x + 4e5, y + 4e5), (x - 4e5, y + 4e5)]
    hole = [(x - 1e5, y - 1e5), (x + 1e5, y - 1e5), (x + 1e5, y + 1e5), (x - 1e5, y + 1e5)]
    geoms = [Point(x, y), LineString([(x, y), (x + 6e5, y + 6e5)]), Polygon(ring, [hole]), MultiPoint([(x, y), (x + 3e5, y)])]
    return gpd.GeoDataFrame(geometry=geoms, crs=states.crs)


if mode in ("before", "after"):
    import carto_flow.data as data
    import carto_flow.flow_cartogram as flow
    from shapely import get_coordinates

    states = data.load_us_census(population=True).reset_index(drop=True)
    lm = landmarks(states)
    options = flow.MorphOptions(show_progress=False, grid=128, snapshot_every=10)
    try:
        c = flow.create_flow_cartogram(states, "Population", landmarks=lm, options=options)
    except Exception as exc:  # noqa: BLE001
        (HERE / "data/before.json").write_text(json.dumps({"error": f"{type(exc).__name__}: {exc}"}))
        sys.exit()
    out = c.get_landmarks()
    from carto_flow.geo_utils.geometry import GeometryCoordinates

    big = GeometryCoordinates(list(lm.geometry) * 3000)
    t0 = time.perf_counter()
    for _ in range(3):
        big.reconstruct()
    t = (time.perf_counter() - t0) / 3
    json.dump(
        {
            "types": [g.geom_type for g in out],
            "holes": len(out[2].interiors),
            "orig": [g.wkt for g in lm.geometry],
            "morphed": [g.wkt for g in out],
            "n_vertices": int(len(get_coordinates(np.array(list(lm.geometry) * 3000, dtype=object)))),
            "reconstruct_s": t,
            "states": [g.wkt for g in c.latest.geometry],
            "states0": [g.wkt for g in states.geometry],
        },
        open(HERE / "data/after.json", "w"),
    )
else:
    from shapely import wkt

    b = json.load(open(HERE / "data/before.json"))
    a = json.load(open(HERE / "data/after.json"))
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for ax, key, title in [(axes[0], "orig", "Input"), (axes[1], "morphed", "After the morph")]:
        for s in a["states" if key == "morphed" else "states0"]:
            g = wkt.loads(s)
            for p in getattr(g, "geoms", [g]):
                ax.plot(*p.exterior.xy, color="0.7", lw=0.5)
        for w in a[key]:
            g = wkt.loads(w)
            for p in getattr(g, "geoms", [g]):
                if p.geom_type == "Polygon":
                    ax.fill(*p.exterior.xy, alpha=0.4, color="C0")
                    for h in p.interiors:
                        ax.fill(*h.xy, color="white")
                elif p.geom_type == "LineString":
                    ax.plot(*p.xy, color="C1", lw=2)
                else:
                    ax.plot(p.x, p.y, "o", color="C3")
        ax.set_title(title)
        ax.set_aspect("equal")
        ax.axis("off")
    fig.savefig(HERE / "fig_mixed.png", dpi=130, bbox_inches="tight")
    (HERE / "data/tables.md").write_text(
        f"| | main | fix |\n|---|---|---|\n| mixed landmarks | {b['error']} | types kept: {a['types']}, holes kept: {a['holes']} |\n"
        f"| rebuild {a['n_vertices']} landmark vertices | n/a | {a['reconstruct_s']*1000:.1f} ms |\n"
    )
