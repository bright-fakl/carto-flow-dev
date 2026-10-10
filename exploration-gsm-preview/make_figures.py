"""Convergence-trace figures and summary tables from data/*.json (written by scripts/run_case.py).

usage: uv run python make_figures.py   (needs matplotlib and numpy only)
"""
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")
RATIO = {("states", 128): 9.2, ("states", 256): 12.0, ("districts", 256): 20.9, ("counties", 256): 47.5}
COL = {"base": "#1f77b4", "blur0": "#7f7f7f", "blur1": "#ff7f0e", "blur2": "#2ca02c", "blur4": "#d62728", "blur8": "#9467bd",
       "blur1_fix4": "#8c564b", "blur1_fix8": "#e377c2", "blur1_fix16": "#bcbd22", "blur1_fix32": "#17becf"}
TITLE = {"states_256": "US states (49), grid 256", "states_128": "US states (49), grid 128",
         "states_mr_128": "States, multiresolution coarse level (grid 128 x 89)", "districts_256": "Congressional districts (432), grid 256",
         "counties_256": "Counties (3,108), grid 256", "horiz_256": "States, horizontal anisotropy, grid 256",
         "tang_256": "States, tangential anisotropy, grid 256", "tilt_256": "States, tilted anisotropy, grid 256"}


def load(name):
    p = os.path.join(D, f"{name}.json")
    return json.load(open(p)) if os.path.exists(p) else None


def ratio(r):
    base = {"states_mr": "states", "horiz": "states", "tang": "states", "tilt": "states"}.get(r["case"], r["case"])
    return RATIO.get((base, r["grid"]), r["baseline"].get("ratio") or 12.0)


def gsm_cost(tr, rt):
    """Cumulative cost per pass in plain-step units: passes * ratio + vertex-velocity evaluations."""
    return np.array([p["p"] * rt + sum(q["evals"] for q in tr[: i + 1]) for i, p in enumerate(tr)])


def first_below(vals, thr=1.0):
    for i, v in enumerate(vals):
        if v < thr:
            return i
    return None


def panel_set(axs, name, r):
    rt = ratio(r)
    b = r["baseline"]
    s = np.array(b["score"])
    ax = axs[0]
    ax.plot(np.arange(len(s)), s, color=COL["base"], lw=1.4)
    ax.set_title("baseline (stall rule + refresh on rise)", fontsize=9)
    ax.set_xlabel("iteration")
    ax = axs[1]
    for k, v in r["gsm"].items():
        if "fix" in k:
            continue
        tr = v["trace"]
        ax.plot([t["p"] for t in tr], [max(t["score"], 1e-3) for t in tr], marker="o", ms=3, lw=1.2, color=COL.get(k), label=k.replace("blur", "blur0=") + " cells")
    ax.set_title("GSM-style prototype", fontsize=9)
    ax.set_xlabel("pass")
    ax.legend(fontsize=7, loc="upper right")
    ax = axs[2]
    it = len(s)
    cost_b = (np.arange(it) + 1) * (1 + b["rec"] / max(it, 1) * rt)
    ax.plot(cost_b, s, color=COL["base"], lw=1.4, label="baseline")
    for k, v in r["gsm"].items():
        if "fix" in k:
            continue
        tr = v["trace"]
        ax.plot(gsm_cost(tr, rt)[1:], [max(t["score"], 1e-3) for t in tr][1:], marker="o", ms=3, lw=1.2, color=COL.get(k), label=k)
    ax.set_xscale("log")
    ax.set_title("score versus cost (plain-step units)", fontsize=9)
    ax.set_xlabel("cost (plain-step units)")
    for ax in axs:
        ax.set_yscale("log")
        ax.axhline(1, color="k", ls="--", lw=0.8)
        ax.grid(alpha=0.25, lw=0.4)
        ax.tick_params(labelsize=8)
    axs[0].set_ylabel("score (below 1 = converged)")


