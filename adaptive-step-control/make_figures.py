"""Figures and tables for the adaptive step PR: `adaptive_dt` off (constant dt, as on main) against on.

Run from a carto-flow checkout of the PR branch (bundled data only; the counties part runs when
COUNTIES_PARQUET points at a GeoDataFrame file with GEOID, total_votes and geometry):
    NUMBA_NUM_THREADS=8 uv run python make_figures.py
Runs are sequential so that wall times are comparable. REUSE=1 reads data/<section>.json for sections
that were computed before. Writes the PNGs next to this file, data/<section>.json and data/tables.md.

The true area error of an output is |area / (value share of the total output area) - 1|, computed from
the output geometry. Cost = iterations + field recomputes x (cost of one recompute in plain steps).
"""

from __future__ import annotations

import json
import os
import time
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import shapely

import carto_flow.flow_cartogram.algorithm as alg
from carto_flow import data
from carto_flow.flow_cartogram import CartogramWorkflow, MorphOptions, morph_gdf
from carto_flow.flow_cartogram.anisotropy import DirectionalTensor
from carto_flow.flow_cartogram.stepsize import DEAD_BAND, THRESHOLD, WINDOW

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
(HERE / "data").mkdir(exist_ok=True)
REUSE = os.environ.get("REUSE") == "1"
TABLES: list[str] = []

STATES = data.load_us_census(population=True).reset_index(drop=True)
DISTRICTS = data.load_us_census(population=True, level="congressional_district").reset_index(drop=True)
INPUTS = {"states": STATES, "districts": DISTRICTS}

# Cost of one field recompute in plain steps, measured per input and grid (adaptive-recompute-experiment).
RATIO = {
    "states": {128: 9.0, 256: 12.0, 512: 24.0, 1024: 71.0},
    "districts": {128: 18.0, 256: 21.0, 512: 23.0, 1024: 47.0},
}

BALANCED = MorphOptions.preset_balanced()
ANISOTROPY = {
    "horizontal": DirectionalTensor(theta=0, Dpar=4, Dperp=0.3),
    "tangential": DirectionalTensor.tangential(Dpar=4, Dperp=0.3),
    "tilted": DirectionalTensor(theta=np.pi / 6, Dpar=4, Dperp=0.3),
}
TIGHT = {"0.2 / 0.4": (0.002, 0.004), "0.5 / 1": (0.005, 0.01)}
OFF, ON = "constant dt (main)", "adaptive_dt"
COLORS = {OFF: "#2a78d6", ON: "#eb6834"}

# Counters: field recomputes of the run in progress.
COUNT = {"recomputes": 0}
_density = alg.compute_density_field_from_geometries


def _counting_density(*args, **kwargs):
    COUNT["recomputes"] += 1
    return _density(*args, **kwargs)


alg.compute_density_field_from_geometries = _counting_density


def true_errors(geometries, values):
    a = shapely.area(np.asarray(list(geometries), dtype=object))
    w = np.asarray(values, float)
    return np.abs(a / (w / w.sum() * a.sum()) - 1.0)


def options_for(name, adaptive, grid, dt=0.2, tol=None, **extra):
    kw = {"grid_size": grid, "dt": dt, "n_iter": 400, "show_progress": False, "adaptive_dt": adaptive}
    if name in ANISOTROPY:
        kw.update(
            {k: getattr(BALANCED, k) for k in ("Dx", "Dy", "mean_tol", "max_tol")},
            area_scale=1e-6,
            anisotropy=ANISOTROPY[name],
        )
    if tol is not None:
        kw.update(mean_tol=tol[0], max_tol=tol[1])
    kw.update(extra)
    return MorphOptions(**kw)


def source(name):
    return STATES if name in ANISOTROPY else INPUTS[name]


def ratio(name, grid):
    return RATIO["states" if name in ANISOTROPY else name][grid]


def score_history(conv, o):
    return np.maximum(conv.mean_log_errors / np.log2(1 + o.mean_tol), conv.max_log_errors / np.log2(1 + o.max_tol))


