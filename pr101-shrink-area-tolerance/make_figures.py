# Produces area_error_per_state.png, map.png and tol_sweep.png next to this file:
# every US state shrunk to its population density relative to the densest state
# (DC excluded), with shrink() from main and from the current checkout. Run from
# a carto-flow checkout: `uv run python make_figures.py`.
import importlib.util
import statistics
import subprocess
import tempfile
import time
from pathlib import Path

import geopandas as gpd
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

import carto_flow.data as data
from carto_flow.proportional_cartogram import shrink as shrink_fix

HERE = Path(__file__).resolve().parent
SRC = "src/carto_flow/proportional_cartogram/shrinking.py"

# shrink() as on main, loaded from the repository history
source = subprocess.check_output(["git", "show", f"main:{SRC}"], text=True)
path = Path(tempfile.mkdtemp()) / "shrink_main.py"
path.write_text(source)
spec = importlib.util.spec_from_file_location("shrink_main", path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
shrink_main = mod.shrink

g = data.load_us_census(population=True)
g = g[g["State Abbreviation"] != "DC"].set_index("State Abbreviation")
dens = g["Population"] / g.geometry.area
frac = dens / dens.max()  # the densest state keeps fraction 1


def run(fn, **kw):
    """Shrink every state; return (area error per state, cores, seconds)."""
    t = time.perf_counter()
    cores = {k: (g.geometry[k] if f >= 1 else fn(g.geometry[k], f, **kw)[0]) for k, f in frac.items()}
    secs = time.perf_counter() - t
    err = {k: cores[k].area / (frac[k] * g.geometry[k].area) - 1 for k in cores}
    return err, cores, secs


def median_time(fn, **kw):
    return statistics.median(run(fn, **kw)[2] for _ in range(3))


err_b, cores_b, _ = run(shrink_main)
err_a, cores_a, _ = run(shrink_fix)
order = sorted(frac.index, key=frac.get)

# area error per state
fig, ax = plt.subplots(1, 2, figsize=(14, 9), sharex=True, sharey=True)
y = np.arange(len(order))
for a, err, name, c in [(ax[0], err_b, "main", "#c0504d"), (ax[1], err_a, "fix (tol=0.01)", "#4f81bd")]:
    a.barh(y, [err[k] * 100 for k in order], color=c)
    a.set_yticks(y)
    a.set_yticklabels([f"{k} ({frac[k]:.1%})" for k in order], fontsize=7)
    a.axvline(0, color="k", lw=0.5)
    a.set_title(f"{name}: area error of shrunken core (%)")
    a.set_xlabel("core area / target area - 1 (%)")
plt.tight_layout()
plt.savefig(HERE / "area_error_per_state.png", dpi=110)
plt.close()

# map
fig, ax = plt.subplots(1, 2, figsize=(16, 7))
for a, err, cores, name in [(ax[0], err_b, cores_b, "main"), (ax[1], err_a, cores_a, "fix (tol=0.01)")]:
    gpd.GeoSeries(g.geometry).plot(ax=a, color="#e5e5e5", edgecolor="#999", lw=0.4)
    gpd.GeoSeries([cores[k] for k in g.index]).plot(ax=a, color="#4f81bd", edgecolor="none")
    a.set_title(f"{name}: max |error| {max(map(abs, err.values())):.2%}")
    a.axis("off")
plt.tight_layout()
plt.savefig(HERE / "map.png", dpi=110)
plt.close()

# tol sweep
rows = [("main", err_b, median_time(shrink_main))]
for tol in (0.05, 0.01, 1e-3, 1e-4):
    rows.append((f"fix tol={tol:g}", run(shrink_fix, tol=tol)[0], median_time(shrink_fix, tol=tol)))
print("| version | max error | mean error | time (s) |\n|---|---|---|---|")
for name, e, t in rows:
    v = np.abs(list(e.values()))
    print(f"| {name} | {v.max():.3%} | {v.mean():.3%} | {t:.1f} |")
for lim in (1e-3, 1e-2):
    print(f"states over {lim:.1%} error: main", sum(abs(v) > lim for v in err_b.values()), "fix", sum(abs(v) > lim for v in err_a.values()))
for k in ["SD", "MT", "ID", "NM", "OH", "PA"]:
    print(k, f"{frac[k]:.2%} main {err_b[k]:+.3%} fix {err_a[k]:+.3%}")

fig, ax = plt.subplots(1, 2, figsize=(11, 4))
names = [r[0] for r in rows]
ax[0].bar(names, [np.abs(list(r[1].values())).max() * 100 for r in rows], color="#4f81bd")
ax[0].set_yscale("log")
ax[0].set_ylabel("max |area error| (%)")
ax[1].bar(names, [r[2] for r in rows], color="#999")
ax[1].set_ylabel("time for 50 states (s, median of 3)")
for a in ax:
    a.tick_params(axis="x", rotation=30)
plt.tight_layout()
plt.savefig(HERE / "tol_sweep.png", dpi=110)
