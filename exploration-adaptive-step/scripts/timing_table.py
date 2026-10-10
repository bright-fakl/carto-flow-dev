"""Markdown table of data/timing.json."""

import json
from pathlib import Path

D = Path(__file__).resolve().parent.parent / "data"
N = {"base": "constant dt", "A_r3_m0.05": "A ref 3", "A_r10_m0.05": "A ref 10", "B_0.1": "B 10 %", "AB_r10_f0.05": "A ref 10 + B 5 %"}
rows = json.load(open(D / "timing.json"))
print("| case | dt | refresh on rise | controller | status | it | rec | redo steps | cost | wall s (min of 2) | load avg |")
print("|---|---|---|---|---|---|---|---|---|---|---|")
for r in rows:
    print(f"| {r['case']} | {r['dt']} | {r['rr']} | {N[r['variant']]} | {r['status']} | {r['it']} | {r['rec']} | {r['redo']} | {r['cost']:.0f} | {r['wall']:.2f} | {min(r['loads']):.0f} to {max(r['loads']):.0f} |")