def fresh_run(name, adaptive, grid, dt=0.2, tol=None, keep_score=False, **extra):
    gdf = source(name)
    o = options_for(name, adaptive, grid, dt, tol, **extra)
    COUNT["recomputes"] = 0
    t = time.perf_counter()
    res = morph_gdf(gdf, "Population", options=o)
    wall = time.perf_counter() - t
    err = true_errors(res.get_geometry(), gdf["Population"])
    out = {
        "case": name, "grid": grid, "dt": dt, "tol": list(tol) if tol else None, "adaptive": adaptive,
        "status": res.status.value, "it": int(res.niterations), "rec": COUNT["recomputes"],
        "cost": res.niterations + COUNT["recomputes"] * ratio(name, grid),
        "true_mean": float(err.mean() * 100), "true_max": float(err.max() * 100), "wall": wall,
    }
    if keep_score:
        out["score"] = score_history(res.convergence, o).tolist()
    return out


def section(name, fn):
    path = HERE / "data" / f"{name}.json"
    if REUSE and path.exists():
        return json.loads(path.read_text())
    out = fn()
    path.write_text(json.dumps(out))
    return out


def label(adaptive):
    return ON if adaptive else OFF


# ---------------------------------------------------------------------------------------------
def fresh_section():
    rows = []
    cases = [("states", g, 0.2) for g in (128, 256, 512)] + [("districts", 256, 0.2)]
    cases += [("states", 256, 0.4), ("districts", 256, 0.4)]
    cases += [(a, 256, dt) for a in ANISOTROPY for dt in (0.2, 0.6)]
    for name, grid, dt in cases:
        for adaptive in (False, True):
            runs = [fresh_run(name, adaptive, grid, dt) for _ in range(2)]
            best = min(runs, key=lambda r: r["wall"])
            rows.append(best)
            print("fresh", name, grid, dt, adaptive, best["status"], best["it"], round(best["wall"], 2), flush=True)
    return rows


def tight_section():
    rows = []
    for name, grids in (("states", (128, 256, 512)), ("districts", (256,))):
        for grid in grids:
            for tol_label, tol in TIGHT.items():
                for dt in (0.2, 0.4):
                    for rise in (0.01, None):
                        for adaptive in (False, True):
                            r = fresh_run(name, adaptive, grid, dt, tol, recompute_on_rise=rise)
                            r["tol_label"] = tol_label
                            r["recompute_on_rise"] = rise
                            rows.append(r)
                            print("tight", name, grid, tol_label, dt, rise, adaptive, r["status"], r["it"], flush=True)
    return rows


def inversion_share(snapshots, values):
    """Share of regions per iteration whose area error changed sign in the last WINDOW iterations (as in stepsize.py)."""
    target = values / values.sum()
    previous, recent, out = None, [], []
    for s in snapshots:
        a = shapely.area(np.asarray(list(s.geometry), dtype=object))
        e = np.log2(a / a.sum() / target)
        flipped = np.zeros(len(e), bool)
        if previous is not None:
            flipped = (np.abs(e) > DEAD_BAND) & (np.abs(previous) > DEAD_BAND) & (np.sign(e) != np.sign(previous))
        recent = (recent + [flipped])[-WINDOW:]
        out.append(float(np.any(recent, axis=0).mean()))
        previous = e
    return out


