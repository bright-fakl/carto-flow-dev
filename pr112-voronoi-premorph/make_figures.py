# Produces every figure of this page and prints the metrics tables (JSON lines).
#
# Part 1 (premorph_states.png, premorph_lognormal.png, premorph_districts.png): five ways to run the
# weighted Voronoi cartogram: (a) fixed outline, (b) ElasticBoundary(0.05) co-evolving with the
# relaxation, (c) a flow-cartogram pre-morph followed by Voronoi with a rigid boundary on the morphed
# outline, (d) pre-morph + ElasticBoundary(0.02), (e) as (c) with RasterBackend(generator_anchor=0.5),
# which is what create_voronoi_cartogram(premorph=True) runs.
# Part 2 (premorph_tx_arrows.png, premorph_tx_trace.png): per-state displacement of the cells from the
# flow-morphed and the original centroids, and a per-iteration trace of the rigid run on the morphed
# states (TX, LA, OK).
# Part 3 (premorph_tx.png): flow cartogram, (c) and (e) side by side with Texas highlighted on the
# three datasets, and an anchor sweep (table only).
# Inputs: 49 US states with population, the same with lognormal weights (seed 1, ~1400x range), and
# 432 congressional districts with population. Run from a carto-flow checkout of
# feat/voronoi-premorph: `NUMBA_NUM_THREADS=8 uv run python make_figures.py`.
import json
import time
import warnings
from pathlib import Path

import matplotlib
import numpy as np
import shapely
import shapely.affinity
from scipy.spatial import procrustes
from scipy.stats import spearmanr

matplotlib.use("Agg")
import matplotlib.pyplot as plt

import carto_flow.data as examples
import carto_flow.flow_cartogram as flow
import carto_flow.voronoi_cartogram as vor
from carto_flow.voronoi_cartogram.backends import _resolve_relaxation

HERE = Path(__file__).resolve().parent
VARIANTS = {
    "a": "(a) fixed outline",
    "b": "(b) elastic co-evolution, 0.05",
    "c": "(c) flow pre-morph + rigid",
    "d": "(d) flow pre-morph + elastic 0.02",
    "e": "(e) pre-morph + rigid + anchor 0.5",
}
NAMED = ("TX", "LA", "OK", "FL", "CA", "NM", "AZ", "NY", "MS", "AR")
TX_COLOR = "#e8762b"


def centroids(geoms):
    c = shapely.centroid(np.asarray(geoms, dtype=object))
    return np.column_stack([shapely.get_x(c), shapely.get_y(c)])


def morph(gdf, col):
    t = time.perf_counter()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        m = flow.morph_gdf(
            gdf,
            col,
            options=flow.MorphOptions.preset_balanced().copy_with(area_scale=1e-6, n_iter=400, show_progress=False),
        )
    t_morph = time.perf_counter() - t
    morphed = m.to_geodataframe()
    # The flow output can contain slightly invalid rings; repair them before the union.
    morphed = morphed.set_geometry(shapely.make_valid(np.asarray(morphed.geometry, dtype=object)))
    return morphed, t_morph, m.status.name


def symdiff(g1, g2):
    k = np.sqrt(g2.area / g1.area)
    g1s = shapely.affinity.scale(g1, k, k, origin=g1.centroid)
    g1s = shapely.affinity.translate(g1s, g2.centroid.x - g1s.centroid.x, g2.centroid.y - g1s.centroid.y)
    return g1s.symmetric_difference(g2).area / g2.area


def to_orig_frame(xy, outline, orig_outline):
    """Scale and shift coordinates so that *outline* has the original area and centroid."""
    s = np.sqrt(orig_outline.area / outline.area)
    c, oc = outline.centroid, orig_outline.centroid
    return (xy - [c.x, c.y]) * s + [oc.x, oc.y]


