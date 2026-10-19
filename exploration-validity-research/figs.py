import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, shapely, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams.update({"figure.facecolor": "white", "axes.facecolor": "white", "axes.edgecolor": "#888", "axes.grid": True, "grid.color": "#e5e5e5", "font.size": 9})
d = os.path.dirname(os.path.abspath(__file__)) + "/out/"
# fig 1: invalid polygons per run
rows = [("baseline dt 0.20", 57), ("baseline dt 0.15", 62), ("baseline dt 0.18", 90), ("baseline dt 0.22", 116), ("baseline dt 0.25", 76), ("baseline dt 0.05", 105),
        ("RK2 advection", 60), ("RK4 advection", 53), ("Euler 4 substeps", 65), ("value floor 0.05 x median", 63), ("value floor 0.2 x median", 50),
        ("quadtree 2^-6, safe pruning", 0), ("validated windows, every 10: dt 0.20", 0), ("... dt 0.15", 0), ("... dt 0.18", 0), ("... dt 0.22", 0), ("... dt 0.25", 0)]
fig, ax = plt.subplots(figsize=(7.5, 5))
cols = ["#777"] * 6 + ["#c77"] * 5 + ["#58a"] + ["#3a7"] * 5
ax.barh(range(len(rows))[::-1], [r[1] for r in rows], color=cols)
ax.set_yticks(range(len(rows))[::-1]); ax.set_yticklabels([r[0] for r in rows])
ax.set_xlabel("invalid output polygons of 3,108 counties (1 km input)")
fig.tight_layout(); fig.savefig(d + "../fig1_invalid_counts.png", dpi=130); plt.close(fig)

# fig 2: one county, baseline vs validated windows
b = shapely.from_wkb(np.load(d + "baseline_county_wkb.npy", allow_pickle=True)); v = shapely.from_wkb(np.load(d + "bf_county_wkb.npy", allow_pickle=True))
inv = np.flatnonzero(~shapely.is_valid(b))
# the invalid county with the most vertices in the zoom: choose by smallest area ratio to a neighbor... take the one with the largest invalid-looking extent
def pt(g):
    r = shapely.is_valid_reason(g)
    try:
        x, y = r.split("[")[1].rstrip("]").split(); return float(x), float(y)
    except Exception: return None
cands = [i for i in inv if pt(b[i])]
i = cands[int(len(cands) // 3)]
x, y = pt(b[i])
fig, axs = plt.subplots(1, 4, figsize=(13, 3.4))
def draw(ax, g, t):
    for part in shapely.get_parts(g):
        xs, ys = part.exterior.xy; ax.plot(xs, ys, "-o", lw=0.8, ms=1.5, color="#357"); ax.fill(xs, ys, alpha=0.15, color="#357")
    ax.set_title(t, fontsize=8); ax.set_aspect("equal"); ax.ticklabel_format(style="plain"); ax.tick_params(labelsize=6)
draw(axs[0], b[i], "baseline (invalid), full"); draw(axs[1], b[i], "baseline, zoom at the self-intersection")
axs[1].set_xlim(x - 6000, x + 6000); axs[1].set_ylim(y - 6000, y + 6000)
draw(axs[2], v[i], "validated windows, full")
mx = shapely.get_coordinates(v[i])[:, 0].min(); my = shapely.get_coordinates(v[i])[shapely.get_coordinates(v[i])[:, 0].argmin(), 1]
draw(axs[3], v[i], "validated windows, zoom at the thin tail"); axs[3].set_xlim(mx - 1000, mx + 12000); axs[3].set_ylim(my - 6000, my + 6000)
fig.suptitle(f"county {i} of two different runs (they diverge): shoelace area baseline {shapely.area(b[i])/1e6:.1f} km2, validated {shapely.area(v[i])/1e6:.1f} km2", fontsize=9)
fig.tight_layout(); fig.savefig(d + "../fig2_example.png", dpi=130); plt.close(fig)
print("example county", i)