def late_section():
    """Every iteration recorded: true maximum area error at unreachable tolerances (the step is not tuned to them)."""
    rows = []
    for name, grid, dts in (("states", 256, (0.1, 0.2, 0.4)), ("districts", 256, (0.2,))):
        gdf = source(name)
        values = gdf["Population"].to_numpy(float)
        for dt in dts:
            for rise in (0.01, None):
                for adaptive in (False, True):
                    o = options_for(name, adaptive, grid, dt, (1e-6, 1e-6), n_iter=300, stall_patience=None, snapshot_every=1, recompute_on_rise=rise)
                    res = morph_gdf(gdf, "Population", options=o)
                    series = [float(true_errors(s.geometry, values).max() * 100) for s in res.snapshots.snapshots]
                    rows.append({"case": name, "grid": grid, "dt": dt, "adaptive": adaptive, "recompute_on_rise": rise, "series": series,
                                 "share": inversion_share(res.snapshots.snapshots, values) if not adaptive else None})
                    tail = np.array(series[-50:])
                    print("late", name, dt, rise, adaptive, round(tail.min(), 3), round(np.median(tail), 3), round(tail.max(), 3), flush=True)
    return rows


def trace_section():
    """Score per iteration at tight but reachable tolerances, states, every iteration."""
    rows = []
    for dt in (0.2, 0.4):
        for adaptive in (False, True):
            r = fresh_run("states", adaptive, 256, dt, (0.002, 0.004), keep_score=True, stall_patience=None, n_iter=250)
            rows.append(r)
    return rows


def restart_section():
    """A second run on the output of a first run (tight tolerances), as in a workflow refinement or a second phase."""
    rows = []
    loose = (0.05, 0.2)
    tight = (0.005, 0.01)
    for name, grid in (("states", 256), ("states", 512), ("districts", 256)):
        gdf = source(name)
        for start, tol in (("converged at 0.5 % / 1 %", tight), ("converged at 5 % / 20 %", loose)):
            for adaptive in (False, True):
                wf = CartogramWorkflow(gdf, "Population", options=options_for(name, adaptive, grid, 0.2, tol))
                COUNT["recomputes"] = 0
                first = wf.morph()
                first_rec = COUNT["recomputes"]
                COUNT["recomputes"] = 0
                second = wf.morph(options=options_for(name, adaptive, grid, 0.2, tight))
                score = score_history(second.convergence, second.options)
                rows.append({
                    "case": name, "grid": grid, "start": start, "adaptive": adaptive,
                    "first_status": first.status.value, "first_it": int(first.niterations),
                    "status": second.status.value, "it": int(second.niterations), "rec": COUNT["recomputes"],
                    "cost": second.niterations + COUNT["recomputes"] * ratio(name, grid),
                    "score_first": float(score[0]), "score_max5": float(score[:5].max()),
                })
                print("restart", name, grid, start, adaptive, rows[-1]["status"], rows[-1]["it"], flush=True)
    return rows


def multires_section():
    rows = []
    for name in ("states", "districts"):
        gdf = source(name)
        for tol_label, tol in (("default 5 % / 10 %", None), ("0.5 % / 1 %", (0.005, 0.01))):
            for dt in (0.2, 0.4):
                for adaptive in (False, True):
                    o = options_for(name, adaptive, 256, dt, tol, n_iter=300)
                    wf = CartogramWorkflow(gdf, "Population", options=o)
                    COUNT["recomputes"] = 0
                    levels, cost, its = [], 0.0, 0
                    # Levels one by one to read the counters of each level (morph_multiresolution runs the same loop).
                    from carto_flow.flow_cartogram.grid import build_multilevel_grids

                    grids = build_multilevel_grids(wf._original_gdf.total_bounds, 128, 3, margin=o.grid_margin, square=True)
                    t = time.perf_counter()
                    for level, grid in enumerate(grids):
                        lo = o.copy_with(grid=grid)
                        if level > 0:
                            lo.prescale_components = False
                        COUNT["recomputes"] = 0
                        res = wf.morph(options=lo)
                        cost += res.niterations + COUNT["recomputes"] * ratio(name, grid.sx)
                        its += res.niterations
                        levels.append({"grid": int(grid.sx), "status": res.status.value, "it": int(res.niterations)})
                        if res.status.value == "converged":
                            break
                    wall = time.perf_counter() - t
                    err = true_errors(wf.last.get_geometry(), gdf["Population"])
                    rows.append({
                        "case": name, "tol_label": tol_label, "dt": dt, "adaptive": adaptive, "levels": levels,
                        "converged": levels[-1]["status"] == "converged", "it": its, "cost": cost, "wall": wall,
                        "true_max": float(err.max() * 100),
                    })
                    print("multires", name, tol_label, dt, adaptive, levels, round(cost), flush=True)
    return rows


