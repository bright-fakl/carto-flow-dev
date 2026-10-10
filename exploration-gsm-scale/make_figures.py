"""Convergence plots and tables for the GSM step-scale experiment.

Reads data/<case>_<grid>[_dt<dt>].json (written by scripts/run_case.py on investigate/gsm-scale) and writes
convergence_states.png, convergence_anisotropy.png, convergence_districts_counties.png and tables.md
next to this file. Runs with `uv run python make_figures.py`. The score is max(mean/mean_tol, max/max_tol) on the
log2 errors; below 1 is converged. Top row of each figure: refresh_on_rise off; bottom row: on (0.01).
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
SURFACE, INK, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e1"
STYLE = {
    "A": ("A constant (current)", "#2a78d6"),
    "B1": ("B1 GSM pattern, normalized", "#1baf7a"),
    "B2": ("B2 GSM physical, cap 1 cell", "#eda100"),
    "B4n": ("B4 integral, normalized", "#eb6834"),
    "B4s": ("B4 integral, physical sub-steps, cap 1", "#e87ba4"),
    "B4oc": ("B4 integral, one step per round, cap 3", "#7a5ec9"),
}
LABELS = {"A": "A constant", "B1": "B1 gsm_normalized (floor 0.02)", "B1f01": "B1 floor 0.01", "B1f10": "B1 floor 0.1",
          "B3n": "B3 precomputed B1", "B2": "B2 gsm_physical (cap 1 cell)", "B2c3": "B2 cap 3 cells", "B2nc": "B2 no cap",
          "B3p": "B3 precomputed B2", "B4n": "B4ii integral normalized", "B4s": "B4ii integral physical (cap 1)",
          "B4snc": "B4ii integral physical, no cap", "B4o": "B4i one step per round, no cap", "B4oc": "B4i one step per round (cap 3)"}
LABELS.update({"C1": "C1 physical, constant scale (cap 1)", "C2": "C2 pattern at A's step, floor 0.02", "C2f10": "C2 floor 0.1",
               "C2f50": "C2 floor 0.5", "C3m": "C3 A at B2-matched dt", "C3d06": "C3 A dt 0.6 (cap 1)", "C3d10": "C3 A dt 1.0 (cap 1)",
               "C4a": "C4 error-prop dt_max 0.6 ref 3", "C4b": "C4 dt_max 0.6 ref 10", "C4c": "C4 dt_max 1.0 ref 3", "C4d": "C4 dt_max 1.0 ref 10"})
ORDER = list(LABELS)
CSTYLE = {"A": ("A constant (dt 0.2)", "#2a78d6"), "B1": ("B1 pattern, normalized", "#1baf7a"), "B2": ("B2 pattern + physical, cap 1", "#eda100"),
          "C1": ("C1 physical, no pattern", "#eb6834"), "C2": ("C2 pattern at A's step", "#e87ba4"), "C3m": ("C3 A at B2-matched dt", "#7a5ec9"),
          "C4a": ("C4 error-prop dt_max 0.6", "#52514e")}


def load(case: str, grid: int, dt: float | None = None) -> dict:
    p = HERE / "data" / f"{case}_{grid}{f'_dt{dt}' if dt else ''}.json"
    return json.loads(p.read_text()) if p.exists() else {}


def style_axes(ax) -> None:
    ax.set_facecolor(SURFACE)
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=MUTED, labelsize=8)


def figure(cases: list[tuple[str, int, str]], title: str, path: Path, ylim=(0.1, 100), styles=None) -> None:
    styles = styles or STYLE
    fig, axes = plt.subplots(2, len(cases), figsize=(3.9 * len(cases), 7.2), squeeze=False,
                             gridspec_kw={"hspace": 0.28, "wspace": 0.22})
    for c, (case, grid, name) in enumerate(cases):
        res = load(case, grid)
        for r, rr in enumerate(("off", "on")):
            ax = axes[r, c]
            style_axes(ax)
            for key, (label, color) in styles.items():
                run = res.get(f"{key}|{rr}")
                if not run or not run["score"]:
                    continue
                s = np.asarray(run["score"])
                ax.plot(np.arange(1, len(s) + 1), s, color=color, linewidth=3.0 if key == "A" else 1.4,
                        alpha=0.55 if key == "A" else 1.0, label=f"{label}: {run['it']} it, {run['rec']} rec")
            ax.axhline(1.0, color=INK, linestyle="--", linewidth=0.8)
            ax.set_yscale("log")
            ax.set_ylim(*ylim)
            ax.set_title(f"{name}, refresh on rise {rr}", fontsize=9, color=INK)
            if c == 0:
                ax.set_ylabel("score (below 1 is converged)", fontsize=8, color=MUTED)
            if r == 1:
                ax.set_xlabel("iteration", fontsize=8, color=MUTED)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    seen = {}
    for r in range(2):
        for c in range(len(cases)):
            for h, lab in zip(*axes[r, c].get_legend_handles_labels()):
                seen.setdefault(lab.split(":")[0], h)
    fig.legend(list(seen.values()), list(seen), loc="lower center", ncol=3, frameon=False, fontsize=8, labelcolor=INK)
    fig.suptitle(title, fontsize=10, color=INK)
    fig.patch.set_facecolor(SURFACE)
    fig.subplots_adjust(bottom=0.14, top=0.92)
    fig.savefig(path, dpi=130, facecolor=SURFACE)
    plt.close(fig)


def row(key: str, run: dict) -> str:
    n, rr = key.split("|")
    if not run["score"]:
        return f"| {LABELS[n]} | {rr} | {run['status']} |" + " |" * 10
    ratio = run.get("ratio")
    cost = run["it"] + run["rec"] * ratio if ratio else float("nan")
    first = run["first_below1"]
    return (f"| {LABELS[n]} | {rr} | {run['status']} | {run['it']} | {run['rec']} | {cost:.0f} | "
            f"{1e3 * run['wall'] / run['it']:.2f} | {100 * run['mean']:.2f} | {100 * run['max']:.1f} | {100 * run['gt10']:.0f} | "
            f"{run['invalid']} | {run['rises20']} | {run['spike']:.2f} |")


def tables() -> None:
    out = ["# Tables (generated by make_figures.py)", "",
           "Cost = iterations + recomputes x ratio. ms/it = wall time per iteration (one run per cell, load average in the json). "
           "Accuracy and invalid polygons are of the returned geometries (best iterate). rises = increases of the score while it is below 20; "
           "spike = largest relative rise.", ""]
    cases = [("states", 128), ("states", 256), ("states", 512), ("states_mr", 128), ("horiz", 256), ("tang", 256), ("tilt", 256),
             ("districts", 256), ("districts", 512), ("counties", 256), ("counties", 512)]
    for case, grid in cases:
        res = load(case, grid)
        if not res:
            continue
        loads = sorted({r.get("load") for r in res.values() if r.get("load")})
        out += [f"## {case} grid {grid}  (ratio {next(iter(res.values())).get('ratio')}, load {loads[0]} to {loads[-1]})", "",
                "| variant | refresh | status | it | rec | cost | ms/it | mean % | max % | >10 % | invalid | rises | spike |",
                "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for rr in ("off", "on"):
            for n in ORDER:
                if f"{n}|{rr}" in res:
                    out.append(row(f"{n}|{rr}", res[f"{n}|{rr}"]))
        out.append("")
    for case in ("states", "districts"):
        out += [f"## dt sweep, {case} grid 256 (refresh on rise on; it / recomputes / status / invalid)", "",
                "| variant | dt 0.1 | dt 0.2 | dt 0.4 | dt 0.6 |", "|---|---|---|---|---|"]
        sets = {dt: load(case, 256, None if dt == 0.2 else dt) for dt in (0.1, 0.2, 0.4, 0.6)}
        for n in ("A", "B1", "B3n", "B2", "B4n", "B4s"):
            cells = []
            for dt, res in sets.items():
                run = res.get(f"{n}|on")
                cells.append("-" if not run else f"{run['it']} / {run['rec']} / {run['status']} / {run['invalid']}")
            out.append(f"| {LABELS[n]} | " + " | ".join(cells) + " |")
        out.append("")
    for case in ("states", "districts"):
        out += [f"## dt sweep of the controls, {case} grid 256 (refresh on; it / recomputes / status / invalid; C4 uses dt as dt_max, cap 1)", "",
                "| variant | dt 0.1 | dt 0.2 | dt 0.4 | dt 0.6 |", "|---|---|---|---|---|"]
        sets = {dt: load(case, 256, dt) for dt in (0.1, 0.2, 0.4, 0.6)}
        for n in ("C2", "C4a", "C4b"):
            cells = []
            for dt, res in sets.items():
                run = res.get(f"{n}|on")
                cells.append("-" if not run else f"{run['it']} / {run['rec']} / {run['status']} / {run['invalid']}")
            out.append(f"| {LABELS[n]} | " + " | ".join(cells) + " |")
        out.append("")
    p = HERE / "data" / "dtmatch.json"
    if p.exists():
        d = json.loads(p.read_text())
        out += ["## Mean vertex displacement per step (cells) and the dt of C3m", "",
                "| case | A (dt0) | B2 | dt0 | dt of C3m |", "|---|---|---|---|---|"]
        for k, v in d.items():
            out.append(f"| {k} | {v['A']:.3f} | {v['B2']:.3f} | {v['dt0']} | {v['dt_match']:.2f} |")
        out.append("")
    p = HERE / "data" / "bench_precompute.json"
    if p.exists():
        b = json.loads(p.read_text())
        out += ["## B1 versus B3: per-step cost and displacement difference", "",
                "| case, grid | vertices | cells | A ms | B1 ms | B3 ms | max diff t=0 (step lengths) | p99 diff t=0 | max diff t=0.9 | p99 diff t=0.9 | load |",
                "|---|---|---|---|---|---|---|---|---|---|---|"]
        for k, v in b.items():
            out.append(f"| {k} | {v['n_vertices']} | {v['cells']} | {v['ms_A']:.2f} | {v['ms_B1']:.2f} | {v['ms_B3']:.2f} | "
                       f"{v['diff_t0.0_max']:.3f} | {v['diff_t0.0_p99']:.4f} | {v['diff_t0.9_max']:.3f} | {v['diff_t0.9_p99']:.4f} | {v['load']} |")
        out.append("")
    (HERE / "tables.md").write_text("\n".join(out))


if __name__ == "__main__":
    figure([("states", 128, "states 128"), ("states", 256, "states 256"), ("states", 512, "states 512"),
            ("states_mr", 128, "multires coarse level")],
           "US states: score per iteration (legend: iterations, recomputes)", HERE / "convergence_states.png", ylim=(0.2, 60))
    figure([("horiz", 256, "horizontal"), ("tang", 256, "tangential"), ("tilt", 256, "tilted")],
           "Strong anisotropy, states, grid 256", HERE / "convergence_anisotropy.png", ylim=(0.2, 60))
    figure([("districts", 256, "districts 256"), ("districts", 512, "districts 512"), ("counties", 256, "counties 256"),
            ("counties", 512, "counties 512")],
           "Districts and counties", HERE / "convergence_districts_counties.png", ylim=(0.2, 200))
    figure([("states", 256, "states 256"), ("states", 512, "states 512"), ("states_mr", 128, "multires coarse level"),
            ("districts", 256, "districts 256"), ("districts", 512, "districts 512")],
           "Controls: pattern versus magnitude (legend: iterations, recomputes)", HERE / "convergence_controls.png", ylim=(0.2, 100), styles=CSTYLE)
    figure([("horiz", 256, "horizontal"), ("tang", 256, "tangential"), ("tilt", 256, "tilted"), ("counties", 256, "counties 256"),
            ("counties", 512, "counties 512")],
           "Controls: anisotropy and counties", HERE / "convergence_controls_aniso_counties.png", ylim=(0.2, 300), styles=CSTYLE)
    tables()
