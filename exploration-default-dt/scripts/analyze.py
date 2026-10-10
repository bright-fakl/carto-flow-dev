"""Builds ../data/tables.md from the jsonl files and shape.json (plain python, no carto_flow import)."""
import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
RATIO = {("states", 128): 9, ("states", 256): 12, ("states", 512): 24, ("states", 1024): 71,
         ("districts", 128): 18, ("districts", 256): 21, ("districts", 512): 23, ("districts", 1024): 47,
         ("counties", 128): 21, ("counties", 256): 47.5, ("counties", 512): 28.5}
BASE = {"horiz": "states", "tang": "states", "tilt": "states", "states_mr": "states"}
DTS = [0.2, 0.3, 0.4, 0.5, 0.6, 0.8]


def load_runs():
    runs = []
    for f in sorted(glob.glob(os.path.join(DATA, "*.jsonl"))):
        name = os.path.basename(f)[:-6]
        if name in ("pipeline", "presets", "landmarks"):
            continue
        for l in open(f):
            r = json.loads(l)
            ratio = RATIO.get((BASE.get(r["case"], r["case"]), r["grid"]))
            r["cost"] = None if ratio is None else r["it"] + r["rec"] * ratio
            r["key"] = f"{r['case']}|{r['grid']}|{r['dt']}|{r['rr']}|{r['rre']}|{int(r['tight'])}"
            runs.append(r)
    return {r["key"]: r for r in runs}


def reliab(r):
    return {"converged": "C", "stall_patience": "S", "iteration_limit": "L"}.get(r["stop"], r["stop"])