def schedule_section():
    """Recompute schedule without the rise rule, and the anisotropy runs: the controller is independent of recompute_on_rise."""
    rows = []
    for name, grid, dt, tol in (("states", 256, 0.2, (0.002, 0.004)), ("states", 256, 0.4, (0.002, 0.004)), ("tilted", 256, 0.6, None), ("horizontal", 256, 0.6, None)):
        for rise in (0.01, None):
            for adaptive in (False, True):
                r = fresh_run(name, adaptive, grid, dt, tol, recompute_on_rise=rise)
                r["recompute_on_rise"] = rise
                rows.append(r)
                print("schedule", name, dt, rise, adaptive, r["status"], r["it"], flush=True)
    return rows


def counties_section():
    path = os.environ.get("COUNTIES_PARQUET")
    if not path:
        return []
    import geopandas as gpd

    gdf = gpd.read_parquet(path)
    rows = []
    for grid in (256,):
        for adaptive in (False, True):
            o = MorphOptions(grid_size=grid, n_iter=300, area_scale=1e-6, show_progress=False, adaptive_dt=adaptive)
            t = time.perf_counter()
            res = morph_gdf(gdf, "total_votes", options=o)
            err = true_errors(res.get_geometry(), gdf["total_votes"])
            e = res.get_errors()
            rows.append({
                "grid": grid, "adaptive": adaptive, "status": res.status.value, "it": int(res.niterations),
                "best_iteration": int(res.best_iteration), "reported_mean": float(e.mean_error_pct),
                "reported_max": float(e.max_error_pct), "true_mean": float(err.mean() * 100),
                "true_max": float(err.max() * 100), "wall": time.perf_counter() - t,
            })
            print("counties", grid, adaptive, rows[-1], flush=True)
    return rows


# ---------------------------------------------------------------------------------------------
def pairs(rows, keys):
    out = {}
    for r in rows:
        out.setdefault(tuple(r[k] if not isinstance(r[k], list) else tuple(r[k]) for k in keys), {})[r["adaptive"]] = r
    return out


def table_fresh(rows):
    TABLES.append("## Fresh runs, default tolerances (5 % / 10 %), wall time is the minimum of two runs")
    TABLES.append("")
    TABLES.append("| input | grid | dt | constant dt: status, iterations, recomputes, cost, wall s, true max % | adaptive_dt: same |")
    TABLES.append("|---|---|---|---|---|")
    for (case, grid, dt), p in pairs(rows, ("case", "grid", "dt")).items():
        cells = [f"{p[a]['status']}, {p[a]['it']}, {p[a]['rec']}, {p[a]['cost']:.0f}, {p[a]['wall']:.2f}, {p[a]['true_max']:.2f}" for a in (False, True)]
        TABLES.append(f"| {case} | {grid} | {dt} | {cells[0]} | {cells[1]} |")
    TABLES.append("")


def table_tight(rows):
    TABLES.append("## Tight tolerances (mean / max)")
    TABLES.append("")
    TABLES.append("| input | grid | tolerances % | dt | recompute_on_rise | constant dt: status, it, cost | adaptive_dt: status, it, cost | true max %: constant / adaptive |")
    TABLES.append("|---|---|---|---|---|---|---|---|")
    for (case, grid, tl, dt, rise), p in pairs(rows, ("case", "grid", "tol_label", "dt", "recompute_on_rise")).items():
        cells = [f"{p[a]['status']}, {p[a]['it']}, {p[a]['cost']:.0f}" for a in (False, True)]
        TABLES.append(f"| {case} | {grid} | {tl} | {dt} | {rise} | {cells[0]} | {cells[1]} | {p[False]['true_max']:.2f} / {p[True]['true_max']:.2f} |")
    TABLES.append("")
    conv = {a: sum(r["status"] == "converged" for r in rows if r["adaptive"] == a) for a in (False, True)}
    n = sum(1 for r in rows if r["adaptive"])
    TABLES.append(f"Converged: constant dt {conv[False]} of {n}, adaptive_dt {conv[True]} of {n}.")
    TABLES.append("")


