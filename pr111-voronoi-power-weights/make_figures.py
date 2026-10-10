# Produces weighted_states.png, weighted_detail.png, weighted_extremes.png, weighted_districts.png,
# elastic_displacement.png and elastic_area.png and prints the metrics table: weighted Voronoi cartograms (population
# weights, plus lognormal weights spanning ~1400x and ~15600x) computed with the code before the
# change (BEFORE_REF), with the branch before the elastic-boundary fix (MID_REF, displacement figure
# only), both exported with `git archive`, and with the current checkout. Cells are colored by
# area / target; the displacement figure shows where the elastic boundary moved out (red) and in (blue);
# elastic_area.png traces the boundary area over 300 forced iterations, adding the particle version
# without mass anchoring (PARTICLE_REF).
# Run from a carto-flow checkout: `uv run python make_figures.py` (BEFORE_REF / MID_REF to override).
import json
import os
import pickle
import subprocess
import sys
import tempfile
import time
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
BEFORE_REF = os.environ.get("BEFORE_REF", "0124245")
MID_REF = os.environ.get("MID_REF", "a1bf32e")
PARTICLE_REF = os.environ.get("PARTICLE_REF", "209f2f8")
NE = ["NY", "NJ", "PA", "MA", "CT", "RI"]
COL = "Population (Millions)"

CASES = {
    "fixed": "fixed boundary",
    "elastic": "ElasticBoundary(0.05)",
    "circle": "circular boundary",
    "lognormal_1.5": "lognormal weights, sigma 1.5",
    "lognormal_2": "lognormal weights, sigma 2",
    "districts": "432 districts, population",
    "elastic_gallery": "ElasticBoundary(0.02) + adjacency_spring 0.2, 100 it",
}


def compute(out_path):
    """Run every case with the carto_flow on sys.path and pickle cells and metrics."""
    import numpy as np
    import shapely

    import carto_flow.data as examples
    import carto_flow.voronoi_cartogram as vor

    us = examples.load_us_census(population=True)
    districts = examples.load_us_census(population=True, level="congressional_district")
    opts = vor.VoronoiOptions(n_iter=300, area_cv_tol=0.05)
    raster = vor.RasterBackend
    runs = {
        "fixed": (us, us[COL].to_numpy(float), {"backend": raster(resolution=256)}),
        "elastic": (us, us[COL].to_numpy(float), {"backend": raster(resolution=256, boundary=vor.ElasticBoundary(0.05))}),
        "circle": (us, us[COL].to_numpy(float), {"backend": raster(resolution=256), "boundary": "circle"}),
        "lognormal_1.5": (us, np.exp(np.random.default_rng(1).normal(0, 1.5, len(us))), {"backend": raster(resolution=256)}),
        "lognormal_2": (us, np.exp(np.random.default_rng(1).normal(0, 2.0, len(us))), {"backend": raster(resolution=256)}),
        "districts": (districts, districts["Population"].to_numpy(float), {"backend": raster(resolution=256)}),
        "elastic_gallery": (us, us[COL].to_numpy(float), {
            "backend": raster(resolution=256, boundary=vor.ElasticBoundary(0.02), adjacency_spring=0.2),
            "options": vor.VoronoiOptions(n_iter=100)}),
    }
    out = {}
    for name, (gdf, w, kw) in runs.items():
        t = time.time()
        kw = dict(kw)
        options = kw.pop("options", opts)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = vor.create_voronoi_cartogram(gdf, weights=w, options=options, **kw)
        elapsed = time.time() - t
        cells = np.asarray(r.cells, dtype=object)
        a = shapely.area(cells)
        ratio = a / (w / w.sum() * a.sum())
        disp = {}
        if name.startswith("elastic"):
            from scipy.stats import spearmanr

            geoms = np.asarray(list(gdf.geometry), dtype=object)
            orig = r._field._original_boundary
            final = r._field._current_boundary
            gained, lost = final.difference(orig), orig.difference(final)
            near = shapely.buffer(geoms, 150_000)
            outward = shapely.area(shapely.intersection(near, gained)) - shapely.area(shapely.intersection(near, lost))
            density = (w / w.sum()) / (shapely.area(geoms) / shapely.area(geoms).sum())
            coastal = shapely.intersects(shapely.boundary(orig), shapely.buffer(geoms, 1000))
            ne = [list(gdf["State Abbreviation"]).index(s) for s in NE]
            ne_near = shapely.union_all(near[ne])
            disp = {
                "original": shapely.to_wkb(orig),
                "gained": shapely.to_wkb(gained),
                "lost": shapely.to_wkb(lost),
                "ne": shapely.to_wkb(shapely.union_all(geoms[ne])),
                "rho_disp": float(spearmanr(np.log(density[coastal]), outward[coastal]).correlation),
                "ne_outward_km2": float(
                    (shapely.area(shapely.intersection(ne_near, gained)) - shapely.area(shapely.intersection(ne_near, lost)))
                    / 1e6
                ),
            }
        out[name] = {
            **disp,
            "cells": shapely.to_wkb(cells),
            "points": r.positions,
            "boundary": shapely.to_wkb(r._field._current_boundary),
            "ratio": ratio,
            "mean": float(np.mean(np.abs(ratio - 1)) * 100),
            "max": float(np.max(np.abs(ratio - 1)) * 100),
            "k": float(np.polyfit(np.log(w), np.log(np.maximum(a, 1.0)), 1)[0]),
            "iterations": r.metrics["n_iterations"],
            "converged": r.metrics["converged"],
            "seconds": elapsed,
            "range": float(w.max() / w.min()),
        }
    with open(out_path, "wb") as f:
        pickle.dump(out, f)


