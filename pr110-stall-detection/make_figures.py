# Produces the before/after figures and the table of the stall-detection report:
#   trajectories.png  convergence score per iteration with the stop marker, three
#                     strong-anisotropy configurations (main vs fix, bundled US states)
#   best_vs_last.png  maps and score trajectory of two runs that do not converge:
#                     main returns the final iterate, the fix returns the best one
#   cycles.png        per-cycle minima of the mean and max components with the stop of
#                     the old and the new rule on two runs
#   refresh_on_rise.png  score of two runs with refresh_on_rise off and on
# and prints the tables: status/iterations/errors, recompute_every sweep, presets,
# multiresolution per level (US states, congressional districts), refresh_on_rise off vs on. "Before" is the algorithm module of
# `main`, loaded from the repository history; the fix is the working tree.
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

import carto_flow.data as data
from carto_flow.flow_cartogram import MorphOptions, morph_gdf
from carto_flow.flow_cartogram.anisotropy import DirectionalTensor

HERE = Path(__file__).resolve().parent
BEFORE_REF = "main"

# algorithm.py as on main, with its relative imports made absolute
source = subprocess.check_output(["git", "show", f"{BEFORE_REF}:src/carto_flow/flow_cartogram/algorithm.py"], text=True)
source = source.replace("from ..geo_utils", "from carto_flow.geo_utils").replace("from .", "from carto_flow.flow_cartogram.")
path = Path(tempfile.mkdtemp()) / "algorithm_main.py"
path.write_text(source)
spec = importlib.util.spec_from_file_location("algorithm_main", path)
mod = importlib.util.module_from_spec(spec)
sys.modules["algorithm_main"] = mod
spec.loader.exec_module(mod)
morph_main = mod.morph_geometries

g = data.load_us_census(population=True).reset_index(drop=True)  # 49 states incl. DC
VALUES = g["Population"].to_numpy()


def run_before(options):
    """Run main's algorithm; main's default stall_patience is 5."""
    return morph_main(list(g.geometry), VALUES, options=options)


def run_after(options):
    """Run the fix with the fixed refresh schedule (refresh_on_rise is compared separately)."""
    return morph_gdf(g, "Population", options=options.copy_with(refresh_on_rise=None))


def with_main_algorithm(fn):
    """Call fn() with the workflow using main's morph_geometries."""
    import carto_flow.flow_cartogram.workflow as wfmod

    original = wfmod.morph_geometries
    wfmod.morph_geometries = morph_main
    try:
        return fn()
    finally:
        wfmod.morph_geometries = original


def score(result, options):
    c = result.convergence
    return np.maximum(c.mean_log_errors / np.log2(1 + options.mean_tol), c.max_log_errors / np.log2(1 + options.max_tol))


def final_errors(result):
    e = result.latest.errors
    return e.mean_error_pct, e.max_error_pct


BASE = MorphOptions.preset_balanced().copy_with(area_scale=1e-6, n_iter=400, show_progress=False)
CONFIGS = {
    "horizontal  DirectionalTensor(theta=0, Dpar=4, Dperp=0.3)": DirectionalTensor(theta=0, Dpar=4, Dperp=0.3),
    "tangential  DirectionalTensor.tangential(Dpar=4, Dperp=0.3)": DirectionalTensor.tangential(Dpar=4, Dperp=0.3),
    "tilted  DirectionalTensor(theta=pi/6, Dpar=4, Dperp=0.3)": DirectionalTensor(theta=np.pi / 6, Dpar=4, Dperp=0.3),
}

rows = []


def add_row(name, before, after):
    bm, bx = final_errors(before)
    am, ax = final_errors(after)
    rows.append(
        f"| {name} | {before.status} / {before.niterations} | {bm:.2f} / {bx:.1f} | "
        f"{after.status} / {after.niterations} (best {after.best_iteration}, {after.stop_reason}) | {am:.2f} / {ax:.1f} |"
    )


