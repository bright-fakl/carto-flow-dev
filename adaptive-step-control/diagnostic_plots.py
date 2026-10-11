"""Per-iteration diagnostics of the step control for representative scenarios (diagnostics_*.png).

Run from a carto-flow checkout of the PR branch (bundled data only), after or independently of make_figures.py:
    NUMBA_NUM_THREADS=8 uv run python diagnostic_plots.py
REUSE=1 reads data/diagnostics.json if it exists. Every iteration is recorded (snapshot_every=1). Per scenario, for
adaptive_dt off (constant dt) and on:
  1. true maximum area error (from the geometry of each snapshot) with the tolerance and the stopping iteration;
  2. share of regions whose error sign changed in any of the last WINDOW iterations (the controller's detection, with
     its dead band), the threshold, and the iterations in which the controller shrank the step;
  3. fraction of dt: actual for the run with adaptive_dt, predicted for the constant-dt run by replaying the
     controller on the recorded errors (open loop: what the rule would have done had it been active);
  4. true mean area error with its tolerance.
"""

from __future__ import annotations

import json
import os
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import carto_flow.flow_cartogram.stepsize as stepsize
from carto_flow.flow_cartogram import CartogramWorkflow, MorphOptions, morph_gdf
from carto_flow.flow_cartogram.grid import build_multilevel_grids
from carto_flow.flow_cartogram.stall import cycle_length
from carto_flow.flow_cartogram.stepsize import DEAD_BAND_FRACTION, THRESHOLD, WINDOW, StepController
from make_figures import LATE_BAND, fixed_dead_band, options_for, source, true_errors

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
OFF, ON = "constant dt (adaptive_dt=False)", "adaptive_dt=True"
COLORS = {False: "#2a78d6", True: "#eb6834"}

# Fractions actually used by the controller, recorded by wrapping StepController.current.
USED: list[float] = []
INITIAL_SCORE: list[float] = []
_current = StepController.current


def _recording_current(self, step):
    value = _current(self, step)
    if step == 0:
        USED.clear()
        INITIAL_SCORE[:] = [self.score]
    USED.append(value)
    return value


StepController.current = _recording_current


def score_series(log_errors, mean_tol, max_tol):
    a = np.abs(log_errors)
    return np.maximum(a.mean(axis=1) / np.log2(1 + mean_tol), a.max(axis=1) / np.log2(1 + max_tol))


def replay(log_errors, scores, window, initial_score, dead_band):
    """Share of regions with a recent sign change and the controller's fractions on a recorded error sequence."""
    controller = StepController(window, initial_score, dead_band)
    previous, recent = None, []
    share, share_all, fraction, shrinks = [], [], [], []
    for t, e in enumerate(log_errors):
        fraction.append(controller.current(t))
        before = controller.fraction
        controller.update(e, scores[t])
        if controller.fraction < before:
            shrinks.append(t + 1)
        flipped = np.zeros(len(e), bool)
        if previous is not None:
            flipped = (np.abs(e) > dead_band) & (np.abs(previous) > dead_band) & (np.sign(e) != np.sign(previous))
        recent = (recent + [flipped])[-WINDOW:]
        inverted = np.any(recent, axis=0)
        share.append(float(inverted.mean()))
        share_all.append(float(inverted.mean()))
        previous = e
    return share, share_all, fraction, shrinks


def collect(result, options, values, adaptive, initial_score=None, dead_band=None):
    snaps = result.snapshots.snapshots
    log_errors = np.array([s.errors.log_errors for s in snaps])
    scores = score_series(log_errors, options.mean_tol, options.max_tol)
    true = np.array([true_errors(s.geometry, values) for s in snaps])
    window = cycle_length(options.recompute_every)
    init = INITIAL_SCORE[0] if adaptive else initial_score
    if dead_band is None:
        dead_band = DEAD_BAND_FRACTION * np.log2(1 + options.max_tol)
    share, share_all, predicted, shrinks = replay(log_errors, scores, window, init, dead_band)
    out = {
        "adaptive": adaptive, "status": result.status.value, "it": int(result.niterations),
        "mean_tol": options.mean_tol, "max_tol": options.max_tol,
        "true_max": (true.max(axis=1) * 100).tolist(), "true_mean": (true.mean(axis=1) * 100).tolist(),
        "share": share, "share_all": share_all, "shrinks": shrinks, "fraction": list(USED) if adaptive else predicted,
        "initial_score": float(init),
    }
    return out


