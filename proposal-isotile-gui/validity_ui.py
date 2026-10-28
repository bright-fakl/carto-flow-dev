"""Validity feedback: how often the editor's inputs give an invalid prototile, what check_prototile reports, and the
cost of the repair strategies.

Part A  slider sweeps (the sliders are 0 to 1, step 0.01): per parameter, the invalid steps against safe_ranges.
Part B  vertex drags (what _on_vertex_change does: least squares on the Jacobian of info()["parameters"][i]["affected_vertices"],
        then clamp to [0, 1]): fraction of random drags that end in an invalid prototile.
Part C  the 17 curve presets of the editor (utils/symmetry.py get_curve_preset) applied to each curvable shape id of each type
        at the default parameters: fraction valid, per preset.
Part D  node drags on the 15 presets: random moves of one editable node; fraction invalid; bad_edges mapped to shape ids.
Part E  the same curve in both modes: valid in one and invalid in the other.
Part F  the repair strategies: revert to the last valid draft, and slide to the boundary by bisection (cost in ms, evaluations).
Part G  hairpin and fold-back examples of the isotile docs (valid hairpin, invalid fold-back at a join).

Run: python validity_ui.py > validity_ui.txt     (GUI_SRC set)
"""
from __future__ import annotations

import os
import statistics
import sys
import time

import numpy as np

sys.path.insert(0, os.environ["GUI_SRC"])
sys.path.insert(0, os.path.dirname(__file__))
import isotile  # noqa: E402
from isotile import IsohedralTiling as IT, check_prototile, enforce_symmetry, get_type, tiling_types  # noqa: E402
from isohedral_tiling_ui.utils.symmetry import get_curve_preset, list_curve_presets  # noqa: E402
import editor_model as em  # noqa: E402

rng = np.random.default_rng(11)
TYPES_P = [n for n in tiling_types() if get_type(n).n_params]

print("== A: slider sweeps, one parameter at a time, others at their defaults ==")
steps = invalid = 0
mismatch = 0
for n in TYPES_P:
    t = get_type(n)
    for k in range(t.n_params):
        lo, hi = t.safe_ranges[k]
        for v in np.arange(0.0, 1.0001, 0.01):
            p = t.default_params.copy()
            p[k] = v
            ok = check_prototile(n, p).valid
            steps += 1
            invalid += not ok
            inside = lo <= v <= hi
            if inside and not ok:
                mismatch += 1  # cannot happen: safe_range is the valid interval around the default
print(f"{steps} slider positions of {sum(get_type(n).n_params for n in TYPES_P)} parameters: {invalid} invalid ({100 * invalid / steps:.1f} %); "
      f"inside safe_range but invalid: {mismatch}")

print("\n== B: vertex drags from random valid states (Jacobian least squares as in _on_vertex_change, clamped to [0, 1]) ==")
total = bad = 0
by_sigma = {0.15: [0, 0], 0.5: [0, 0]}
for n in TYPES_P:
    t = get_type(n)
    info = IT(n).info()
    for sigma in by_sigma:
        for _ in range(100):
            while True:  # a random valid start in [0, 1]^k
                p = rng.uniform(0, 1, t.n_params)
                if check_prototile(n, p).valid:
                    break
            k = int(rng.integers(0, t.n_params))
            aff = info["parameters"][k]["affected_vertices"]
            if not aff:
                continue
            dv = rng.normal(0, sigma, 2)
            j = np.array([[a["dx_dp"], a["dy_dp"]] for a in aff])
            p[k] = np.clip(p[k] + float((j @ dv).sum() / max((j * j).sum(), 1e-12)), 0, 1)
            by_sigma[sigma][0] += 1
            by_sigma[sigma][1] += not check_prototile(n, p).valid
for sigma, (tot_, bad_) in by_sigma.items():
    print(f"displacement sigma {sigma}: {tot_} drags of one parameter from a random valid state, {bad_} end invalid ({100 * bad_ / tot_:.1f} %)")

print("\n== C: the 17 curve presets of the editor on every curvable shape id (default parameters) ==")
rows = []
for name in list_curve_presets():
    ok = tot = 0
    for n in tiling_types():
        t = get_type(n)
        for sid, shape in enumerate(t.shape_types):
            if shape == "I":
                continue
            c = enforce_symmetry(np.array(get_curve_preset(name), float), shape)
            tot += 1
            ok += check_prototile(n, edge_curves={sid: c}).valid
    rows.append((name, ok, tot))
for name, ok, tot in rows:
    print(f"  {name:22s} valid {ok:4d} of {tot} ({100 * ok / tot:5.1f} %)")
print(f"  all presets: valid {sum(r[1] for r in rows)} of {sum(r[2] for r in rows)}")

