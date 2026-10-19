"""Continue the finest level of the county ladder past its stall and follow the regions that were above 10 % at the stall."""
import warnings, sys, json; warnings.filterwarnings("ignore")
import numpy as np, shapely, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import carto_flow.data as data
from carto_flow.flow_cartogram import MorphOptions, CartogramWorkflow
out = sys.argv[1]
g = data.load_us_census(level="county", max_segment_length=1000).reset_index(drop=True)
v = g["Population"].to_numpy(float); gdf = g[["geometry"]].assign(v=v)
w = CartogramWorkflow(gdf, "v", validate=False)
w.morph_multiresolution(min_resolution="auto", levels="auto", options=MorphOptions(area_scale=1e-6, n_iter=1000, show_progress=False))
c = w[-1]; stall_it = c.niterations

def err(geoms):
    o = np.array(geoms, dtype=object); a = shapely.area(o); T = v / v.sum() * a.sum()
    return abs(a - T) / T * 100, int((~shapely.is_valid(o)).sum())

e0, _ = err(c.get_geometry()); bad0 = e0 > 10
c2 = w.morph(options=MorphOptions(area_scale=1e-6, grid=2048, n_iter=1500, stall_patience=None, snapshot_every=50, show_progress=False))
rows = []
for sn in c2.snapshots.snapshots:
    e, inv = err(sn.geometry)
    rows.append(dict(it=sn.iteration, mean=e.mean(), median=float(np.median(e)), p95=float(np.percentile(e, 95)), max=e.max(),
                     n10=int((e > 10).sum()), lag_median=float(np.median(e[bad0])), lag_mean=float(e[bad0].mean()), invalid=inv))
json.dump(dict(stall_it=stall_it, n_lag=int(bad0.sum()), rows=rows), open(f"{out}/continue.json", "w"))
INK, MUTED, GRID, BLUE, RED = "#1f2933", "#6b7785", "#e4e7eb", "#2a62a3", "#c0392b"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "text.color": INK, "xtick.color": MUTED,
                     "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True})
it = [r["it"] for r in rows]
fig, axs = plt.subplots(1, 2, figsize=(11, 4.2))
ax = axs[0]
ax.plot(it, [r["lag_median"] for r in rows], color=BLUE, lw=2); ax.set_yscale("log")
ax.set_ylabel(f"median error, the {int(bad0.sum())} counties above 10 % (%)"); ax.set_xlabel("iterations after the stall (finest level)")
ax.set_title("the lagging counties keep improving", loc="left", fontsize=10)
ax = axs[1]
ax.plot(it, [r["mean"] for r in rows], color=RED, lw=2, label="mean error, all counties")
ax.plot(it, [r["median"] for r in rows], color=MUTED, lw=2, label="median error, all counties")
ax.set_yscale("log"); ax.set_ylabel("error (%)"); ax.set_xlabel("iterations after the stall (finest level)")
ax.set_title("while the mean (the stall criterion) gets worse", loc="left", fontsize=10); ax.legend(frameon=False, loc="lower right")
fig.tight_layout(); fig.savefig(f"{out}/fig1_past_stall.png", dpi=150)