def run(gdf, col, keys="abcde"):
    """The variants on one dataset; returns per-variant results, the morphed regions and the morph time."""
    w = gdf[col].to_numpy(float)
    orig_c = centroids(gdf.geometry)
    orig_outline = shapely.union_all(np.asarray(gdf.geometry, dtype=object))
    r0 = np.sqrt(orig_outline.area / len(gdf))
    morphed, t_morph, morph_status = morph(gdf, col)
    flow_c = centroids(morphed.geometry)
    flow_outline = shapely.union_all(np.asarray(morphed.geometry, dtype=object))
    flow_c_o = to_orig_frame(flow_c, flow_outline, orig_outline)
    regions = np.asarray(morphed.geometry, dtype=object)
    opts = vor.VoronoiOptions(n_iter=300, area_cv_tol=0.05)
    setups = {
        "a": (gdf, vor.RasterBackend(resolution=256), 0.0),
        "b": (gdf, vor.RasterBackend(resolution=256, boundary=vor.ElasticBoundary(0.05)), 0.0),
        "c": (morphed, vor.RasterBackend(resolution=256), t_morph),
        "d": (morphed, vor.RasterBackend(resolution=256, boundary=vor.ElasticBoundary(0.02)), t_morph),
        "e": (morphed, vor.RasterBackend(resolution=256, generator_anchor=0.5), t_morph),
    }
    out = {}
    for key in keys:
        src, backend, t0 = setups[key]
        t = time.perf_counter()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = vor.create_voronoi_cartogram(src, weights=w, backend=backend, options=opts)
        t_vor = time.perf_counter() - t
        cells = np.asarray(r.cells, dtype=object)
        a = shapely.area(cells)
        err = np.abs(a / (w / w.sum() * a.sum()) - 1) * 100
        cell_c = centroids(cells)
        outline = r._field._current_boundary
        # Position fidelity in units of the mean original cell radius; the final map is
        # rescaled to the original area so the comparison is size-independent.
        cc = to_orig_frame(cell_c, outline, orig_outline)
        d_orig = np.linalg.norm(cc - orig_c, axis=1)
        d_flow = np.linalg.norm(cc - flow_c_o, axis=1)
        _, _, disparity = procrustes(orig_c, cell_c)
        rank = 0.5 * (spearmanr(orig_c[:, 0], cell_c[:, 0]).correlation + spearmanr(orig_c[:, 1], cell_c[:, 1]).correlation)
        gen = r.positions
        lag = np.linalg.norm(gen - cell_c, axis=1) / np.sqrt(a / np.pi)
        compact = 4 * np.pi * a / shapely.length(cells) ** 2
        split = sum(1 for c in cells if c.geom_type == "MultiPolygon" and sorted(g.area for g in c.geoms)[-2] > 0.01 * c.area)
        # Share of each morphed region covered by its own cell (pre-morph variants only).
        own = shapely.area(shapely.intersection(cells, regions)) / shapely.area(regions) if key in "cde" else None
        out[key] = {
            "cells": cells, "outline": outline, "cc_o": cc, "flow_c_o": flow_c_o, "orig_c": orig_c,
            "d_orig": d_orig, "d_flow": d_flow, "own": own, "r0": r0,
            "mean_err": float(err.mean()), "max_err": float(err.max()),
            "d_orig_med": float(np.median(d_orig) / r0), "d_orig_max": float(d_orig.max() / r0),
            "d_flow_med": float(np.median(d_flow) / r0), "d_flow_max": float(d_flow.max() / r0),
            "own_mean": float(own.mean()) if own is not None else None,
            "procrustes": float(disparity), "rank": float(rank),
            "outline_vs_flow": symdiff(outline, flow_outline), "outline_vs_orig": symdiff(outline, orig_outline),
            "lag_med": float(np.median(lag)), "lag_max": float(lag.max()), "compact": float(np.mean(compact)),
            "split": split, "it": r.metrics["n_iterations"], "t_vor": t_vor, "t_total": t_vor + t0,
            "x_orig": orig_c[:, 0],
        }
    return out, morphed, t_morph, morph_status


def fill(ax, geoms, colors, lw=0.3, edge="white"):
    for g, color in zip(geoms, colors, strict=True):
        for part in shapely.get_parts(g):
            if part.geom_type == "Polygon" and not part.is_empty:
                ax.fill(*part.exterior.xy, facecolor=color, edgecolor=edge, linewidth=lw)


def plot_variants(res, title, filename):
    fig, axes = plt.subplots(1, len(res), figsize=(5.5 * len(res), 4.6))
    x = next(iter(res.values()))["x_orig"]
    colors = plt.get_cmap("viridis")((x - x.min()) / np.ptp(x))
    for ax, (key, r) in zip(axes, res.items(), strict=True):
        fill(ax, r["cells"], colors)
        ax.set_title(
            f"{VARIANTS[key]}\nmean err {r['mean_err']:.2f} %, offset vs flow {r['d_flow_med']:.2f} R (med), "
            f"lag {r['lag_med']:.3f}, {r['it']} it, {r['t_total']:.1f} s",
            fontsize=8,
        )
        ax.set_aspect("equal")
        ax.axis("off")
    fig.suptitle(title + " — cells colored by the original longitude of their region", fontsize=10)
    fig.savefig(HERE / filename, dpi=100, bbox_inches="tight")
    plt.close(fig)


