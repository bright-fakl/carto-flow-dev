"""Sweep of the contested fraction of the step controller: constant dt and CONTESTED_FRACTION 0.8, 0.9, 1.0.

A region is contested if its error is at least this fraction of the largest error; 1.0 is the region of the
largest error only. Run from a carto-flow checkout of the PR branch (bundled data only):
    NUMBA_NUM_THREADS=8 uv run python contested_sweep.py [orig|fresh|mc|late|mr2|d128]   (no argument: all)
Prints one line per case: iterations, status (c converged, s stalled, o completed) and the true max error % of the
output for each variant, and writes data/contested.json and data/tables_contested.md. "orig" are the 11 cases
of the dead band sweep, "fresh" are held-out cases. Late-phase runs use unreachable tolerances (1e-6) with every
iteration recorded and the dead band set as for a max tolerance of 0.4 %.
"""

import json
import sys
import warnings
from pathlib import Path

import numpy as np
warnings.filterwarnings("ignore")
import carto_flow.flow_cartogram.algorithm as alg
import carto_flow.flow_cartogram.stepsize as ss
from carto_flow.flow_cartogram import CartogramWorkflow, morph_gdf
from make_figures import options_for, source, true_errors, ANISOTROPY

MODE = {"m": "off"}
_Base = ss.StepController

def factory(window, score, dead_band, enabled=True):
    m = MODE["m"]
    if isinstance(m, tuple) and m[0] == "cf":
        ss.CONTESTED_FRACTION = m[1]
        db = m[2] if len(m) > 2 else dead_band
    elif m == "fixed":
        db = 1e-3
    elif isinstance(m, tuple) and m[0] == "c":
        db = dead_band * m[1] / ss.DEAD_BAND_FRACTION
    elif isinstance(m, tuple) and m[0] == "abs":
        db = m[1]
    else:
        db = dead_band
    return _Base(window, score, db, enabled)

alg.StepController = factory
MODES = ["off", ("cf", 0.8), ("cf", 0.9), ("cf", 1.0)]
NAMES = ["constant", "cf 0.8", "cf 0.9", "cf 1.0"]

def adaptive_of(m):
    return m != "off"

def fresh(name, grid, dt, tol=None, rise=0.01):
    gdf = source(name); out = []
    for m in MODES:
        MODE["m"] = m
        o = options_for(name, adaptive_of(m), grid, dt, tol, recompute_on_rise=rise)
        r = morph_gdf(gdf, "Population", options=o)
        te = true_errors(r.get_geometry(), gdf["Population"]).max() * 100
        out.append((r.niterations, r.status.value[0], round(te, 2)))
    return out

def multires(name, tol):
    gdf = source(name); out = []
    for m in MODES:
        MODE["m"] = m
        o = options_for(name, adaptive_of(m), 256, 0.2, tol, n_iter=300)
        wf = CartogramWorkflow(gdf, "Population", options=o)
        wf.morph_multiresolution(min_resolution=128, levels=3)
        its = sum(r.niterations for r in wf.results[1:])
        te = true_errors(wf.last.get_geometry(), gdf["Population"]).max() * 100
        out.append((its, wf.last.status.value[0], round(te, 2)))
    return out

def cont(name, grid, first_tol, tol):
    gdf = source(name); out = []
    for m in MODES:
        MODE["m"] = m
        wf = CartogramWorkflow(gdf, "Population", options=options_for(name, adaptive_of(m), grid, 0.2, first_tol))
        wf.morph()
        r = wf.morph(options=options_for(name, adaptive_of(m), grid, 0.2, tol))
        te = true_errors(r.get_geometry(), gdf["Population"]).max() * 100
        out.append((r.niterations, r.status.value[0], round(te, 2)))
    return out