def table_late(rows):
    TABLES.append("## Late phase: true maximum area error over the last 50 of 300 iterations (every iteration recorded, tolerances unreachable)")
    TABLES.append("")
    TABLES.append("| input | dt | recompute_on_rise | constant dt: lowest / median / highest % | adaptive_dt: lowest / median / highest % |")
    TABLES.append("|---|---|---|---|---|")
    for (case, dt, rise), p in pairs(rows, ("case", "dt", "recompute_on_rise")).items():
        cells = []
        for a in (False, True):
            t = np.array(p[a]["series"][-50:])
            cells.append(f"{t.min():.3f} / {np.median(t):.3f} / {t.max():.3f}")
        TABLES.append(f"| {case} | {dt} | {rise} | {cells[0]} | {cells[1]} |")
    TABLES.append("")


def table_restart(rows):
    TABLES.append("## Second run on the output of a first run (tight tolerances 0.5 % / 1 %, workflow refinement)")
    TABLES.append("")
    TABLES.append("| input | grid | first run | constant dt: status, it, cost, score after it 1, max score in it 1-5 | adaptive_dt: same |")
    TABLES.append("|---|---|---|---|---|")
    for (case, grid, start), p in pairs(rows, ("case", "grid", "start")).items():
        cells = [f"{p[a]['status']}, {p[a]['it']}, {p[a]['cost']:.0f}, {p[a]['score_first']:.1f}, {p[a]['score_max5']:.1f}" for a in (False, True)]
        TABLES.append(f"| {case} | {grid} | {start} | {cells[0]} | {cells[1]} |")
    TABLES.append("")


def table_multires(rows):
    TABLES.append("## Multiresolution (min_resolution 128, 3 levels, 300 iterations per level)")
    TABLES.append("")
    TABLES.append("| input | tolerances | dt | constant dt: levels (grid:status:it), cost, true max % | adaptive_dt: same |")
    TABLES.append("|---|---|---|---|---|")
    for (case, tl, dt), p in pairs(rows, ("case", "tol_label", "dt")).items():
        cells = []
        for a in (False, True):
            lv = " ".join(f"{x['grid']}:{x['status'][:4]}:{x['it']}" for x in p[a]["levels"])
            cells.append(f"{lv}, {p[a]['cost']:.0f}, {p[a]['true_max']:.2f}")
        TABLES.append(f"| {case} | {tl} | {dt} | {cells[0]} | {cells[1]} |")
    TABLES.append("")


def table_schedule(rows):
    TABLES.append("## With and without recompute_on_rise")
    TABLES.append("")
    TABLES.append("| input | dt | tolerances | recompute_on_rise | constant dt: status, it, cost | adaptive_dt: status, it, cost |")
    TABLES.append("|---|---|---|---|---|---|")
    for (case, dt, tol, rise), p in pairs(rows, ("case", "dt", "tol", "recompute_on_rise")).items():
        cells = [f"{p[a]['status']}, {p[a]['it']}, {p[a]['cost']:.0f}" for a in (False, True)]
        TABLES.append(f"| {case} | {dt} | {tol or 'default'} | {rise} | {cells[0]} | {cells[1]} |")
    TABLES.append("")


def table_counties(rows):
    if not rows:
        return
    TABLES.append("## Counties (3,108, grid 256, 300 iterations)")
    TABLES.append("")
    TABLES.append("| adaptive_dt | status | iterations | best iteration | reported mean / max % | true mean / max % | wall s |")
    TABLES.append("|---|---|---|---|---|---|---|")
    for r in rows:
        TABLES.append(f"| {r['adaptive']} | {r['status']} | {r['it']} | {r['best_iteration']} | {r['reported_mean']:.1f} / {r['reported_max']:.0f} | {r['true_mean']:.1f} / {r['true_max']:.0f} | {r['wall']:.1f} |")
    TABLES.append("")


