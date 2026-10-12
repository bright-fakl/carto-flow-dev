"""Writes data/tables.md from the JSON left by stall_levels.py."""
import glob
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
rows = []
for f in sorted(glob.glob(str(HERE / "data" / "stall_*.json"))):
    rows += json.loads(Path(f).read_text())
out = ["| case | variant | status | iterations | recomputes | cost | seconds | true mean / max % | invalid | levels (grid, status, iterations) |", "|---|---|---|---|---|---|---|---|---|---|"]
for r in rows:
    lv = ", ".join(f"{g} {s[:4]} {i}" for g, s, i in r["levels"])
    out.append(f"| {r['case']} | {r['variant']} | {r['status']} | {r['iterations']} | {r['recomputes']} | {r['cost']:.0f} | {r['wall']:.1f} | {r['true_mean']:.2f} / {r['true_max']:.1f} | {r['invalid']} | {lv} |")
(HERE / "data" / "tables.md").write_text("\n".join(out) + "\n")
