"""Markdown tables for summary.md from data/*.jsonl|json. Usage: python tables.py <table-name>"""

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

D = Path(__file__).resolve().parent.parent / "data"
NAMES = {
    "base": "constant dt",
    "A_r3_m0.05": "A ref 3",
    "A_r10_m0.05": "A ref 10",
    "A_r30_m0.05": "A ref 30",
    "B_0.05": "B 5 %",
    "B_0.1": "B 10 %",
    "C_r3": "C ref 3",
    "C_r10": "C ref 10",
    "AB_r10_f0.05": "A ref 10 + B 5 %",
}


def rows(*names):
    out = []
    for n in names:
        out += [json.loads(line) for line in open(D / n)]
    return out


def md(header, body):
    return "\n".join(["| " + " | ".join(header) + " |", "|" + "---|" * len(header)] + ["| " + " | ".join(map(str, r)) + " |" for r in body])


def spikes():
    rs = rows("grid_cheap.jsonl")
    out = []
    for case, dt in (("states_t", 0.2), ("horiz", 0.6), ("tang", 0.6), ("tilt", 0.6), ("districts", 0.6)):
        for rr in ("off", "on"):
            for v in NAMES:
                m = [r for r in rs if (r["case"], r["dt"], r["R"], r["rr"], r["variant"]) == (case, dt, 10, rr, v)]
                if m:
                    r = m[0]
                    out.append([case, dt, rr, NAMES[v], r["status"], r["it"], r["rec"], r["rises20"], f"{r['spike']:.2f}", f"{r['final'] / r['best']:.1f}", f"{r['out_max']:.1f}", f"{r['cost']:.0f}"])
    return md(["case", "dt", "refresh on rise", "controller", "status", "it", "rec", "rises (score<20)", "max rise factor", "final/best score", "max err % (output)", "cost"], out)


def accuracy(dt=0.2, R=10, rr="on"):
    rs = rows("grid_cheap.jsonl", "grid_counties.jsonl")
    out = []
    for case in ("states", "states_t", "districts", "horiz", "tang", "tilt", "counties"):
        for v in ("base", "A_r3_m0.05", "A_r10_m0.05", "B_0.1", "AB_r10_f0.05"):
            m = [r for r in rs if (r["case"], r["dt"], r["R"], r["rr"], r["variant"]) == (case, dt, R, rr, v)]
            if m:
                r = m[0]
                out.append([case, NAMES[v], r["status"], r["it"], f"{r['lib_mean']:.2f} / {r['lib_max']:.1f}", f"{r['out_mean']:.2f} / {r['out_max']:.1f}", f"{r['out_share10']:.1f}", f"{r['best']:.2f}"])
    return md(["case", "controller", "status", "it", "library mean / max %", "output mean / max %", "share above 10 %", "best score"], out)


def robustness():
    rs = rows("grid_cheap.jsonl")
    g = defaultdict(list)
    for r in rs:
        g[(r["variant"], r["rr"], r["R"])].append(r)
    base = {(r["case"], r["dt"], r["R"], r["rr"]): r for r in rs if r["variant"] == "base"}
    out = []
    for (v, rr, R), x in sorted(g.items(), key=lambda kv: (list(NAMES).index(kv[0][0]), kv[0][1], -kv[0][2])):
        c = defaultdict(int)
        for r in x:
            c[r["cls"]] += 1
        conv = [r for r in x if r["cls"] == "converged"]
        both = [(r, base[(r["case"], r["dt"], R, rr)]) for r in conv if base[(r["case"], r["dt"], R, rr)]["cls"] == "converged"]
        ratio_it = f"{np.median([a['it'] / b['it'] for a, b in both]):.2f}" if both else "-"
        ratio_c = f"{np.median([a['cost'] / b['cost'] for a, b in both]):.2f}" if both else "-"
        out.append([NAMES[v], rr, R, len(x), c["converged"], c["stalled"], c["diverged"], c["incomplete"], f"{np.median([r['it'] for r in conv]):.0f}" if conv else "-", ratio_it, ratio_c, f"{np.sum([r['rises20'] for r in x]) / len(x):.1f}"])
    return md(["controller", "refresh on rise", "recompute_every", "runs", "converged", "stalled", "diverged", "incomplete", "median it (conv)", "it ratio to constant dt (both conv)", "cost ratio (both conv)", "mean rises below score 20"], out)


def bydt():
    rs = rows("grid_cheap.jsonl")
    dts = sorted({r["dt"] for r in rs})
    out = []
    for rr in ("off", "on"):
        for v in NAMES:
            if not any(r["variant"] == v for r in rs):
                continue
            row = [NAMES[v], rr]
            for dt in dts:
                x = [r for r in rs if r["variant"] == v and r["rr"] == rr and r["dt"] == dt]
                row.append(f"{sum(r['cls'] == 'converged' for r in x)}/{len(x)}")
            out.append(row)
    return md(["controller", "refresh on rise"] + [f"dt {d}" for d in dts], out)


def counties():
    rs = rows("grid_counties.jsonl")
    out = []
    for v in NAMES:
        for rr in ("off", "on"):
            x = [r for r in rs if r["variant"] == v and r["rr"] == rr]
            if not x:
                continue
            c = defaultdict(int)
            for r in x:
                c[r["cls"]] += 1
            out.append([NAMES[v], rr, len(x), c["converged"], c["stalled"], c["diverged"], c["incomplete"], f"{np.median([r['best'] for r in x]):.1f}", f"{np.median([r['out_mean'] for r in x]):.0f}", f"{np.median([r['cost'] for r in x]):.0f}"])
    return md(["controller", "refresh on rise", "runs", "conv", "stall", "div", "incompl", "median best score", "median output mean err %", "median cost"], out)