# ---------------------------------------------------------------------------------------------
def style(ax):
    ax.grid(True, color="#e6e5e1", linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


def fig_late(rows):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2))
    ax = axes[0]
    style(ax)
    p = pairs(rows, ("case", "dt", "recompute_on_rise"))[("states", 0.2, 0.01)]
    for a in (False, True):
        s = p[a]["series"][-80:]
        ax.plot(np.arange(300 - len(s) + 1, 301), s, color=COLORS[label(a)], label=label(a), linewidth=1.5)
    ax.set_xlabel("iteration")
    ax.set_ylabel("true maximum area error %")
    ax.set_title("States, grid 256, dt 0.2: last 80 iterations", fontsize=10)
    ax.legend(frameon=False)
    ax = axes[1]
    style(ax)
    dts = sorted({r["dt"] for r in rows if r["case"] == "states"})
    for a in (False, True):
        hi = [np.max(pairs(rows, ("case", "dt", "recompute_on_rise"))[("states", dt, 0.01)][a]["series"][-50:]) for dt in dts]
        med = [np.median(pairs(rows, ("case", "dt", "recompute_on_rise"))[("states", dt, 0.01)][a]["series"][-50:]) for dt in dts]
        ax.plot(dts, hi, "o-", color=COLORS[label(a)], label=f"{label(a)}: highest")
        ax.plot(dts, med, "s--", color=COLORS[label(a)], alpha=0.6, label=f"{label(a)}: median")
    ax.set_xlabel("dt")
    ax.set_ylabel("true maximum area error %, last 50 iterations")
    ax.set_title("Amplitude of the late phase against dt", fontsize=10)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(HERE / "late_phase.png", dpi=120)
    plt.close(fig)


def fig_share(rows):
    """Share of regions with a recent sign change, constant dt, against the true maximum error (every iteration)."""
    p = pairs(rows, ("case", "dt", "recompute_on_rise"))[("states", 0.2, 0.01)][False]
    fig, ax = plt.subplots(figsize=(10, 4.2))
    style(ax)
    x = np.arange(1, len(p["share"]) + 1)
    ax.plot(x, p["share"], color="#eb6834", label="share of regions with a sign change in the last 3 iterations")
    ax.axhline(THRESHOLD, color="black", linestyle="--", linewidth=0.8, label=f"threshold {THRESHOLD}")
    ax.set_xlabel("iteration")
    ax.set_ylabel("share of regions")
    ax2 = ax.twinx()
    ax2.plot(x, p["series"], color="#2a78d6", linewidth=1.0, label="true maximum area error %")
    ax2.set_yscale("log")
    ax2.set_ylabel("true maximum area error %")
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, frameon=False, fontsize=8, loc="center left")
    ax.set_title("States, grid 256, dt 0.2, constant dt, tolerances 1e-6", fontsize=10)
    fig.tight_layout()
    fig.savefig(HERE / "inversion_share.png", dpi=120)
    plt.close(fig)


def fig_traces(rows):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2), sharey=True)
    for ax, dt in zip(axes, (0.2, 0.4), strict=True):
        style(ax)
        for r in rows:
            if r["dt"] == dt:
                ax.plot(np.arange(1, len(r["score"]) + 1), r["score"], color=COLORS[label(r["adaptive"])], label=f"{label(r['adaptive'])}: {r['it']} it, {r['status']}", linewidth=1.5)
        ax.axhline(1.0, color="black", linestyle="--", linewidth=0.8)
        ax.set_yscale("log")
        ax.set_ylim(bottom=0.1)
        ax.set_xlim(left=95 if dt == 0.2 else 50)
        ax.set_xlabel("iteration")
        ax.set_title(f"States, grid 256, tolerances 0.2 % / 0.4 %, dt {dt}", fontsize=10)
        ax.legend(frameon=False, fontsize=8)
    axes[0].set_ylabel("score (below 1 is converged)")
    fig.tight_layout()
    fig.savefig(HERE / "tight_traces.png", dpi=120)
    plt.close(fig)