def fresh(name, grid, dt, tol=None, rise=0.01, n_iter=400, band=None, **extra):
    gdf = source(name)
    values = gdf["Population"].to_numpy(float)
    runs = {}
    init = None
    for adaptive in (True, False):  # the run with adaptive_dt first: it records the initial score
        o = options_for(name, adaptive, grid, dt, tol, snapshot_every=1, recompute_on_rise=rise, n_iter=n_iter, **extra)
        if band is None:
            res = morph_gdf(gdf, "Population", options=o)
        else:
            with fixed_dead_band(band):
                res = morph_gdf(gdf, "Population", options=o)
        runs[adaptive] = collect(res, o, values, adaptive, init, band)
        init = runs[True]["initial_score"]
    return runs


def multires_level(name, dt, tol=None):
    gdf = source(name)
    values = gdf["Population"].to_numpy(float)
    runs, init = {}, None
    for adaptive in (True, False):
        o = options_for(name, adaptive, 256, dt, tol, n_iter=300, snapshot_every=1)
        wf = CartogramWorkflow(gdf, "Population", options=o)
        grid = build_multilevel_grids(wf._original_gdf.total_bounds, 128, 3, margin=o.grid_margin, square=True)[0]
        lo = o.copy_with(grid=grid)
        res = wf.morph(options=lo)
        runs[adaptive] = collect(res, lo, values, adaptive, init)
        init = runs[True]["initial_score"]
    return runs


def continuation(name, grid, first_tol, tol):
    gdf = source(name)
    values = gdf["Population"].to_numpy(float)
    runs, init = {}, None
    for adaptive in (True, False):
        wf = CartogramWorkflow(gdf, "Population", options=options_for(name, adaptive, grid, 0.2, first_tol))
        wf.morph()
        o = options_for(name, adaptive, grid, 0.2, tol, snapshot_every=1)
        res = wf.morph(options=o)
        runs[adaptive] = collect(res, o, values, adaptive, init)
        init = runs[True]["initial_score"]
    return runs


SCENARIOS = [
    ("horizontal_dt06", "Horizontal anisotropy, states grid 256, dt 0.6, default tolerances (122 against 127 iterations)", lambda: fresh("horizontal", 256, 0.6)),
    ("tangential_dt06", "Tangential anisotropy, states grid 256, dt 0.6, default tolerances (118 against 123)", lambda: fresh("tangential", 256, 0.6)),
    ("tilted_dt06", "Tilted anisotropy, states grid 256, dt 0.6, default tolerances (95 against 98)", lambda: fresh("tilted", 256, 0.6)),
    ("districts_multires", "Districts, coarse multiresolution level (grid 128), dt 0.2, default tolerances (123 in both modes)", lambda: multires_level("districts", 0.2)),
    ("districts_multires_tight", "Districts, coarse multiresolution level (grid 128), dt 0.2, tolerances 0.5 % / 1 % (173 against 149 iterations)", lambda: multires_level("districts", 0.2, (0.005, 0.01))),
    ("states_tight", "States grid 256, dt 0.2, tolerances 0.5 % / 1 % (112 in both modes)", lambda: fresh("states", 256, 0.2, (0.005, 0.01))),
    ("districts_continuation", "Districts grid 256: second run at 0.5 % / 1 % on a result converged at 5 % / 20 % (7 against 13)", lambda: continuation("districts", 256, (0.05, 0.2), (0.005, 0.01))),
    ("tilted_stall", "Tilted anisotropy, dt 0.6, default tolerances, recompute_on_rise None (stalls at 130 in both modes)", lambda: fresh("tilted", 256, 0.6, rise=None)),
    ("states_tight_none", "States grid 256, dt 0.2, tolerances 0.2 % / 0.4 %, recompute_on_rise None (192 against 152)", lambda: fresh("states", 256, 0.2, (0.002, 0.004), rise=None)),
    ("states_late", "States grid 256, dt 0.4, unreachable tolerances 1e-6, dead band as for a 0.4 % max tolerance, stall rule off (late phase)", lambda: fresh("states", 256, 0.4, (1e-6, 1e-6), n_iter=300, band=LATE_BAND, stall_patience=None)),
]