def print_rows(name, res, t_morph, morph_status):
    for key, r in res.items():
        print(json.dumps({"table": "variants", "dataset": name, "variant": VARIANTS[key], "morph_s": round(t_morph, 1),
                          "morph": morph_status, **{k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()
                                                    if not isinstance(v, (np.ndarray, shapely.Geometry)) and k != "x_orig"}}), flush=True)


def print_states(res, abbr):
    """Per-state offsets (cell radii and km) and the ten worst states per variant."""
    for key, r in res.items():
        r0 = r["r0"]
        row = {"table": "states", "variant": VARIANTS[key]}
        for s in NAMED:
            i = abbr.index(s)
            own = f", own {r['own'][i]:.2f}" if r["own"] is not None else ""
            row[s] = (f"flow {r['d_flow'][i] / r0:.2f} R / {r['d_flow'][i] / 1e3:.0f} km, "
                      f"orig {r['d_orig'][i] / r0:.2f} R / {r['d_orig'][i] / 1e3:.0f} km{own}")
        row["worst_vs_flow"] = ", ".join(f"{abbr[i]} {r['d_flow'][i] / r0:.2f}" for i in np.argsort(-r["d_flow"])[:10])
        row["worst_vs_orig"] = ", ".join(f"{abbr[i]} {r['d_orig'][i] / r0:.2f}" for i in np.argsort(-r["d_orig"])[:10])
        print(json.dumps(row), flush=True)


def plot_arrows(res, gdf, filename):
    """Arrows from the flow-morphed (top) and original (bottom) centroids to the cell centroids."""
    abbr = list(gdf["State Abbreviation"])
    tx = abbr.index("TX")
    keys = [k for k in "abce" if k in res]
    fig, axes = plt.subplots(2, len(keys), figsize=(5.5 * len(keys), 7.5))
    orig_outline = shapely.union_all(np.asarray(gdf.geometry, dtype=object))
    oc = orig_outline.centroid
    for col, key in enumerate(keys):
        r = res[key]
        s = np.sqrt(orig_outline.area / r["outline"].area)
        c = r["outline"].centroid
        cells_o = [shapely.affinity.translate(shapely.affinity.scale(g, s, s, origin=(c.x, c.y)), oc.x - c.x, oc.y - c.y)
                   for g in r["cells"]]
        for row, (start, label, dist) in enumerate(((r["flow_c_o"], "flow-morphed", r["d_flow"]),
                                                    (r["orig_c"], "original", r["d_orig"]))):
            ax = axes[row, col]
            fill(ax, cells_o, ["#dddddd" if i != tx else TX_COLOR for i in range(len(cells_o))], lw=0.4)
            end = r["cc_o"]
            big = dist / r["r0"] > 1.0
            for i in range(len(end)):
                ax.annotate("", xy=end[i], xytext=start[i],
                            arrowprops={"arrowstyle": "->", "lw": 1.2 if big[i] else 0.7,
                                        "color": "#b2182b" if big[i] else "#2166ac"})
            for i in [*np.argsort(-dist)[:6].tolist(), tx]:
                ax.text(*end[i], abbr[i], fontsize=7, ha="center", va="bottom")
            ax.set_title(f"{VARIANTS[key]}\nfrom {label} centroids: median {np.median(dist) / r['r0']:.2f} R, "
                         f"TX {dist[tx] / r['r0']:.2f} R ({dist[tx] / 1e3:.0f} km)", fontsize=8)
            ax.set_aspect("equal")
            ax.axis("off")
    fig.suptitle("States, population: cells scaled to the original area; arrows from the flow-morphed (top) and "
                 "original (bottom) centroids to the cell centroids; red: more than one mean cell radius R = "
                 f"{res['a']['r0'] / 1e3:.0f} km; Texas in orange", fontsize=9)
    fig.savefig(HERE / filename, dpi=100, bbox_inches="tight")
    plt.close(fig)


def trace(morphed, gdf, col, anchor):
    """Rigid weighted run on the morphed regions, stepped by hand to record each iteration."""
    w = gdf[col].to_numpy(float)
    geoms = list(morphed.geometry)
    pos = []
    for g in geoms:
        c = g.centroid
        if not g.contains(c):
            c = g.representative_point()
        pos.append([c.x, c.y])
    pos = np.array(pos)
    outline = shapely.union_all(np.asarray(geoms, dtype=object))
    backend = vor.RasterBackend(resolution=256, generator_anchor=anchor)
    field = backend.build_field(pos, outline, weights=w, adj_pairs=None, boundary_mask=None, geometries=geoms)
    schedule = _resolve_relaxation(backend.relaxation)
    share = w / w.sum()
    traj, ratio = [pos.copy()], []
    for i in range(300):
        backend.relax_step(field, schedule(i), i)
        traj.append(field.points.copy())
        ratio.append(field._last_counts / field._last_counts.sum() / share)
        if field.area_cv() < 0.05:
            break
    cells = field.get_cells()
    return np.array(traj), np.array(ratio), cells