def trace(out_path):
    """Boundary area (relative to the original) per iteration over 300 forced elastic iterations."""
    import numpy as np

    import carto_flow.data as examples
    import carto_flow.voronoi_cartogram as vor
    from carto_flow.voronoi_cartogram.fields._raster import RasterField

    areas = []
    deform = RasterField._deform_boundary

    def recording(self):
        deform(self)
        areas.append(self._current_boundary.area / self._original_boundary.area)

    RasterField._deform_boundary = recording
    us = examples.load_us_census(population=True)
    configs = {
        "elastic": vor.RasterBackend(resolution=256, boundary=vor.ElasticBoundary(0.05)),
        "elastic_gallery": vor.RasterBackend(resolution=256, boundary=vor.ElasticBoundary(0.02), adjacency_spring=0.2),
    }
    out = {}
    for name, backend in configs.items():
        areas.clear()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            vor.create_voronoi_cartogram(us, weights=us[COL].to_numpy(float), backend=backend,
                                         options=vor.VoronoiOptions(n_iter=300))
        out[name] = np.array(areas)
    with open(out_path, "wb") as f:
        pickle.dump(out, f)


def export(repo, ref, tmp, name):
    dest = Path(tmp) / name
    dest.mkdir()
    archive = subprocess.run(["git", "-C", str(repo), "archive", ref, "src"], check=True, capture_output=True)
    subprocess.run(["tar", "-x", "-C", str(dest)], input=archive.stdout, check=True)
    return str(dest / "src")


def run_version(label, tmp, pythonpath=None, mode="--compute"):
    path = Path(tmp) / f"{label}{mode}.pkl"
    env = dict(os.environ, MPLBACKEND="Agg")
    if pythonpath:
        env["PYTHONPATH"] = pythonpath
    subprocess.run([sys.executable, __file__, mode, str(path)], check=True, env=env)
    with open(path, "rb") as f:
        return pickle.load(f)