def fig_cost(fresh, tight):
    fig, axes = plt.subplots(1, 2, figsize=(13, 8), gridspec_kw={"width_ratios": [1, 1.15]})
    marks = {(True, True): ("o", "#0b0b0b", "both converged"), (False, True): ("^", "#eb6834", "only adaptive_dt converged"),
             (True, False): ("v", "#2a78d6", "only constant dt converged"), (False, False): ("s", "#7a7a7a", "neither converged")}
    for ax, rows, keys, title in (
        (axes[0], fresh, ("case", "grid", "dt"), "default tolerances"),
        (axes[1], tight, ("case", "grid", "tol_label", "dt", "recompute_on_rise"), "tight tolerances"),
    ):
        style(ax)
        items = list(pairs(rows, keys).items())
        for y, (k, p) in enumerate(items):
            m, c, _ = marks[(p[False]["status"] == "converged", p[True]["status"] == "converged")]
            ax.plot(p[True]["cost"] / p[False]["cost"], y, m, color=c, markersize=6)
        ax.set_yticks(range(len(items)))
        ax.set_yticklabels([" ".join(str(x) for x in k) for k, _ in items], fontsize=7)
        ax.invert_yaxis()
        ax.axvline(1.0, color="black", linewidth=0.8)
        ax.set_xscale("log")
        ax.set_xlim(0.08, 1.6)
        ax.minorticks_off()
        ax.set_xticks([0.1, 0.2, 0.5, 1.0, 1.5])
        ax.set_xticklabels(["0.1", "0.2", "0.5", "1", "1.5"])
        ax.set_title(title + " (labels: input, grid, [tolerances %, dt, recompute_on_rise], dt)", fontsize=9)
        ax.set_xlabel("cost with adaptive_dt / cost with constant dt")
    for m, c, text in marks.values():
        axes[1].plot([], [], m, color=c, label=text)
    axes[1].legend(frameon=False, fontsize=8, loc="lower left")
    fig.tight_layout()
    fig.savefig(HERE / "cost_ratio.png", dpi=120)
    plt.close(fig)


def fig_restart(rows):
    fig, ax = plt.subplots(figsize=(10, 4.2))
    style(ax)
    keys = list(pairs(rows, ("case", "grid", "start")).items())
    x = np.arange(len(keys))
    for i, a in enumerate((False, True)):
        ax.bar(x + (i - 0.5) * 0.38, [p[a]["it"] for _, p in keys], 0.38, color=COLORS[label(a)], label=label(a))
    ax.set_xticks(x)
    ax.set_xticklabels([f"{k[0]} {k[1]}\n{k[2].replace('converged at ', '')}" for k, _ in keys], fontsize=7)
    ax.set_ylabel("iterations of the second run")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(HERE / "restart.png", dpi=120)
    plt.close(fig)


if __name__ == "__main__":
    fresh = section("fresh", fresh_section)
    tight = section("tight", tight_section)
    late = section("late", late_section)
    traces = section("traces", trace_section)
    restart = section("restart", restart_section)
    multires = section("multires", multires_section)
    schedule = section("schedule", schedule_section)
    counties = section("counties", counties_section)
    table_fresh(fresh)
    table_tight(tight)
    table_late(late)
    table_restart(restart)
    table_multires(multires)
    table_schedule(schedule)
    table_counties(counties)
    fig_late(late)
    fig_share(late)
    fig_traces(traces)
    fig_cost(fresh, tight)
    fig_restart(restart)
    (HERE / "data" / "tables.md").write_text("\n".join(TABLES) + "\n")