def figure(names, fname, suptitle):
    rows = [(n, load(n)) for n in names]
    rows = [(n, r) for n, r in rows if r]
    if not rows:
        return
    fig, axs = plt.subplots(len(rows), 3, figsize=(13, 3.3 * len(rows)), squeeze=False)
    for i, (n, r) in enumerate(rows):
        panel_set(axs[i], n, r)
        axs[i][0].annotate(TITLE[n], xy=(0, 1.22), xycoords="axes fraction", fontsize=10, weight="bold")
    fig.suptitle(suptitle, y=1.0, fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(os.path.join(HERE, fname), dpi=110)
    plt.close(fig)


def sensitivity(names, fname):
    rows = [(n, load(n)) for n in names]
    rows = [(n, r) for n, r in rows if r]
    fig, axs = plt.subplots(len(rows), 2, figsize=(10, 3.2 * len(rows)), squeeze=False)
    for i, (n, r) in enumerate(rows):
        for k, v in r["gsm"].items():
            tr = v["trace"]
            ax = axs[i][0] if "fix" not in k else axs[i][1]
            ax.plot([t["p"] for t in tr], [max(t["score"], 1e-3) for t in tr], marker="o", ms=3, lw=1.2, color=COL.get(k),
                    label=k.replace("blur1_fix", "fixed ").replace("blur", "blur0=") if "fix" in k else k.replace("blur", "blur0="))
        axs[i][0].set_title(TITLE[n] + ": blur (adaptive steps)", fontsize=9)
        axs[i][1].set_title(TITLE[n] + ": fixed number of steps per pass (blur0=1)", fontsize=9)
        for ax in axs[i]:
            ax.set_yscale("log"); ax.axhline(1, color="k", ls="--", lw=0.8); ax.grid(alpha=0.25, lw=0.4)
            ax.legend(fontsize=7); ax.set_xlabel("pass"); ax.set_ylabel("score")
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, fname), dpi=110)
    plt.close(fig)


def tables():
    out = []
    names = ["states_256", "states_128", "states_mr_128", "districts_256", "counties_256", "horiz_256", "tang_256", "tilt_256"]
    out.append("| case | variant | passes / iter | velocity fields | rasterizations | evals | cost (plain steps) | wall s | mean % | max % | >10 % | invalid (self-int.) | status / first pass below 1 | cost to first <1 | wall s to first <1 | load |")
    out.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for n in names:
        r = load(n)
        if not r:
            continue
        rt = ratio(r)
        b = r["baseline"]
        f = b["final"]
        cost = b["it"] + b["rec"] * rt
        out.append(f"| {n} | baseline | {b['it']} | {b['rec']} | {b['rast']} | - | {cost:.0f} | {b['wall']:.2f} | {100*f['mean']:.2f} | {100*f['max']:.1f} | {100*f['gt10']:.0f} % | {f['invalid']} ({f['selfint']}) | {b['status']} | {cost:.0f} | {b['wall']:.2f} | {b['load']} |")
        for k, v in r["gsm"].items():
            tr = v["trace"]
            sc = [t["score"] for t in tr]
            fp = first_below(sc)
            last = tr[-1]
            P = v["passes"]
            cost = P * rt + v["evals"]
            note = f"first <1 at pass {fp}" if fp is not None else "never <1"
            c1 = f"{fp * rt + sum(q['evals'] for q in tr[: fp + 1]):.0f}" if fp is not None else "-"
            w1 = f"{tr[fp]['wall']:.1f}" if fp is not None else "-"
            out.append(f"| {n} | {k} | {P} | {P} | {P} | {v['evals']} | {cost:.0f} | {v['wall']:.1f} | {100*last['mean']:.2f} | {100*last['max']:.1f} | {100*last['gt10']:.0f} % | {last['invalid']} ({last['selfint']}) | {note} | {c1} | {w1} | {v['load']} |")
    return "\n".join(out)


def monotonic(r, k):
    sc = [t["score"] for t in r["gsm"][k]["trace"]]
    return int(sum(b > a * 1.001 for a, b in zip(sc[:-1], sc[1:])))


if __name__ == "__main__":
    figure(["states_256", "states_128", "states_mr_128"], "convergence_states.png", "States: baseline versus GSM-style prototype (score below 1 = converged, dashed)")
    figure(["districts_256", "counties_256"], "convergence_districts_counties.png", "Districts and counties: baseline versus GSM-style prototype")
    figure(["horiz_256", "tang_256", "tilt_256"], "convergence_anisotropy.png", "Strong anisotropy (velocity modulator applied to the per-pass velocity field)")
    sensitivity(["states_256", "districts_256"], "sensitivity.png")
    t = tables()
    open(os.path.join(HERE, "tables.md"), "w").write(t + "\n")
    print(t)
    for n in ("states_256", "states_128", "states_mr_128", "districts_256", "counties_256"):
        r = load(n)
        if r:
            print(n, "score rises (>0.1 %) per variant:", {k: monotonic(r, k) for k in r["gsm"]},
                  "baseline rises:", int(sum(b > a * 1.001 for a, b in zip(r["baseline"]["score"][:-1], r["baseline"]["score"][1:]))),
                  "dc_err gsm:", {k: (None if v.get("dc_err") is None else round(v["dc_err"], 3)) for k, v in r["gsm"].items()}, "dc base:", r["baseline"].get("dc_err"))