def plot_trace(morphed, gdf, col, filename):
    abbr = list(gdf["State Abbreviation"])
    idx = {s: abbr.index(s) for s in ("TX", "LA", "OK")}
    colors = {"TX": TX_COLOR, "LA": "#2166ac", "OK": "#7b3294"}
    runs = {a: trace(morphed, gdf, col, a) for a in (0.0, 0.5)}
    fig = plt.figure(figsize=(17, 8.5))
    grid = fig.add_gridspec(2, 3, width_ratios=[1.6, 1.6, 1])
    for k, (anchor, (traj, _, cells)) in enumerate(runs.items()):
        ax = fig.add_subplot(grid[:, k])
        fill(ax, list(morphed.geometry), ["#f0f0f0"] * len(cells), lw=0.6, edge="#999999")
        for s, i in idx.items():
            for part in shapely.get_parts(cells[i]):
                if part.geom_type == "Polygon":
                    ax.fill(*part.exterior.xy, facecolor=colors[s], alpha=0.35, edgecolor=colors[s], lw=1.2)
        ax.plot(traj[:, :, 0], traj[:, :, 1], color="#888888", lw=0.5)
        for s, i in idx.items():
            ax.plot(traj[:, i, 0], traj[:, i, 1], color=colors[s], lw=2)
            ax.plot(*traj[0, i], "o", color=colors[s], ms=5)
            ax.text(*traj[-1, i], s, fontsize=9, fontweight="bold")
        ax.set_title(f"generator_anchor={anchor}: generator paths ({len(traj) - 1} it, dot = seed) over the "
                     "morphed states;\nfilled: final cells of TX, LA, OK", fontsize=8)
        ax.set_aspect("equal")
        ax.axis("off")
    traj, ratio, _ = runs[0.0]
    ax1 = fig.add_subplot(grid[0, 2])
    ax2 = fig.add_subplot(grid[1, 2])
    for s, i in idx.items():
        ax1.plot(np.linalg.norm(traj[1:, i] - traj[0, i], axis=1) / 1e3, color=colors[s], lw=2, label=s)
        ax2.plot(ratio[:, i], color=colors[s], lw=2, label=s)
    ax1.set(ylabel="generator distance from its seed (km)", title="generator_anchor=0", xlabel="iteration")
    ax2.set(ylabel="raster cell area / target", xlabel="iteration")
    ax2.axhline(1.0, color="#999999", lw=0.8)
    for ax in (ax1, ax2):
        ax.legend(frameon=False, fontsize=8)
        ax.grid(alpha=0.3)
    fig.savefig(HERE / filename, dpi=100, bbox_inches="tight")
    plt.close(fig)
    for anchor, (traj, ratio, cells) in runs.items():
        for s, i in idx.items():
            d = np.linalg.norm(traj[1:, i] - traj[0, i], axis=1) / 1e3
            print(json.dumps({"table": "trace", "anchor": anchor, "state": s, "iterations": len(traj) - 1,
                              "dist_km_at_it_1_3_10_20_end": [round(float(d[j]), 0) for j in (0, 2, 9, 19, len(d) - 1)],
                              "area_ratio_at_it_1_3_10_20": [round(float(ratio[j, i]), 2) for j in (0, 2, 9, 19)],
                              "max_dist_km": round(float(d.max()), 0)}), flush=True)


