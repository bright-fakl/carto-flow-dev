"""Figures of the border pile-up report (#86) from data/*.json and the cache data/states_morph.pkl.

    NUMBA_NUM_THREADS=8 uv run python distance_remap.py   # once, writes data/states_morph.pkl
    uv run python make_figures.py

Writes fig_resolution.png, fig_two_regions.png, fig_remap_states.png, fig_remap_toy.png, fig_profile_states.png, fig_map.png and fig_map_zoom.png next to itself.
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
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True)
    pick = {"8 sectors, dots inside the region only": next(r for r in t["rows"] if r["sectors"] == 8 and not r["signed"]),
            "8 sectors, dots outside pulled back": next(r for r in t["rows"] if r["sectors"] == 8 and r["signed"])}
    for ax, key, title in zip(axes, ("0", "1"), ("A: value 1, shrinks", "B: value 4, grows")):
        first = next(iter(pick.values()))
        ax.plot(x, first["before"][key], color=GRAY, marker="o", markersize=4, linewidth=1.8, label="no correction")
        for (lab, r), c in zip(pick.items(), (BLUE, ORANGE)):
            ax.plot(x, r["after"][key], color=c, marker="o", markersize=4, linewidth=1.8, label=lab)
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
    import landmark_warp as lw

    z = pickle.load(open(D / "states_morph.pkl", "rb"))
    L, owner_t, dot_sets, tr_orig = z["L"], z["owner_t"], z["dot_sets"], z["tr_orig"]
    geoms = [shapely.from_wkb(x) for x in z["geoms"]]
    final = [shapely.from_wkb(x) for x in z["geoms_raw"]]
    orig = list(bb.g.geometry)
    cuts = np.cumsum([0] + [len(P) for _, P in dot_sets])
    tracers = L[cuts[-1]:]
    k = 7
    owner, P0 = dot_sets[k]
    P = L[cuts[k]:cuts[k + 1]]
    bb.owner = owner
    Q = dr.Remap(geoms, tracers, owner_t, False).apply(P, owner)
    W = P0.copy()
    for r in np.unique(owner):
        sel = owner_t == r
        W[owner == r] = lw.warp_region(orig[r], final[r], 16, 0, tr_orig[sel], tracers[sel])(P0[owner == r])
    zs = {"orig": bb.band_z(orig, P0)[2], "flow": bb.band_z(geoms, P)[2], "remap": bb.band_z(geoms, Q)[2], "warp": bb.band_z(geoms, W)[2]}
    names = list(bb.g["State Name"])
    pick = [names.index("California"), names.index("Nevada")]
    shared = geoms[pick[0]].boundary.intersection(geoms[pick[1]].boundary)
    shared_o = orig[pick[0]].boundary.intersection(orig[pick[1]].boundary)

    def draw(ax, polys, pts, title, lim, dot=7):
        for i in pick:
            poly = polys[i]
            inner = poly.buffer(-0.06 * np.sqrt(poly.area))
            for pp in getattr(poly, "geoms", [poly]):
                ax.fill(*pp.exterior.xy, color="#f1f0ec", zorder=1)
            for pp in getattr(inner, "geoms", [inner]):
                if not pp.is_empty:
                    ax.fill(*pp.exterior.xy, color="white", zorder=2)
            for pp in getattr(poly, "geoms", [poly]):
                ax.plot(*pp.exterior.xy, color=GRAY, linewidth=1, zorder=3)
            sel = np.isin(owner, [i])
            ax.scatter(pts[sel, 0], pts[sel, 1], s=dot, color=BLUE if i == pick[0] else ORANGE, zorder=4)
        ax.set_xlim(lim[0], lim[2])
        ax.set_ylim(lim[1], lim[3])
        ax.set_aspect("equal")
        ax.set_title(title, fontsize=10)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.grid(False)

    lim_o = shapely.union_all([orig[i] for i in pick]).bounds
    lim_f = shapely.union_all([geoms[i] for i in pick]).bounds
    fig, axes = plt.subplots(1, 4, figsize=(16, 5))
    draw(axes[0], orig, P0, f"Original map\nborder band z = {zs['orig']:.1f} (all states)", lim_o)
    draw(axes[1], geoms, P, f"Carried by the flow\nz = {zs['flow']:.1f}", lim_f)
    draw(axes[2], geoms, Q, f"Distance remap\nz = {zs['remap']:.1f}", lim_f)
    draw(axes[3], geoms, W, f"Reference-point warp (16 vertices)\nz = {zs['warp']:.1f}", lim_f)
    fig.suptitle("California (blue) and Nevada (orange), dot seed 7; the z-score is over all 49 states; the border band (6 % of sqrt(area)) is shaded", fontsize=9, y=1.0)
    save(fig, "fig_map.png")

    zb = shared.buffer(0.18 * np.sqrt(geoms[pick[1]].area)).bounds
    fig, axes = plt.subplots(1, 2, figsize=(9, 6))
    for ax, T, title in zip(axes, (Q, W), ("Distance remap: dot carried by the flow, arrow to the corrected position", "Reference-point warp: same")):
        draw(ax, geoms, P, title, zb, dot=22)
        ax.set_title(title, fontsize=8)
        for i in pick:
            for j in np.where(np.isin(owner, [i]))[0]:
                if zb[0] <= P[j, 0] <= zb[2] and zb[1] <= P[j, 1] <= zb[3]:
                    ax.annotate("", xy=T[j], xytext=P[j], arrowprops={"arrowstyle": "->", "color": INK, "linewidth": 0.9}, zorder=5)
    save(fig, "fig_map_zoom.png")


def fig_profile_states():
    w = json.loads((D / "landmark_warp.json").read_text())
    edges = np.array(w["profiles"]["edges"])
    x = np.arange(len(edges) - 1)
    labels = [f"{a:g}-{b:g}" for a, b in zip(edges[:-1], edges[1:])]
    styles = {"original": (GRAY, "--"), "flow": (ORANGE, "-"), "distance remap": (BLUE, "-"), "warp (16 boundary vertices)": (AQUA, "-"), "warp (64 boundary vertices, 1 interior point)": ("#4a3aa7", "-")}
    fig, ax = plt.subplots(figsize=(8.5, 4))
    for name, (c, ls) in styles.items():
        if name in w["profiles"]["rows"]:
            ax.plot(x, w["profiles"]["rows"][name], color=c, linestyle=ls, marker="o", markersize=4, linewidth=1.8, label=name)
    ax.axhline(1, color=INK, linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=8)
    ax.set_xlabel("distance to the border of the region (x sqrt(area))")
    ax.set_ylabel("observed / expected dots (8 seeds, 49 states)")
    ax.legend(frameon=False, fontsize=8)
    ax.set_title("Pooled distance profile of the dots")
    save(fig, "fig_profile_states.png")


if __name__ == "__main__":
    fig_resolution()
    fig_two_regions()
    fig_remap_states()
    fig_remap_toy()
    if (D / "landmark_warp.json").exists():
        fig_profile_states()
    if (D / "states_morph.pkl").exists():
        fig_map()
