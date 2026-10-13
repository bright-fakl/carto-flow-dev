"""Figures of the border pile-up report (#86) from data/*.json and the cache data/states_morph.pkl.

    NUMBA_NUM_THREADS=8 uv run python distance_remap.py   # once, writes data/states_morph.pkl
    uv run python make_figures.py

Writes fig_resolution.png, fig_two_regions.png, fig_remap_states.png, fig_remap_toy.png and fig_map.png next to itself.
"""
import json
import pickle
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import shapely

HERE = Path(__file__).resolve().parent
D = HERE / "data"
BLUE, ORANGE, AQUA, GRAY, INK, GRID = "#2a78d6", "#eb6834", "#1baf7a", "#8a8984", "#0b0b0b", "#dcdbd6"
plt.rcParams.update({"figure.facecolor": "white", "axes.facecolor": "white", "axes.edgecolor": GRID, "axes.labelcolor": INK, "text.color": INK,
                     "xtick.color": "#52514e", "ytick.color": "#52514e", "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
                     "axes.spines.top": False, "axes.spines.right": False, "font.size": 10, "axes.titlesize": 11, "axes.titleweight": "regular"})


def save(fig, name):
    fig.savefig(HERE / name, dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig_resolution():
    band = json.loads((D / "border_band_seed7.json").read_text())
    scan = json.loads((D / "resolution_scan_128_256_512_1024.json").read_text())
    fig, (a, b) = plt.subplots(1, 2, figsize=(11, 3.8), gridspec_kw={"width_ratios": [1.6, 1]})
    names = ["start", "defaults", "grid 512", "recompute\nevery 1", "grid 512,\nrecompute\nevery 1", "center\nrasterizer", "adaptive_dt\noff", "dt 0.05"]
    z = [r["z"] for r in band]
    cols = [GRAY] + [BLUE] * (len(z) - 1)
    a.bar(range(len(z)), z, color=cols, width=0.6)
    a.set_xticks(range(len(z)))
    a.set_xticklabels(names, fontsize=7.5)
    a.set_ylabel("border band z-score")
    a.set_title("Current code, dot seed 7")
    for i, v in enumerate(z):
        a.text(i, v + 0.08, f"{v:.1f}", ha="center", fontsize=8)
    a.grid(axis="x", visible=False)
    g = [int(r["variant"].split()[1].rstrip(",")) for r in scan]
    zz = [r["z"] for r in scan]
    b.plot(g, zz, color=BLUE, marker="o", markersize=5, linewidth=2)
    b.axhline(band[0]["z"], color=GRAY, linestyle="--", linewidth=1)
    b.text(g[-1], band[0]["z"] + 0.12, "start geometry", ha="right", fontsize=8, color="#52514e")
    b.set_xscale("log", base=2)
    b.set_xticks(g)
    b.set_xticklabels([str(x) for x in g])
    b.set_xlabel("grid size (field recomputed every iteration)")
    b.set_title("Falls with the resolution")
    b.set_ylim(0, 4.6)
    save(fig, "fig_resolution.png")


def fig_two_regions():
    t = json.loads((D / "two_regions.json").read_text())
    edges = np.array(t["edges"])
    x = np.arange(len(edges) - 1)
    labels = [f"{a:g}-{b:g}" for a, b in zip(edges[:-1], edges[1:])]
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6), sharey=True)
    colors = [BLUE, AQUA, ORANGE, "#4a3aa7"]
    for ax, key, title in zip(axes, ("0", "1"), ("A: value 1, shrinks", "B: value 4, grows")):
        for r, c in zip(t["rows"], colors):
            v = [np.nan if y is None else y for y in r["ratio_by_distance"][key]]
            ax.plot(x, v, color=c, marker="o", markersize=4, linewidth=1.8, label=r["variant"])
        ax.axhline(1, color=GRAY, linestyle="--", linewidth=1)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
        ax.set_xlabel("distance to the shared border (x sqrt(area))")
        ax.set_title(title)
    axes[0].set_ylabel("observed / expected dots")
    axes[0].legend(frameon=False, fontsize=8, loc="upper left")
    save(fig, "fig_two_regions.png")


def fig_remap_states():
    d = json.loads((D / "distance_remap_states.json").read_text())["states"]["seeds"]
    s = json.loads((D / "sector_remap.json").read_text())
    fig, (a, b) = plt.subplots(1, 2, figsize=(10, 3.8), gridspec_kw={"width_ratios": [1, 1.2]})
    xs = {"before": 0, "region": 1, "pooled": 2}
    for r in d:
        ys = [r["before"], r["region"]["z"], r["pooled"]["z"]]
        a.plot([0, 1, 2], ys, color=GRAY, linewidth=0.8, alpha=0.7, marker="o", markersize=3)
    means = [np.mean([r["before"] for r in d]), np.mean([r["region"]["z"] for r in d]), np.mean([r["pooled"]["z"] for r in d])]
    a.plot([0, 1, 2], means, color=BLUE, marker="o", markersize=7, linewidth=2.5)
    for i, m in enumerate(means):
        a.text(i + 0.06, m, f"{m:.1f}", color=BLUE, fontsize=9, va="center")
    a.axhline(0, color=INK, linewidth=0.8)
    a.set_xticks([0, 1, 2])
    a.set_xticklabels(["no correction", "per-region\nremap", "pooled\nremap"])
    a.set_xlim(-0.3, 2.5)
    a.set_ylabel("border band z-score (8 dot seeds)")
    a.set_title("Per region beats pooling")
    a.grid(axis="x", visible=False)
    rows1 = [r for r in s["rows"] if r["sectors"] == 1]
    rows8 = [r for r in s["rows"] if r["sectors"] == 8]
    for rows, c, lab in ((rows1, BLUE, "1 sector (per region)"), (rows8, ORANGE, "8 sectors")):
        n = [r["tracers_per_region"] for r in rows]
        zm = [r["z_mean"] for r in rows]
        sd = [r["z_sd"] / np.sqrt(8) for r in rows]
        b.errorbar(n, zm, yerr=sd, color=c, marker="o", markersize=5, linewidth=1.8, capsize=2, label=lab)
    b.axhline(s["before_mean"], color=GRAY, linestyle="--", linewidth=1)
    b.text(45, s["before_mean"] - 0.28, "no correction", fontsize=8, color="#52514e")
    b.set_xscale("log")
    b.set_xticks([50, 100, 200, 500, 2000])
    b.set_xticklabels(["50", "100", "200", "500", "2000"])
    b.set_xlabel("tracer points per region")
    b.set_ylabel("mean z-score (bars: s.e. over seeds)")
    b.set_ylim(0, 5)
    b.set_title("Few tracers suffice; sectors do not help")
    b.legend(frameon=False, fontsize=8, loc="center right")
    save(fig, "fig_remap_states.png")


