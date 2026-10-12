"""Writes data/tables.md from the JSON files that start_resolution.py and relaxed_coarse.py leave in data/ (no run here)."""
import glob
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(pattern):
    rows = []
    for f in sorted(glob.glob(str(HERE / "data" / pattern))):
        rows += json.loads(Path(f).read_text())
    return rows


def lv(levels):
    return ", ".join(f"{g} {s[:4]} {i}" for g, s, i in levels)


out = []
out.append("## Start grid (finest 512 on districts, 1024 on others), default and tight tolerance\n")
out.append("| input | tolerance | start | regions < 1 cell at start | status | iterations | true mean / max % | invalid | levels (grid status iterations) |\n|---|---|---|---|---|---|---|---|---|")
for r in load("start_*_default.json") + load("start_*_tight.json") + load("start_districts_loose*.json"):
    if "f2048" in str(r) and False:
        continue
    out.append(f"| {r['input']} | {r['tol']} | {r['start']} | {r['sub_cell_pct_at_start']:.1f} % | {r['reported_status']} | {r['iterations']} | {r['true_mean']:.2f} / {r['true_max']:.1f} | {r['invalid']} | {lv(r['levels_run'])} |")
out.append("\n## Counties, finest grid 2048 and 4096\n")
out.append("| start | levels | true mean / max % | invalid |\n|---|---|---|---|")
for pat in ("start_counties_default_f2048.json", "start_counties_default_f4096.json"):
    for r in load(pat):
        out.append(f"| {r['start']} | {lv(r['levels_run'])} | {r['true_mean']:.1f} / {r['true_max']:.0f} | {r['invalid']} |")
out.append("\n## Single grid, strict ladder, relaxed ladder (tolerance 1 % / 3 %; relaxed: coarse levels at 4 times)\n")
out.append("| input | values | finest | scheme | status | iterations | seconds | true mean / max % | invalid | levels |\n|---|---|---|---|---|---|---|---|---|---|")
for fin, pat in (("default", "relaxed_districts_states.json"), ("default", "relaxed_*_fdef_*.json"), ("1024", "relaxed_*_f1024_*.json"), ("2048", "relaxed_*_f2048_*.json")):
    for r in load(pat):
        f = fin if fin != "default" else ("256" if r["input"] == "states" else "512")
        out.append(f"| {r['input']} | {r['dist']} | {f} | {r['scheme']} | {r['status']} | {r['iterations']} | {r['wall']:.1f} | {r['true_mean']:.2f} / {r['true_max']:.1f} | {r['invalid']} | {lv(r['levels'])} |")
(HERE / "data" / "tables.md").write_text("\n".join(out) + "\n")
print(len(out), "lines")
