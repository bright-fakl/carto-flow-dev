"""Tables of the preset review from data/*.json (run presets_now.py with LABEL=before on main and LABEL=after on the branch,
preset_matrix.py and hq_dt.py first)."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
load = lambda n: json.loads((HERE / "data" / n).read_text())  # noqa: E731
out = []


def cell(r):
    return f"{r['status']}, {r['it']} it, cost {r['cost']:.0f}, {r['wall']:.2f} s; true mean {r['true_mean']:.2f} / max {r['true_max']:.1f} %; invalid {r['invalid']}"


out.append("## The presets before and after\n")
out.append("| input | preset | before (n_iter as listed) | after |\n|---|---|---|---|")
before, after = load("presets_before.json"), load("presets_after.json")
b = {(r["input"], r["preset"]): r for r in before}
for r in after:
    k = (r["input"], r["preset"])
    out.append(f"| {r['input']} | {r['preset']} | {cell(b[k])} | {cell(r)} |")

m = load("preset_matrix.json")
out.append("\n## Grid, dt and tolerance sets (n_iter 500; iterations / cost / invalid output regions)\n")
for name in ("states", "districts"):
    out.append(f"**{name}**\n")
    out.append("| grid | dt | loose 15/25 % | default 5/10 % | tight 1/3 % |\n|---|---|---|---|---|")
    for grid in (128, 256, 512):
        for dt in (0.2, 0.3, 0.4):
            cells = []
            for tol in ("loose 15/25 %", "default 5/10 %", "tight 1/3 %"):
                r = next(x for x in m if x["input"] == name and x["grid"] == grid and x["dt"] == dt and x["tol"] == tol)
                flag = "" if r["status"] == "converged" else f" ({r['status']})"
                cells.append(f"{r['it']} / {r['cost']:.0f} / {r['invalid']}{flag}")
            out.append(f"| {grid} | {dt} | " + " | ".join(cells) + " |")
    out.append("")

h = load("hq_dt.json")
out.append("## dt for the high-quality preset (grid 512, n_iter 1000)\n")
out.append("| input | dt | tolerances | iterations | cost | true mean / max % | invalid regions |\n|---|---|---|---|---|---|---|")
for r in h:
    out.append(f"| {r['input']} | {r['dt']} | {r['tol']} | {r['it']} ({r['status']}) | {r['cost']:.0f} | {r['true_mean']:.2f} / {r['true_max']:.1f} | {r['invalid']} |")
(HERE / "data" / "tables.md").write_text("\n".join(out) + "\n")
print("\n".join(out))
