"""Before / after of prescale_components with landmarks (PR 134): two separate squares with values 1 and 4 and 300 dots in each.

    uv run python make_figures.py before   # in a checkout of main
    uv run python make_figures.py after    # in a checkout of the fix
    uv run python make_figures.py plot     # writes fig_before_after.png and data/tables.md
"""
import json
import sys
import warnings
from pathlib import Path

import geopandas as gpd
import numpy as np
import shapely
from shapely.geometry import box

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
mode = sys.argv[1]

gdf = gpd.GeoDataFrame({"v": [1.0, 4.0]}, geometry=[box(0, 0, 1, 1), box(3, 0, 4, 1)])
rng = np.random.default_rng(0)
points = np.vstack([np.column_stack([rng.uniform(0, 1, 300), rng.uniform(0, 1, 300)]), np.column_stack([rng.uniform(3, 4, 300), rng.uniform(0, 1, 300)])])
owner = np.repeat([0, 1], 300)

if mode in ("before", "after"):
    import carto_flow.flow_cartogram as flow

    options = flow.MorphOptions(show_progress=False, grid=128, prescale_components=True, mean_tol=0.005, max_tol=0.01)
    c = flow.create_flow_cartogram(gdf, "v", landmarks=gpd.GeoSeries(shapely.points(points)), options=options)
    geoms = list(c.get_geometry())
    P = shapely.get_coordinates(np.asarray(c.get_landmarks(), dtype=object))
    inside = np.array([shapely.contains(geoms[o], shapely.Point(p)) for o, p in zip(owner, P)])
    np.savez(HERE / "data" / f"{mode}.npz", P=P, inside=inside, polys=np.array([shapely.get_coordinates(g) for g in geoms], dtype=object), areas=np.array([g.area for g in geoms]))
else:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    BLUE, ORANGE, GRAY = "#2a78d6", "#eb6834", "#8a8984"
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.4), sharey=True)
    axes[0].set_title("Input: two separate squares, values 1 and 4")
    for g in gdf.geometry:
        axes[0].fill(*g.exterior.xy, color="#f1f0ec", zorder=1)
        axes[0].plot(*g.exterior.xy, color=GRAY, linewidth=1)
    axes[0].scatter(points[:, 0], points[:, 1], s=4, color=BLUE, zorder=3)
    rows = []
    for ax, mode_, title in ((axes[1], "before", "Before the fix"), (axes[2], "after", "After the fix")):
        z = np.load(HERE / "data" / f"{mode_}.npz", allow_pickle=True)
        for poly in z["polys"]:
            ax.fill(poly[:, 0], poly[:, 1], color="#f1f0ec", zorder=1)
            ax.plot(poly[:, 0], poly[:, 1], color=GRAY, linewidth=1)
        P, ins = z["P"], z["inside"]
        ax.scatter(P[ins, 0], P[ins, 1], s=4, color=BLUE, zorder=3, label="inside its region")
        ax.scatter(P[~ins, 0], P[~ins, 1], s=4, color=ORANGE, zorder=3, label="outside")
        ax.set_title(f"{title}: {100 * ins.mean():.0f} % of the dots inside")
        rows.append((title, [round(float(ins[owner == r].mean()), 3) for r in (0, 1)], [round(float(a), 3) for a in z["areas"]]))
    h, l = axes[2].get_legend_handles_labels()
    fig.legend(h, l, frameon=False, fontsize=9, loc="lower center", ncol=2, bbox_to_anchor=(0.5, -0.06), markerscale=3)
    for ax in axes:
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.grid(False)
    fig.savefig(HERE / "fig_before_after.png", dpi=150, bbox_inches="tight")
    lines = ["| | share of the dots inside their region (square 1, square 2) | final areas |", "|---|---|---|"]
    lines += [f"| {t} | {i[0]}, {i[1]} | {a[0]}, {a[1]} |" for t, i, a in rows]
    (HERE / "data" / "tables.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