def late(name, grid, dt, rise, band_tol):
    gdf = source(name); v = gdf["Population"].to_numpy(float); out = []
    ab = ss.DEAD_BAND_FRACTION * np.log2(1 + band_tol)
    for m in ["off", ("cf", 0.8, ab), ("cf", 0.9, ab), ("cf", 1.0, ab)]:
        MODE["m"] = m
        o = options_for(name, m != "off", grid, dt, (1e-6, 1e-6), n_iter=300, stall_patience=None, snapshot_every=1, recompute_on_rise=rise)
        r = morph_gdf(gdf, "Population", options=o)
        t = np.array([true_errors(s.geometry, v).max() * 100 for s in r.snapshots.snapshots])[-50:]
        out.append((round(np.median(t), 3), round(t.max(), 3)))
    return out

rows = []
LATE_ROWS = []
LATE2 = []
GROUPS = {}
def add(label, res):
    rows.append((label, res))
    GROUPS.setdefault(which_now[0], []).append((label, res))
    print(f"{label:42s} " + " | ".join(f"{n} {r[0]}{r[1]} {r[2]}" for n, r in zip(NAMES, res)), flush=True)

HERE = Path(__file__).resolve().parent
which = sys.argv[1] if len(sys.argv) > 1 else "all"
which_now = [""]
which_now[0] = "held-out fresh runs"
if which in ("fresh", "all"):
    for a in ("horizontal", "tangential", "tilted"):
        for dt in (0.4, 0.8):
            add(f"{a} dt {dt}", fresh(a, 256, dt))
    add("states 128 dt .4 default", fresh("states", 128, 0.4))
    add("states 512 dt .4 default", fresh("states", 512, 0.4))
    add("districts 256 dt .2 default", fresh("districts", 256, 0.2))
    add("districts 256 dt .4 default", fresh("districts", 256, 0.4))
    for g in (128, 256):
        add(f"states {g} tol 1/2 dt .2", fresh("states", g, 0.2, (0.01, 0.02)))
        add(f"states {g} tol .1/.2 dt .2", fresh("states", g, 0.2, (0.001, 0.002)))
    add("states 256 tol .2/.4 dt .2 rise on", fresh("states", 256, 0.2, (0.002, 0.004)))
which_now[0] = "held-out multiresolution and continuation"
if which in ("mc", "all"):
    add("multires states .5/1", multires("states", (0.005, 0.01)))
    add("multires districts default", multires("districts", None))
    add("cont states 256 5/20 -> .5/1", cont("states", 256, (0.05, 0.2), (0.005, 0.01)))
    add("cont districts 256 5/20 -> .5/1", cont("districts", 256, (0.05, 0.2), (0.005, 0.01)))
if which in ("late", "all"):
    for rise in (0.01, None):
        for dt in (0.2, 0.4):
            r = late("states", 256, dt, rise, 0.004)
            LATE_ROWS.append(("states", dt, rise, r))
            print(f"late states dt {dt} rise {rise}: constant {r[0]} cf0.8 {r[1]} cf0.9 {r[2]} cf1.0 {r[3]}  (median, highest)", flush=True)
    r = late("districts", 256, 0.2, 0.01, 0.004)
    print(f"late districts dt .2 rise on: constant {r[0]} cf0.8 {r[1]} cf0.9 {r[2]} cf1.0 {r[3]}", flush=True)
which_now[0] = "original 11 cases"
if which in ("orig", "all"):
    add("states 256 default dt .2", fresh("states", 256, 0.2))
    add("states 256 default dt .4", fresh("states", 256, 0.4))
    for a in ("horizontal", "tangential", "tilted"):
        add(f"{a} dt .6", fresh(a, 256, 0.6))
    add("districts 128 default", fresh("districts", 128, 0.2))
    add("states 256 .2/.4 rise None dt .2", fresh("states", 256, 0.2, (0.002, 0.004), rise=None))
    add("states 256 .2/.4 dt .4", fresh("states", 256, 0.4, (0.002, 0.004)))
    add("states 256 .5/1 dt .2", fresh("states", 256, 0.2, (0.005, 0.01)))
    add("districts 256 .5/1 dt .2", fresh("districts", 256, 0.2, (0.005, 0.01)))
    add("states 512 .5/1 dt .2", fresh("states", 512, 0.2, (0.005, 0.01)))
    tot = [sum(r[1][i][0] for r in rows) for i in range(len(NAMES))]
    print("sum", dict(zip(NAMES, tot)))