def plot(before, after, names, filename, title, zoom=None):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    import shapely
    from matplotlib.colors import Normalize

    norm = Normalize(-2, 2)
    cmap = plt.get_cmap("RdBu_r")
    fig, axes = plt.subplots(len(names), 2, figsize=(13, 4.3 * len(names)), squeeze=False)
    for row, name in enumerate(names):
        for col, (label, res) in enumerate((("before", before[name]), ("after", after[name]))):
            ax = axes[row, col]
            cells = shapely.from_wkb(res["cells"])
            colors = cmap(norm(np.log2(np.clip(res["ratio"], 1e-3, None))))
            for cell, color in zip(cells, colors):
                for part in getattr(cell, "geoms", [cell]):
                    if part.geom_type != "Polygon" or part.is_empty:
                        continue
                    x, y = part.exterior.xy
                    ax.fill(x, y, facecolor=color, edgecolor="black", linewidth=0.35)
            bx = shapely.from_wkb(res["boundary"])
            for part in getattr(bx, "geoms", [bx]):
                ax.plot(*part.exterior.xy, color="0.4", linewidth=0.4)
            ax.plot(res["points"][:, 0], res["points"][:, 1], ".", color="black", markersize=1.5)
            ax.set_title(
                f"{label}: {CASES[name]}\nmean {res['mean']:.2f} %, max {res['max']:.1f} %, k {res['k']:.2f}, "
                f"{res['iterations']} it, {res['seconds']:.1f} s",
                fontsize=9,
            )
            ax.set_aspect("equal")
            ax.axis("off")
            if zoom is not None:
                ax.set_xlim(zoom[0], zoom[1])
                ax.set_ylim(zoom[2], zoom[3])
    sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
    cbar = fig.colorbar(sm, ax=axes, shrink=0.5, location="bottom", pad=0.02)
    cbar.set_ticks([-2, -1, 0, 1, 2])
    cbar.set_ticklabels(["1/4", "1/2", "1", "2", "4"])
    cbar.set_label("cell area / target area")
    fig.suptitle(title, fontsize=11)
    fig.savefig(HERE / filename, dpi=110, bbox_inches="tight")
    plt.close(fig)


def plot_displacement(before, mid, after):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import shapely

    def fill(ax, geom, **kw):
        for part in getattr(geom, "geoms", [geom]):
            if part.geom_type == "Polygon" and not part.is_empty:
                ax.fill(*part.exterior.xy, **kw)

    names = ["elastic", "elastic_gallery"]
    versions = (("main", before), ("branch before fix", mid), ("after fix", after))
    fig, axes = plt.subplots(len(names), 3, figsize=(19, 5.2 * len(names)), squeeze=False)
    for row, name in enumerate(names):
        for col, (label, res) in enumerate(versions):
            ax = axes[row, col]
            r = res[name]
            fill(ax, shapely.from_wkb(r["original"]), facecolor="0.92", edgecolor="0.5", linewidth=0.3)
            fill(ax, shapely.from_wkb(r["ne"]), facecolor="0.75", edgecolor="0.3", linewidth=0.5)
            fill(ax, shapely.from_wkb(r["gained"]), facecolor="tab:red", alpha=0.8, linewidth=0)
            fill(ax, shapely.from_wkb(r["lost"]), facecolor="tab:blue", alpha=0.8, linewidth=0)
            ax.set_title(
                f"{label}: {CASES[name]}\nrank corr(log density, outward move) {r['rho_disp']:.2f}\n"
                f"NE outward {r['ne_outward_km2'] / 1e3:.0f}k km2, mean area error {r['mean']:.2f} %",
                fontsize=8,
            )
            ax.set_aspect("equal")
            ax.axis("off")
    fig.suptitle("Elastic boundary: moved outward (red) and inward (blue); NE states (NY, NJ, PA, MA, CT, RI) in dark gray",
                 fontsize=11)
    fig.savefig(HERE / "elastic_displacement.png", dpi=110, bbox_inches="tight")
    plt.close(fig)