# --- Figure 1: strong anisotropy -----------------------------------------------------
fig, axes = plt.subplots(1, 3, figsize=(15, 4.2), sharey=True)
for ax, (name, mod_) in zip(axes, CONFIGS.items(), strict=True):
    opt_b = BASE.copy_with(anisotropy=mod_, stall_patience=5)
    opt_a = BASE.copy_with(anisotropy=mod_)
    before, after = run_before(opt_b), run_after(opt_a)
    add_row(name.split("  ")[0], before, after)
    for res, opt, color, label in ((before, opt_b, "#c0392b", "main"), (after, opt_a, "#1f77b4", "fix")):
        s = score(res, opt)
        ax.plot(res.convergence.iterations, s, color=color, lw=4.5 if label == "main" else 1.6, label=f"{label}: {res.status}, {res.niterations} it.")
        ax.plot(res.niterations, s[-1], "o", color=color, ms=8)
    ax.axhline(1, color="k", lw=0.8, ls="--")
    ax.set_yscale("log")
    ax.set_title(name.split("  ")[0] + "\n" + name.split("  ")[1], fontsize=9)
    ax.set_xlabel("iteration")
    ax.legend(fontsize=8)
axes[0].set_ylabel("score (< 1 converged)")
fig.suptitle(
    "US states (49), preset_balanced, area_scale=1e-6, n_iter=400; score = max(mean/mean_tol, max/max_tol); dot = stop"
)
fig.tight_layout()
fig.savefig(HERE / "trajectories.png", dpi=130)
plt.close(fig)

# --- Baseline cases that must not change ---------------------------------------------
for name, opts in (
    ("default options", MorphOptions(show_progress=False)),
    ("grid_size=512", MorphOptions(show_progress=False, grid_size=512)),
):
    add_row(name, run_before(opts), run_after(opts))

# --- Figure 2: best vs last iterate of runs that do not converge ---------------------
CASES = {
    "tolerances 0.5% / 1%, n_iter=300": MorphOptions(show_progress=False, n_iter=300, mean_tol=0.005, max_tol=0.01),
    "dt=0.6, tolerances 0.1% / 0.2%, n_iter=60": MorphOptions(
        show_progress=False, n_iter=60, dt=0.6, mean_tol=0.001, max_tol=0.002, stall_patience=None
    ),
}
fig, axes = plt.subplots(len(CASES), 3, figsize=(15, 4.6 * len(CASES)), gridspec_kw={"width_ratios": [1, 1, 1.1]})
for r, (name, opts) in enumerate(CASES.items()):
    before = run_before(opts.copy_with(stall_patience=5) if opts.stall_patience is not None else opts)
    after = run_after(opts)
    add_row(name, before, after)
    plot = g.copy()
    plot_b = g.copy()
    plot_b.geometry = before.latest.geometry
    plot.geometry = after.latest.geometry
    for ax, gdf_, res, title in (
        (axes[r, 0], plot_b, before, f"main: final iterate ({before.niterations})"),
        (axes[r, 1], plot, after, f"fix: best iterate ({after.best_iteration})"),
    ):
        pct = res.latest.errors.errors_pct
        gdf_.assign(err=pct).plot(column="err", ax=ax, cmap="RdBu_r", vmin=-30, vmax=30, edgecolor="k", linewidth=0.3)
        ax.set_axis_off()
        e = res.latest.errors
        ax.set_title(f"{title}\nmean {e.mean_error_pct:.2f}%, max {e.max_error_pct:.1f}%", fontsize=9)
    ax = axes[r, 2]
    s = score(after, opts)
    ax.plot(after.convergence.iterations, s, color="#1f77b4")
    ax.plot(after.best_iteration, s[after.best_iteration - 1], "o", color="#2ca02c", ms=9, label=f"best {after.best_iteration}")
    ax.plot(after.niterations, s[-1], "s", color="#c0392b", ms=8, label=f"final {after.niterations}")
    ax.axhline(1, color="k", lw=0.8, ls="--")
    ax.set_yscale("log")
    ax.set_xlabel("iteration")
    ax.set_ylabel("score")
    ax.set_title(name, fontsize=9)
    ax.legend(fontsize=8)
fig.tight_layout()
fig.savefig(HERE / "best_vs_last.png", dpi=130)
plt.close(fig)

# --- Figure 3: per-cycle minima --------------------------------------------------------
from carto_flow.flow_cartogram.stall import cycle_length  # noqa: E402