if which == "late2":
    gdf = source("states"); v = gdf["Population"].to_numpy(float)
    for rise in (0.01, None):
        for dt in (0.2, 0.4):
            res = []
            for c in (0.01, 0.03, 0.1, 0.3):
                MODE["m"] = ("abs", c * np.log2(1.004))
                o = options_for("states", True, 256, dt, (1e-6, 1e-6), n_iter=300, stall_patience=None, snapshot_every=1, recompute_on_rise=rise)
                r = morph_gdf(gdf, "Population", options=o)
                t = np.array([true_errors(s.geometry, v).max() * 100 for s in r.snapshots.snapshots])[-50:]
                res.append(f"c{c}: {np.median(t):.2f}/{t.max():.2f}")
            LATE2.append((rise, dt, res))
            print(f"rise {rise} dt {dt} (median/highest, band for 0.4 %): " + " | ".join(res), flush=True)

which_now[0] = "districts, three more tolerances in a multiresolution run"
if which in ("mr2", "all"):
    for tol in ((0.01, 0.02), (0.005, 0.01), (0.002, 0.004)):
        add(f"multires districts {tol}", multires("districts", tol))
    add("multires states (0.002, 0.004)", multires("states", (0.002, 0.004)))

which_now[0] = "districts grid 128, single level, 4 tolerances x 4 dt"
if which in ("d128", "all"):
    for tol in (None, (0.01, 0.02), (0.005, 0.01), (0.002, 0.004)):
        for dt in (0.15, 0.2, 0.3, 0.4):
            add(f"districts 128 {tol or 'default'} dt {dt}", fresh("districts", 128, dt, tol))

out = {k: [(label, [list(r) for r in res]) for label, res in v] for k, v in GROUPS.items()}
(HERE / "data" / "contested.json").write_text(json.dumps({"names": NAMES, "groups": out, "late": [(a, b, c, [list(map(float, x)) for x in d]) for a, b, c, d in LATE_ROWS], "late2": LATE2}))
lines = []
for group, items in GROUPS.items():
    lines += [f"## {group}", "", "| case | " + " | ".join(NAMES) + " |", "|---|" + "---|" * len(NAMES)]
    for label, res in items:
        lines.append(f"| {label} | " + " | ".join(f"{r[0]} {r[1]}, {r[2]} %" for r in res) + " |")
    sums = [sum(res[i][0] for _, res in items) for i in range(len(NAMES))]
    lines += ["", "Sum of iterations: " + ", ".join(f"{n} {v}" for n, v in zip(NAMES, sums)), ""]
if LATE_ROWS:
    lines += ["## Late phase, states grid 256 (median, highest true max error % over the last 50 of 300 iterations)", "", "| dt | recompute_on_rise | constant | cf 0.8 (adopted) | cf 0.9 | cf 1.0 |", "|---|---|---|---|---|---|"]
    for _, dt, rise, r in LATE_ROWS:
        lines.append(f"| {dt} | {rise} | " + " | ".join(f"{float(x[0]):.2f} / {float(x[1]):.2f}" for x in r) + " |")
    lines.append("")
if LATE2:
    lines += ["## Late phase for the tied factor c (median / highest %)", "", "| recompute_on_rise | dt | c 0.01 | c 0.03 | c 0.1 | c 0.3 |", "|---|---|---|---|---|---|"]
    for rise, dt, res in LATE2:
        lines.append(f"| {rise} | {dt} | " + " | ".join(x.split(': ')[1] for x in res) + " |")
    lines.append("")
(HERE / "data" / "tables_contested.md").write_text("\n".join(lines) + "\n")