def plot_area(traces):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.2), sharey=True)
    for ax, name in zip(axes, ("elastic", "elastic_gallery"), strict=True):
        for label, tr in traces.items():
            ax.plot(100 * (tr[name] - 1), label=label, linewidth=1.2)
        ax.axhline(0, color="0.5", linewidth=0.6)
        ax.set(title=CASES[name], xlabel="iteration", ylabel="boundary area change (%)")
        ax.set_ylim(-6, 3)
    axes[0].legend(fontsize=8)
    fig.suptitle("Elastic boundary area over 300 forced iterations (stopping rules off), 49 states, population weights",
                 fontsize=10)
    fig.savefig(HERE / "elastic_area.png", dpi=110, bbox_inches="tight")
    plt.close(fig)


def main():
    repo = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "before_src"
        src.mkdir()
        archive = subprocess.run(["git", "-C", str(repo), "archive", BEFORE_REF, "src"], check=True, capture_output=True)
        subprocess.run(["tar", "-x", "-C", str(src)], input=archive.stdout, check=True)
        before = run_version("before", tmp, pythonpath=str(src / "src"))
        mid_src = Path(tmp) / "mid_src"
        mid_src.mkdir()
        archive = subprocess.run(["git", "-C", str(repo), "archive", MID_REF, "src"], check=True, capture_output=True)
        subprocess.run(["tar", "-x", "-C", str(mid_src)], input=archive.stdout, check=True)
        mid = run_version("mid", tmp, pythonpath=str(mid_src / "src"))
        after = run_version("after", tmp)
        particle_src = export(repo, PARTICLE_REF, tmp, "particle_src")
        traces = {
            "main": run_version("before", tmp, pythonpath=str(src / "src"), mode="--trace"),
            "branch before elastic fix": run_version("mid", tmp, pythonpath=str(mid_src / "src"), mode="--trace"),
            "particles without mass anchoring": run_version("particle", tmp, pythonpath=particle_src, mode="--trace"),
            "after": run_version("after", tmp, mode="--trace"),
        }
    plot_displacement(before, mid, after)
    plot_area(traces)

    plot(before, after, ["fixed", "elastic", "circle"], "weighted_states.png",
         "US states, population weights: weighted gallery configurations")
    plot(before, after, ["fixed"], "weighted_detail.png", "Northeast detail, fixed boundary",
         zoom=(1.2e6, 2.3e6, -0.1e6, 0.9e6))
    plot(before, after, ["lognormal_1.5", "lognormal_2"], "weighted_extremes.png",
         "US states, lognormal weights (ranges ~1400x and ~15600x)")
    plot(before, after, ["districts"], "weighted_districts.png", "Congressional districts, population weights")

    rows = []
    for name in ("elastic", "elastic_gallery"):
        print(json.dumps({"case": CASES[name], **{
            label: {"rho_disp": round(v[name]["rho_disp"], 3), "ne_outward_km2": round(v[name]["ne_outward_km2"]),
                    "mean": round(v[name]["mean"], 3), "iterations": v[name]["iterations"],
                    "seconds": round(v[name]["seconds"], 1)}
            for label, v in (("before", before), ("branch_before_fix", mid), ("after", after))}}))
    for name in CASES:
        b, a = before[name], after[name]
        rows.append({
            "case": CASES[name], "range": round(a["range"]),
            "before": {k: round(b[k], 3) if isinstance(b[k], float) else b[k] for k in ("mean", "max", "k", "iterations", "seconds", "converged")},
            "after": {k: round(a[k], 3) if isinstance(a[k], float) else a[k] for k in ("mean", "max", "k", "iterations", "seconds", "converged")},
        })
    for row in rows:
        print(json.dumps(row))


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--compute":
        compute(sys.argv[2])
    elif len(sys.argv) == 3 and sys.argv[1] == "--trace":
        trace(sys.argv[2])
    else:
        main()