def main():
    runs = load_runs()
    shape = json.load(open(os.path.join(DATA, "shape.json"))) if os.path.exists(os.path.join(DATA, "shape.json")) else {}
    out = []

    def table(title, case, grid, rr, rre=10, tight=False, dts=None):
        out.append(f"### {title}\n")
        out.append("| dt | status | it | rec | cost | wall s | mean % | max % | >10 % | invalid (self-int.) | rises<20 | spike | symdiff % | vertex shift (cells) | centroids >0.5 cell |")
        out.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        ref = runs.get(f"{case}|{grid}|0.2|{rr}|{rre}|{int(tight)}")
        all_dts = sorted({r["dt"] for r in runs.values() if (r["case"], r["grid"], r["rr"], r["rre"], r["tight"]) == (case, grid, rr, rre, tight)})
        for dt in (dts or all_dts):
            k = f"{case}|{grid}|{dt}|{rr}|{rre}|{int(tight)}"
            r = runs.get(k)
            if r is None:
                continue
            s = shape.get(k)
            cost = "" if r["cost"] is None else f"{r['cost']:.0f}"
            rel = "" if (r["cost"] is None or ref is None) else f" ({r['cost'] / ref['cost']:.2f}x)"
            sh = f"{100 * s['symdiff']:.2f} | {s['vdisp_mean']:.2f} / {s['vdisp_max']:.1f} | {s['cent_gt05']}" if s else "- | - | -"
            out.append(f"| {dt} | {reliab(r)} | {r['it']} | {r['rec']} | {cost}{rel} | {r['wall']:.1f} | {100 * r['mean']:.2f} | {100 * r['max']:.1f} | {100 * r['gt10']:.0f} | {r['invalid']} ({r['selfint']}) | {r['rises20']} | {r['spike']:.1f} | {sh} |")
        out.append("")

    for case, grids in (("states", (128, 256, 512, 1024)), ("districts", (256, 512)), ("horiz", (256,)), ("tang", (256,)), ("tilt", (256,)), ("counties", (256,))):
        for grid in grids:
            table(f"{case} grid {grid}, refresh_on_rise 0.01, recompute_every 10", case, grid, 0.01)
    table("states_mr (coarse level, min_resolution 128), refresh_on_rise 0.01", "states_mr", 128, 0.01)
    table("states_mr (coarse level), refresh_on_rise off", "states_mr", 128, None)
    for case in ("states", "districts"):
        table(f"{case} grid 256, tight tolerances (0.5 % / 1 %), refresh_on_rise 0.01", case, 256, 0.01, tight=True)
    table("states grid 256, tight tolerances, refresh off", "states", 256, None, tight=True, dts=[0.2, 0.4, 0.6])
    for case in ("states", "districts", "horiz", "tang", "tilt"):
        table(f"{case} grid 256, refresh_on_rise 0.2", case, 256, 0.2)
        table(f"{case} grid 256, refresh_on_rise off", case, 256, None)
    table("states grid 512, refresh off", "states", 512, None, dts=[0.2, 0.4, 0.6])
    # (dt, recompute_every) grid
    out.append("### (dt, recompute_every), refresh_on_rise 0.01, grid 256: cost (iterations / recomputes / invalid / status)\n")
    pairs = [(0.2, 5), (0.2, 10), (0.2, 20), (0.4, 5), (0.4, 10), (0.4, 20), (0.6, 5), (0.6, 10), (0.6, 20), (0.8, 5), (0.8, 10)]
    out.append("| case | " + " | ".join(f"({a}, {b})" for a, b in pairs) + " |")
    out.append("|---|" + "---|" * len(pairs))
    for case in ("states", "districts", "horiz", "tang", "tilt"):
        cells = []
        for dt, rre in pairs:
            r = runs.get(f"{case}|256|{dt}|0.01|{rre}|0")
            cells.append("-" if r is None else f"{r['cost']:.0f} ({r['it']}/{r['rec']}/{r['invalid']}/{reliab(r)})")
        out.append(f"| {case} | " + " | ".join(cells) + " |")
    out.append("")
    # pipeline, presets, landmarks
    p = os.path.join(DATA, "pipeline.jsonl")
    if os.path.exists(p):
        out.append("### morph_multiresolution(min_resolution=128, levels=3), default options, n_iter 300 per level\n")
        out.append("| case | refresh | dt | it | rec | cost | levels (grid status it) | mean % | max % | invalid | symdiff vs 0.2 % | vertex shift (cells) |")
        out.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
        for l in open(p):
            r = json.loads(l)
            s = shape.get(r["_key"])
            lv = "; ".join(f"{x['grid']} {x['status'][:4]} {x['it']}" for x in r["levels"])
            sh = f"{100 * s['symdiff']:.2f} | {s['vdisp_mean']:.2f}" if s else "- | -"
            out.append(f"| {r['case']} | {r['rr']} | {r['dt']} | {r['it']} | {r['rec']} | {r['cost']:.0f} | {lv} | {100 * r['mean']:.2f} | {100 * r['max']:.1f} | {r['invalid']} | {sh} |")
        out.append("")
    p = os.path.join(DATA, "presets.jsonl")
    if os.path.exists(p):
        out.append("### Presets (area_scale 1, defaults otherwise, preset grid_size / n_iter / tolerances)\n")
        out.append("| case | preset | dt (preset's own: *) | grid | n_iter | tols | status | it | rec | cost | mean % | max % | invalid |")
        out.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        for l in open(p):
            r = json.loads(l)
            own = "*" if abs(r["dt"] - r["preset_dt"]) < 1e-9 else ""
            cost = "" if r["cost"] is None else f"{r['cost']:.0f}"
            ratio = RATIO.get((r["case"], r["grid"]))
            cost = "" if ratio is None else f"{r['it'] + r['rec'] * ratio:.0f}"
            out.append(f"| {r['case']} | {r['preset']} | {r['dt']}{own} | {r['grid']} | {r['n_iter_set']} | {r['mean_tol_set']}/{r['max_tol_set']} | {reliab(r)} | {r['it']} | {r['rec']} | {cost} | {100 * r['mean']:.2f} | {100 * r['max']:.1f} | {r['invalid']} |")
        out.append("")
    p = os.path.join(DATA, "landmarks.jsonl")
    if os.path.exists(p):
        rows = [json.loads(l) for l in open(p)]
        out.append("### Landmarks (issue 86): border-band z over 5 dot seeds (7 to 11), preset_balanced, area_scale 1e-6, snapshot_every 1\n")
        out.append("| dt | recompute_every (dt x rre = nominal cells per cycle) | seeds | status (C/S/L) | it (mean) | frames | z start (mean) | z end per seed | z end mean | max displacement per iteration (cells; map fraction) | mean of per-iteration max (cells) | dots inside own state |")
        out.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
        combos = sorted({(r["dt"], r["rre"]) for r in rows}, key=lambda x: (x[0] * x[1], x[0]))
        for dt, rre in combos:
            if True:
                rs = [r for r in rows if r["dt"] == dt and r["rre"] == rre]
                zs = [r["z"] for r in rs]
                st = "".join({"converged": "C", "stalled": "S"}.get(r["status"], "L") for r in rs)
                out.append(f"| {dt} | {rre} ({dt * rre:.1f}) | {len(rs)} | {st} | {sum(r['it'] for r in rs) / len(rs):.0f} | {sum(r['frames'] for r in rs) / len(rs):.0f} | {sum(r['z_start'] for r in rs) / len(rs):.2f} | {' '.join(f'{z:+.1f}' for z in zs)} | {sum(zs) / len(zs):+.2f} | {max(r['max_disp_cells'] for r in rs):.2f}; {max(r['max_disp_frac'] for r in rs):.4f} | {sum(r['mean_max_disp_cells'] for r in rs) / len(rs):.2f} | {min(r['inside'] for r in rs):.3f} |")
        out.append("")
    open(os.path.join(DATA, "tables.md"), "w").write("\n".join(out))
    print("\n".join(out))


if __name__ == "__main__":
    main()