def fig_remap_toy():
    t = json.loads((D / "toy_remap.json").read_text())
    edges = np.array(t["edges"])
    x = np.arange(len(edges) - 1)
    labels = [f"{a:g}-{b:g}" for a, b in zip(edges[:-1], edges[1:])]
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6), sharey=True)
    for ax, key, title in zip(axes, ("0", "1"), ("A: value 1, shrinks", "B: value 4, grows")):
        r1 = next(r for r in t["rows"] if r["sectors"] == 1)
        r8 = next(r for r in t["rows"] if r["sectors"] == 8)
        ax.plot(x, r1["before"][key], color=GRAY, marker="o", markersize=4, linewidth=1.8, label="no correction")
        ax.plot(x, r1["after"][key], color=BLUE, marker="o", markersize=4, linewidth=1.8, label="remap per region")
        ax.plot(x, r8["after"][key], color=ORANGE, marker="o", markersize=4, linewidth=1.8, label="remap, 8 sectors")
        ax.axhline(1, color=INK, linestyle="--", linewidth=0.8)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
        ax.set_xlabel("distance to the shared border (x sqrt(area))")
        ax.set_title(title)
    axes[0].set_ylabel("observed / expected dots")
    axes[0].legend(frameon=False, fontsize=8, loc="upper left")
    save(fig, "fig_remap_toy.png")


def fig_map():
    import border_band as bb
    import distance_remap as dr

    z = pickle.load(open(D / "states_morph.pkl", "rb"))
    L, owner_t, dot_sets = z["L"], z["owner_t"], z["dot_sets"]
    geoms = [shapely.from_wkb(x) for x in z["geoms"]]
    cuts = np.cumsum([0] + [len(P) for _, P in dot_sets])
    tracers = L[cuts[-1]:]
    m = dr.Remap(geoms, tracers, owner_t, False)
    owner, _ = dot_sets[7]
    P = L[cuts[7]:cuts[8]]
    Q = m.apply(P, owner)
    names = list(bb.g["State Name"])
    pick = [names.index("California"), names.index("Nevada")]
    fig, axes = plt.subplots(1, 3, figsize=(14, 5.2), gridspec_kw={"width_ratios": [1, 1, 1]})
    allb = shapely.union_all([geoms[i] for i in pick]).bounds
    shared = geoms[pick[0]].boundary.intersection(geoms[pick[1]].boundary)

    def draw(ax, pts, title, zoom=None):
        for i in pick:
            poly = geoms[i]
            inner = poly.buffer(-0.06 * np.sqrt(poly.area))
            for pp in getattr(poly, "geoms", [poly]):
                ax.fill(*pp.exterior.xy, color="#f1f0ec", zorder=1)
            for pp in getattr(inner, "geoms", [inner]):
                if not pp.is_empty:
                    ax.fill(*pp.exterior.xy, color="white", zorder=2)
            for pp in getattr(poly, "geoms", [poly]):
                ax.plot(*pp.exterior.xy, color=GRAY, linewidth=1, zorder=3)
            sel = np.isin(owner, [i])
            ax.scatter(pts[sel, 0], pts[sel, 1], s=7 if zoom is None else 22, color=BLUE if i == pick[0] else ORANGE, zorder=4)
        lim = allb if zoom is None else zoom
        ax.set_xlim(lim[0], lim[2])
        ax.set_ylim(lim[1], lim[3])
        ax.set_aspect("equal")
        ax.set_title(title)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.grid(False)

    draw(axes[0], P, "Carried by the flow")
    draw(axes[1], Q, "After the distance remap")
    zb = shared.buffer(0.18 * np.sqrt(geoms[pick[1]].area)).bounds
    draw(axes[2], P, "Zoom: dot before, arrow to after", zoom=zb)
    for i in pick:
        sel = np.where(np.isin(owner, [i]))[0]
        for j in sel:
            if zb[0] <= P[j, 0] <= zb[2] and zb[1] <= P[j, 1] <= zb[3]:
                axes[2].annotate("", xy=Q[j], xytext=P[j], arrowprops={"arrowstyle": "->", "color": INK, "linewidth": 0.9}, zorder=5)
    fig.suptitle("California (blue) and Nevada (orange), dot seed 7; the border band (6 % of sqrt(area)) is shaded", fontsize=9, y=0.98)
    save(fig, "fig_map.png")


if __name__ == "__main__":
    fig_resolution()
    fig_two_regions()
    fig_remap_states()
    fig_remap_toy()
    if (D / "states_morph.pkl").exists():
        fig_map()