def sweep(name, gdf, col, morphed, anchors):
    w = gdf[col].to_numpy(float)
    regions = np.asarray(morphed.geometry, dtype=object)
    r0 = np.sqrt(shapely.union_all(regions).area / len(gdf))
    tx = np.flatnonzero(gdf["State Abbreviation"].to_numpy() == "TX")
    for anchor in anchors:
        t = time.perf_counter()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = vor.create_voronoi_cartogram(morphed, weights=w, backend=vor.RasterBackend(resolution=256, generator_anchor=anchor),
                                             options=vor.VoronoiOptions(n_iter=300, area_cv_tol=0.05))
        dt = time.perf_counter() - t
        cells = np.asarray(r.cells, dtype=object)
        a = shapely.area(cells)
        d = np.linalg.norm(centroids(cells) - centroids(regions), axis=1) / r0
        own = shapely.area(shapely.intersection(cells, regions)) / shapely.area(regions)
        lag = np.linalg.norm(r.positions - centroids(cells), axis=1) / np.sqrt(a / np.pi)
        split = sum(1 for c in cells if c.geom_type == "MultiPolygon" and sorted(g.area for g in c.geoms)[-2] > 0.01 * c.area)
        # Texas: the state, or the union of its districts.
        tx_cell, tx_reg = shapely.union_all(cells[tx]), shapely.union_all(regions[tx])
        print(json.dumps({"table": "sweep", "dataset": name, "anchor": anchor, "it": r.metrics["n_iterations"], "time_s": round(dt, 2),
                          "mean_err_pct": round(r.metrics["mean_area_error_pct"], 4), "max_err_pct": round(r.metrics["max_area_error_pct"], 3),
                          "offset_med_R": round(float(np.median(d)), 3), "offset_max_R": round(float(d.max()), 3),
                          "own_mean": round(float(own.mean()), 3), "own_min": round(float(own.min()), 3),
                          "TX_offset_R": round(float(np.hypot(tx_cell.centroid.x - tx_reg.centroid.x, tx_cell.centroid.y - tx_reg.centroid.y) / r0), 3),
                          "TX_own": round(float(tx_cell.intersection(tx_reg).area / tx_reg.area), 3),
                          "lag_med": round(float(np.median(lag)), 3), "lag_max": round(float(lag.max()), 3),
                          "compact": round(float(np.mean(4 * np.pi * a / shapely.length(cells) ** 2)), 3), "split": split}), flush=True)


def plot_tx(panels, filename):
    """Rows: datasets; columns: flow cartogram, (c), (e); Texas (or its districts) in orange."""
    fig, axes = plt.subplots(len(panels), 3, figsize=(18, 4.8 * len(panels)))
    for row, (name, gdf, morphed, res) in enumerate(panels):
        is_tx = gdf["State Abbreviation"].to_numpy() == "TX"
        x = centroids(gdf.geometry)[:, 0]
        base = plt.get_cmap("Greys")(0.25 + 0.45 * (x - x.min()) / np.ptp(x))
        colors = [TX_COLOR if t else base[i] for i, t in enumerate(is_tx)]
        for k, (title, geoms) in enumerate((("flow cartogram (morphed regions)", list(morphed.geometry)),
                                            (VARIANTS["c"], res["c"]["cells"]), (VARIANTS["e"], res["e"]["cells"]))):
            ax = axes[row, k]
            fill(ax, geoms, colors, lw=0.2 if len(geoms) > 100 else 0.4)
            if k:
                r = res["ce"[k - 1]]
                title += (f"\noffset vs flow {r['d_flow_med']:.2f} R (med), own region {r['own_mean']:.2f} (mean), "
                          f"compactness {r['compact']:.2f}")
            ax.set_title(f"{name}: {title}", fontsize=8)
            ax.set_aspect("equal")
            ax.axis("off")
    fig.savefig(HERE / filename, dpi=100, bbox_inches="tight")
    plt.close(fig)


def main():
    us = examples.load_us_census(population=True)
    us_log = us.copy()
    us_log["w"] = np.exp(np.random.default_rng(1).normal(0, 1.5, len(us)))
    districts = examples.load_us_census(population=True, level="congressional_district")
    panels = []
    for name, gdf, col, fname, anchors in (
        ("states, population", us, "Population (Millions)", "premorph_states.png", (0.0, 0.25, 0.5, 0.75, 1.0)),
        ("states, lognormal sigma 1.5", us_log, "w", "premorph_lognormal.png", (0.0, 0.25, 0.5, 1.0)),
        ("districts, population", districts, "Population", "premorph_districts.png", (0.0, 0.25, 0.5, 1.0)),
    ):
        res, morphed, t_morph, morph_status = run(gdf, col)
        plot_variants(res, f"{name} (flow morph {t_morph:.1f} s)", fname)
        print_rows(name, res, t_morph, morph_status)
        if name.startswith("states, population"):
            print_states(res, list(gdf["State Abbreviation"]))
            plot_arrows(res, gdf, "premorph_tx_arrows.png")
            plot_trace(morphed, gdf, col, "premorph_tx_trace.png")
        sweep(name, gdf, col, morphed, anchors)
        panels.append((name, gdf, morphed, res))
    plot_tx(panels, "premorph_tx.png")


if __name__ == "__main__":
    main()