print("\n== D: random node drags on the 15 presets ==")
tot = bad = 0
nbad_ids = []
for name in isotile.list_presets():
    t = IT.from_preset(name)
    if not t.edge_curves:
        continue
    d = em.Draft.from_tiling(t)
    for _ in range(200):
        sid = int(rng.choice(sorted(d.curve_dict)))
        shape = em.shape_of(d.type_number, sid)
        c = d.curve(sid)
        cand = [i for i in range(len(c)) if em.editable(shape, len(c), i)]
        if not cand:
            continue
        i = int(rng.choice(cand))
        x, y = c[i][0] + rng.normal(0, 0.12), c[i][1] + rng.normal(0, 0.12)
        nd = d.with_curve(sid, em.move_node(c, shape, i, x, y))
        r = nd.report()
        tot += 1
        if not r.valid:
            bad += 1
            ids = {int(t.type.edge_shape_ids[e]) for e in r.bad_edges}
            nbad_ids.append(len(ids))
print(f"{tot} random single-node moves (sigma 0.12): {bad} invalid ({100 * bad / tot:.1f} %); shape ids named by bad_edges: median {statistics.median(nbad_ids)}, max {max(nbad_ids)}")

print("\n== E: valid in one mode, invalid in the other ==")
found = {"spline_ok_linear_bad": None, "linear_ok_spline_bad": None}
for _ in range(4000):
    n = int(rng.choice(tiling_types()))
    t = get_type(n)
    ids = [s for s, sh in enumerate(t.shape_types) if sh != "I"]
    if not ids:
        continue
    sid = ids[0]
    m = int(rng.integers(4, 9))
    pts = np.column_stack([np.sort(rng.uniform(0, 1, m)), rng.normal(0, 0.25, m)])
    pts[0], pts[-1] = (0, 0), (1, 0)
    c = enforce_symmetry(pts, t.shape_types[sid])
    a = check_prototile(n, edge_curves={sid: c}, edge_curve_modes={sid: "spline"}).valid
    b = check_prototile(n, edge_curves={sid: c}, edge_curve_modes={sid: "linear"}).valid
    if a and not b and found["spline_ok_linear_bad"] is None:
        found["spline_ok_linear_bad"] = (n, sid, c.round(3).tolist())
    if b and not a and found["linear_ok_spline_bad"] is None:
        found["linear_ok_spline_bad"] = (n, sid, c.round(3).tolist())
for k, v in found.items():
    print(f"  {k}: {v}")

print("\n== F: repair strategies for an invalid node move ==")
revert_ms, slide_ms, slide_evals, found_ok = [], [], [], 0
n_try = 0
for name in isotile.list_presets():
    t = IT.from_preset(name)
    if not t.edge_curves:
        continue
    d0 = em.Draft.from_tiling(t)
    for _ in range(150):
        sid = int(rng.choice(sorted(d0.curve_dict)))
        shape = em.shape_of(d0.type_number, sid)
        c = d0.curve(sid)
        cand = [i for i in range(len(c)) if em.editable(shape, len(c), i)]
        if not cand:
            continue
        i = int(rng.choice(cand))
        x, y = c[i][0] + rng.normal(0, 0.3), c[i][1] + rng.normal(0, 0.3)
        t0 = time.perf_counter()
        nd = d0.with_curve(sid, em.move_node(c, shape, i, x, y))
        valid = nd.report().valid
        revert_ms.append((time.perf_counter() - t0) * 1000)
        if valid:
            continue
        n_try += 1
        # slide: bisection on the segment from the old node to the dragged node
        t0 = time.perf_counter()
        lo, hi, evals = 0.0, 1.0, 0
        for _ in range(12):
            mid = (lo + hi) / 2
            cand_d = d0.with_curve(sid, em.move_node(c, shape, i, c[i][0] + mid * (x - c[i][0]), c[i][1] + mid * (y - c[i][1])))
            evals += 1
            if cand_d.report().valid:
                lo = mid
            else:
                hi = mid
        slide_ms.append((time.perf_counter() - t0) * 1000)
        slide_evals.append(evals)
        found_ok += lo > 0
print(f"  revert (one check): median {statistics.median(revert_ms):.2f} ms")
print(f"  slide to the boundary (12 bisection steps, {n_try} invalid moves): median {statistics.median(slide_ms):.1f} ms, max {max(slide_ms):.1f} ms; "
      f"a valid point other than the start found in {found_ok} of {n_try}")

print("\n== G: hairpin and fold-back (docs/curves.md) ==")
cases = {
    "hairpin, arms 0.1 apart (finger)": [(0, 0), (0.3, 0.0), (0.4, 0.5), (0.5, 0.5), (0.6, 0.0), (0.7, 0), (1, 0)],
    "hairpin, arms 0.001 apart": [(0, 0), (0.3, 0.0), (0.499, 0.5), (0.501, 0.5), (0.7, 0), (1, 0)],
    "arms 1e-7 apart (below the clearance)": [(0, 0), (0.3, 0.0), (0.4999999, 0.5), (0.5000001, 0.5), (0.7, 0), (1, 0)],
    "fold-back at a join (180 degree turn on a line)": [(0, 0), (0.6, 0.0), (0.3, 0.0), (1, 0)],
    "bow tie (crossing)": [(0, 0), (0.8, 0.5), (0.2, 0.5), (1, 0)],
}
for label, c in cases.items():
    for mode in ("spline", "linear"):
        r = check_prototile(41, edge_curves={0: c}, edge_curve_modes={0: mode})
        print(f"  {label:48s} {mode:6s} valid={r.valid!s:5} bad_edges={r.bad_edges} {r.message}")