def plot(key, title, runs):
    fig, axes = plt.subplots(4, 1, figsize=(9, 11), sharex=True, gridspec_kw={"hspace": 0.12})
    for a in (False, True):
        r = runs[a]
        x = np.arange(1, len(r["true_max"]) + 1)
        label = f"{ON if a else OFF}: {r['it']} it, {r['status']}"
        c = COLORS[a]
        axes[0].plot(x, r["true_max"], color=c, label=label, linewidth=1.3)
        axes[0].axvline(r["it"], color=c, linestyle=":", linewidth=1.2)
        axes[1].plot(x, r["share"], color=c, linewidth=1.3, label=("inverted regions, " + ON) if a else ("inverted regions, " + OFF))
        axes[2].plot(x, r["fraction"], color=c, linewidth=1.6, label=("actual (" + ON + ")") if a else ("predicted (open loop on the constant-dt run)"),
                     linestyle="-" if a else "--")
        axes[3].plot(x, r["true_mean"], color=c, linewidth=1.3)
        axes[3].axvline(r["it"], color=c, linestyle=":", linewidth=1.2)
        if a:
            for s in r["shrinks"]:
                axes[1].plot(s, r["share"][s - 1], "v", color=c, markersize=6)
        else:
            for s in r["shrinks"]:
                axes[1].plot(s, r["share"][s - 1], "v", color=c, markersize=5, markerfacecolor="none")
    r = runs[True]
    axes[0].axhline(r["max_tol"] * 100, color="black", linestyle="--", linewidth=0.8, label=f"max tolerance {r['max_tol'] * 100:.3g} %")
    axes[3].axhline(r["mean_tol"] * 100, color="black", linestyle="--", linewidth=0.8, label=f"mean tolerance {r['mean_tol'] * 100:.3g} %")
    axes[1].axhline(THRESHOLD, color="black", linestyle="--", linewidth=0.8, label=f"threshold {THRESHOLD} on the share of inverted regions (triangles: shrink events; open: predicted on the constant-dt run)")
    axes[0].set_yscale("log")
    axes[3].set_yscale("log")
    axes[2].set_ylim(0, 1.05)
    axes[0].set_ylabel("true max area error %")
    axes[1].set_ylabel("share of regions with a\nrecent sign change")
    axes[2].set_ylabel("fraction of dt")
    axes[3].set_ylabel("true mean area error %")
    axes[3].set_xlabel("iteration (dotted: stopping iteration)")
    for ax in axes:
        ax.grid(True, color="#e6e5e1", linewidth=0.8)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        ax.legend(frameon=False, fontsize=7, loc="best")
    fig.suptitle(title, fontsize=10)
    fig.savefig(HERE / f"diagnostics_{key}.png", dpi=110, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    path = HERE / "data" / "diagnostics.json"
    stored = json.loads(path.read_text()) if (os.environ.get("REUSE") == "1" and path.exists()) else {}
    for key, title, fn in SCENARIOS:
        if key not in stored:
            runs = fn()
            stored[key] = {str(a): r for a, r in runs.items()}
            print(key, {a: (r["it"], r["status"], len(r["shrinks"]), round(r["fraction"][-1], 3)) for a, r in runs.items()}, flush=True)
            path.write_text(json.dumps(stored))
        plot(key, title, {a == "True": r for a, r in stored[key].items()})