HORIZONTAL = DirectionalTensor(theta=0, Dpar=4, Dperp=0.3)
CYCLE_CASES = {
    "horizontal anisotropy": BASE.copy_with(anisotropy=HORIZONTAL),
    "preset_balanced, dt=0.6": MorphOptions.preset_balanced().copy_with(dt=0.6, show_progress=False),
}
fig, axes = plt.subplots(1, 2, figsize=(14, 4.5))
for ax, (name, opts) in zip(axes, CYCLE_CASES.items(), strict=True):
    full = run_after(opts.copy_with(stall_patience=None))
    old = run_before(opts.copy_with(stall_patience=5))
    new = run_after(opts)
    c = full.convergence
    mean_r = c.mean_log_errors / np.log2(1 + opts.mean_tol)
    max_r = c.max_log_errors / np.log2(1 + opts.max_tol)
    cyc = cycle_length(opts.recompute_every)
    n = len(mean_r) // cyc
    xs = np.arange(1, n + 1) * cyc
    ax.plot(c.iterations, np.maximum(mean_r, max_r), color="0.75", lw=1, label="score per iteration")
    ax.plot(xs, mean_r[: n * cyc].reshape(n, cyc).min(axis=1), "o-", color="#1f77b4", ms=4, label="cycle min, mean ratio")
    ax.plot(xs, max_r[: n * cyc].reshape(n, cyc).min(axis=1), "s-", color="#ff7f0e", ms=4, label="cycle min, max ratio")
    ax.axvline(old.niterations, color="#c0392b", ls="--", label=f"old rule stops ({old.niterations}, {old.status})")
    ax.axvline(new.niterations, color="#2ca02c", ls=":", lw=2.5, label=f"new rule stops ({new.niterations}, {new.status})")
    ax.axhline(1, color="k", lw=0.8)
    ax.set_yscale("log")
    ax.set_xlabel("iteration")
    ax.set_title(name, fontsize=10)
    ax.legend(fontsize=7)
axes[0].set_ylabel("ratio to tolerance (< 1 converged)")
fig.tight_layout()
fig.savefig(HERE / "cycles.png", dpi=130)
plt.close(fig)

# --- recompute_every sweep and presets -------------------------------------------------
sweep = ["| recompute_every | main: status / iterations | fix: status / iterations |", "|---|---|---|"]
for re_ in (1, 2, 5, 10):
    opts = BASE.copy_with(anisotropy=HORIZONTAL, recompute_every=re_)
    b, a = run_before(opts.copy_with(stall_patience=5)), run_after(opts)
    sweep.append(f"| {re_} | {b.status} / {b.niterations} | {a.status} / {a.niterations} |")

presets = ["| options | main: status / iterations | fix: status / iterations |", "|---|---|---|"]
for name, opts in (
    ("preset_fast", MorphOptions.preset_fast()),
    ("preset_balanced", MorphOptions.preset_balanced()),
    ("preset_high_quality", MorphOptions.preset_high_quality()),
    ("preset_balanced, dt=0.6", MorphOptions.preset_balanced().copy_with(dt=0.6)),
):
    opts = opts.copy_with(show_progress=False)
    b, a = run_before(opts.copy_with(stall_patience=5)), run_after(opts)
    presets.append(f"| {name} | {b.status} / {b.niterations} | {a.status} / {a.niterations} |")

# --- multiresolution: per-level status and iterations, best of 3 timings ---------------
import time  # noqa: E402
import warnings  # noqa: E402

from carto_flow.flow_cartogram import CartogramWorkflow  # noqa: E402

warnings.simplefilter("ignore")
DATASETS = {
    "states": g,
    "districts": data.load_us_census(level="congressional_district", population=True).reset_index(drop=True),
}


def run_multires(frame, levels, stall_patience=None):
    kw = {} if stall_patience is None else {"stall_patience": stall_patience}
    opts = MorphOptions(show_progress=False, refresh_on_rise=None, **kw)
    wf = CartogramWorkflow(frame, "Population", options=opts)
    wf.morph_multiresolution(min_resolution=128, levels=levels, options=opts)
    return wf.results[1:]


def timed(fn):
    best, res = np.inf, None
    for _ in range(3):
        t = time.perf_counter()
        res = fn()
        best = min(best, time.perf_counter() - t)
    return res, best