def restart():
    rs = json.load(open(D / "restart.json"))
    out = []
    for case, grid in sorted({(r["case"], r["grid"]) for r in rs}):
        for kind in ("conv", "loose", "stall"):
            for rr in ("on", "off"):
                for v in ("base", "A_r3_m0.05", "A_r10_m0.05", "C_r10", "B_0.1", "AB_r10_f0.05"):
                    m = [r for r in rs if (r["case"], r["grid"], r["kind"], r["rr"], r["variant"]) == (case, grid, kind, rr, v)]
                    if m:
                        r = m[0]
                        out.append([case, grid, kind, f"{r['start_best']:.2f}", rr, NAMES[v], r["cls"], r["it"], r["rec"], f"{r['s0']:.1f}", f"{r['first5_max']:.1f}", f"{r['out_max']:.2f}", f"{r['cost']:.0f}"])
    return md(["case", "grid", "start", "start score", "refresh on rise", "controller", "result", "it", "rec", "score after it 1", "max score in it 1-5", "output max err %", "cost"], out)


def restart_summary():
    rs = json.load(open(D / "restart.json"))
    out = []
    for kind in ("conv", "loose", "stall"):
        for rr in ("on", "off"):
            for v in ("base", "A_r3_m0.05", "A_r10_m0.05", "A_r30_m0.05", "C_r3", "C_r10", "B_0.1", "AB_r10_f0.05"):
                x = [r for r in rs if r["kind"] == kind and r["rr"] == rr and r["variant"] == v]
                c = sum(r["cls"] == "converged" for r in x)
                out.append([kind, rr, NAMES[v], f"{c}/{len(x)}", f"{np.median([r['it'] for r in x]):.0f}", f"{np.median([r['cost'] for r in x]):.0f}", f"{np.median([r['s0'] for r in x]):.1f}", f"{np.median([r['first5_max'] for r in x]):.1f}"])
    return md(["start", "refresh on rise", "controller", "converged", "median it", "median cost", "median score after it 1", "median max score in it 1-5"], out)


def multires():
    rs = rows("multires.jsonl")
    out = []
    for case in ("states", "districts", "states_t"):
        for stall in (4, None):
            for rr in ("on", "off"):
                for dt in (0.2, 0.4):
                    for v in ("base", "A_r3_m0.05", "A_r10_m0.05", "A_r30_m0.05", "B_0.1", "C_r10", "AB_r10_f0.05"):
                        m = [r for r in rs if (r["case"], r["stall"], r["rr"], r["dt"], r["variant"]) == (case, stall, rr, dt, v)]
                        if m:
                            r = m[0]
                            lv = ", ".join(f"{x['grid']}: {x['status'][:4]} {x['it']}" for x in r["levels"])
                            out.append([case, stall, rr, dt, NAMES[v], r["final"], r["it"], r["rec"], f"{r['cost']:.0f}", f"{r['out_max']:.1f}", lv])
    return md(["case", "stall_patience", "refresh on rise", "dt", "controller", "final", "it", "rec", "cost", "output max err %", "levels (grid: status iterations)"], out)


def multires_summary():
    rs = rows("multires.jsonl")
    out = []
    for case in ("states", "districts", "states_t"):
        for stall in (4, None):
            for rr in ("on", "off"):
                for v in ("base", "A_r3_m0.05", "A_r10_m0.05", "A_r30_m0.05", "B_0.1", "C_r10", "AB_r10_f0.05"):
                    x = [r for r in rs if (r["case"], r["stall"], r["rr"], r["variant"]) == (case, stall, rr, v)]
                    if x:
                        out.append([case, stall, rr, NAMES[v], f"{sum(r['final'] == 'converged' for r in x)}/{len(x)}", f"{np.mean([r['cost'] for r in x]):.0f}", f"{np.mean([len(r['levels']) for r in x]):.1f}", f"{np.mean([r['out_max'] for r in x]):.1f}"])
    return md(["case", "stall_patience", "refresh on rise", "controller", "converged", "mean cost (dt 0.2 and 0.4)", "mean levels run", "mean output max err %"], out)


def stall():
    rs = rows("stall.jsonl")
    ref = {(r["case"], r["dt"], r["rr"], r["variant"]): r for r in rs if r["tag"] == "None"}
    out = []
    for v in ("base", "A_r10_m0.05", "B_0.1", "AB_r10_f0.05"):
        for rr in ("on", "off"):
            for p in ("None", "4", "2", "1"):
                x = [r for r in rs if r["variant"] == v and r["rr"] == rr and r["tag"] == p]
                conv_ref = [r for r in x if ref[(r["case"], r["dt"], r["rr"], r["variant"])]["cls"] == "converged"]
                false = [r for r in conv_ref if r["cls"] != "converged"]
                hopeless = [r for r in x if ref[(r["case"], r["dt"], r["rr"], r["variant"])]["cls"] != "converged"]
                saved = np.mean([1 - r["it"] / ref[(r["case"], r["dt"], r["rr"], r["variant"])]["it"] for r in hopeless]) if hopeless else float("nan")
                out.append([NAMES[v], rr, p, len(x), f"{sum(r['cls'] == 'converged' for r in x)}", len(false), len(hopeless), f"{100 * saved:.0f} %" if hopeless else "-", f"{np.median([r['out_max'] for r in x]):.1f}"])
    return md(["controller", "refresh on rise", "stall_patience", "runs", "converged", "false stalls (reference converges)", "runs where the reference does not converge", "iterations saved on those", "median output max err %"], out)


if __name__ == "__main__":
    print(globals()[sys.argv[1]](*[float(a) if "." in a else a for a in sys.argv[2:]]))