multires = [
    "| data | levels | main: per level status / iterations | main total | fix: per level | fix total | time main / fix (s) |",
    "|---|---|---|---|---|---|---|",
]
for name, frame in DATASETS.items():
    for levels in (3, 4):
        rb, tb = timed(lambda f=frame, lv=levels: with_main_algorithm(lambda: run_multires(f, lv, 5)))
        ra, ta = timed(lambda f=frame, lv=levels: run_multires(f, lv))
        fmt = lambda rs: "; ".join(f"{r.status}/{r.niterations}" for r in rs)  # noqa: E731
        multires.append(
            f"| {name} | {levels} | {fmt(rb)} | {sum(r.niterations for r in rb)} | {fmt(ra)} | "
            f"{sum(r.niterations for r in ra)} | {tb:.1f} / {ta:.1f} |"
        )

# --- refresh_on_rise ON vs OFF (fix only; cost = iterations + recomputes x ratio) ------
ROR = 0.01
RATIO = {128: 9, 256: 12, 512: 24, 1024: 71}  # one recompute in plain-step units, per grid size


def ror_row(name, res, opts):
    s = score(res, opts)
    rises = int(np.sum((s[1:] > s[:-1]) & (s[:-1] < 20)))
    rec = res.benchmark.density_calls
    e = res.latest.errors
    return (
        f"| {name} | {res.status} | {res.niterations} | {rec} | {rises} | {e.mean_error_pct:.2f} / {e.max_error_pct:.1f} "
        f"| {s.min():.2f} | {res.niterations + rec * RATIO[opts.grid_size]:.0f} |"
    )


ror = [
    "| run | status | iterations | recomputes | rises (score < 20) | mean / max error % | best score | cost |",
    "|---|---|---|---|---|---|---|---|",
]
districts = DATASETS["districts"]
ROR_CASES = [
    ("horizontal", g, BASE.copy_with(anisotropy=HORIZONTAL)),
    ("horizontal, recompute_every=5", g, BASE.copy_with(anisotropy=HORIZONTAL, recompute_every=5)),
    ("tangential", g, BASE.copy_with(anisotropy=list(CONFIGS.values())[1])),
    ("tilted", g, BASE.copy_with(anisotropy=list(CONFIGS.values())[2])),
    ("default", g, MorphOptions()),
    ("grid 512", g, MorphOptions(grid_size=512)),
    ("tolerances 0.5% / 1%, n_iter=300", g, MorphOptions(n_iter=300, mean_tol=0.005, max_tol=0.01)),
    (
        "dt=0.6, tight, n_iter=60, no stall",
        g,
        MorphOptions(n_iter=60, dt=0.6, mean_tol=0.001, max_tol=0.002, stall_patience=None),
    ),
    ("preset_balanced, dt=0.6", g, MorphOptions.preset_balanced().copy_with(dt=0.6)),
    ("districts 256", districts, MorphOptions()),
    ("districts 512", districts, MorphOptions(grid_size=512)),
]
ror_results = {}
for name, frame, opts in ROR_CASES:
    opts = opts.copy_with(benchmark=True, show_progress=False)
    for label, value in (("off", None), (f"on {ROR}", ROR)):
        o = opts.copy_with(refresh_on_rise=value)
        res = morph_gdf(frame, "Population", options=o)
        ror_results[(name, label)] = (res, o)
        ror.append(ror_row(f"{name}, {label}", res, o))

ror_multires = [
    "| data | refresh_on_rise | per level: grid: status / iterations / recomputes | total iterations | cost |",
    "|---|---|---|---|---|",
]
for name, frame in DATASETS.items():
    for levels in (3, 4):
        for value in (None, ROR):
            o = MorphOptions(show_progress=False, benchmark=True, refresh_on_rise=value)
            wf = CartogramWorkflow(frame, "Population", options=o)
            wf.morph_multiresolution(min_resolution=128, levels=levels, options=o)
            rs = wf.results[1:]
            lv = "; ".join(f"{r.grid.sx}: {r.status}/{r.niterations}/{r.benchmark.density_calls}" for r in rs)
            cost = sum(r.niterations + r.benchmark.density_calls * RATIO[r.grid.sx] for r in rs)
            ror_multires.append(f"| {name}, {levels} levels | {value} | {lv} | {sum(r.niterations for r in rs)} | {cost:.0f} |")

fig, axes = plt.subplots(1, 2, figsize=(14, 4.2))
for ax, name in zip(axes, ("horizontal", "preset_balanced, dt=0.6"), strict=True):
    for label, color in (("off", "#1f77b4"), (f"on {ROR}", "#2ca02c")):
        res, o = ror_results[(name, label)]
        ax.plot(
            res.convergence.iterations,
            score(res, o),
            color=color,
            lw=1.4,
            label=f"refresh_on_rise {label}: {res.status}, {res.niterations} it.",
        )
    ax.axhline(1, color="k", lw=0.8)
    ax.set_yscale("log")
    ax.set_xlabel("iteration")
    ax.set_title(name, fontsize=10)
    ax.legend(fontsize=8)
axes[0].set_ylabel("score (< 1 converged)")
fig.tight_layout()
fig.savefig(HERE / "refresh_on_rise.png", dpi=130)
plt.close(fig)

# --- Figure 5: counties (not bundled; set COUNTIES_PARQUET to a GeoDataFrame file) -----
import os  # noqa: E402

from carto_flow.flow_cartogram.stall import StallMonitor  # noqa: E402


class AnyComponentMonitor(StallMonitor):
    """Previous progress definition: either component improving counts, also a satisfied one."""

    def update(self, step, mean_ratio, max_ratio):
        self._cur_mean = min(self._cur_mean, mean_ratio)
        self._cur_max = min(self._cur_max, max_ratio)
        if (step + 1) % self.cycle != 0:
            return False
        keep = 1.0 - self.min_improvement
        progress = self._cur_mean < self.best_mean * keep or self._cur_max < self.best_max * keep
        self.best_mean = min(self.best_mean, self._cur_mean)
        self.best_max = min(self.best_max, self._cur_max)
        self._cur_mean = self._cur_max = float("inf")
        self.cycles_without_progress = 0 if progress else self.cycles_without_progress + 1
        return self.cycles_without_progress >= self.patience


counties_path = os.environ.get("COUNTIES_PARQUET")
if counties_path:
    import geopandas as gpd

    counties = gpd.read_parquet(counties_path)
    fig, axes = plt.subplots(1, 2, figsize=(14, 4.5))
    for ax, grid_size in zip(axes, (256, 512), strict=True):
        opts = MorphOptions(
            show_progress=False, grid_size=grid_size, n_iter=600, area_scale=1e-6, stall_patience=None, refresh_on_rise=None
        )
        res = morph_gdf(counties, "total_votes", options=opts)
        mean_r = res.convergence.mean_log_errors / np.log2(1 + opts.mean_tol)
        max_r = res.convergence.max_log_errors / np.log2(1 + opts.max_tol)
        n = len(mean_r) // 10
        xs = np.arange(1, n + 1) * 10
        ax.plot(res.convergence.iterations, np.maximum(mean_r, max_r), color="0.8", lw=1, label="score per iteration")
        ax.plot(xs, mean_r[: n * 10].reshape(n, 10).min(axis=1), "o-", ms=3, color="#1f77b4", label="cycle min, mean ratio")
        ax.plot(xs, max_r[: n * 10].reshape(n, 10).min(axis=1), "s-", ms=3, color="#ff7f0e", label="cycle min, max ratio")
        for cls, color, ls, label in ((AnyComponentMonitor, "#c0392b", "--", "previous rule"), (StallMonitor, "#2ca02c", ":", "new rule")):
            mon = cls(4, 0.02, 10)
            stop = next((i + 1 for i in range(len(mean_r)) if mon.update(i, mean_r[i], max_r[i])), None)
            if stop:
                ax.axvline(stop, color=color, ls=ls, lw=2, label=f"{label} stops ({stop})")
        ax.axhline(1, color="k", lw=0.8)
        ax.set_yscale("log")
        ax.set_xlabel("iteration")
        ax.set_title(f"3,108 counties, grid {grid_size}", fontsize=10)
        ax.legend(fontsize=7)
    axes[0].set_ylabel("ratio to tolerance (< 1 satisfied)")
    fig.tight_layout()
    fig.savefig(HERE / "counties.png", dpi=130)
    plt.close(fig)
else:
    print("counties.png skipped: set COUNTIES_PARQUET to a GeoDataFrame of counties (column total_votes, area_scale=1e-6)")

print("| run | main: status / iterations | main: mean / max error % | fix: status / iterations | fix: mean / max error % |")
print("|---|---|---|---|---|")
print("\n".join(rows))
for table in (sweep, presets, multires, ror, ror_multires):
    print()
    print("\n".join(table))
