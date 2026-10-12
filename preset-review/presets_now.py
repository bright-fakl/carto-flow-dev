"""The three presets as they are, on states, districts and counties (stall rule, refresh-on-rise, adaptive_dt, exact rasterization all at their defaults)."""
import json
import os
from pathlib import Path

from common import INPUTS, MorphOptions, fmt, run

HERE = Path(__file__).resolve().parent
PRESETS = {"fast": MorphOptions.preset_fast(), "balanced": MorphOptions.preset_balanced(), "high_quality": MorphOptions.preset_high_quality(), "default": MorphOptions()}
rows = []
for name in INPUTS:
    for pname, opts in PRESETS.items():
        r = run(name, opts, repeats=2)
        r["preset"] = pname
        rows.append(r)
        print(f"{name:10s} {pname:13s} grid {opts.grid_size} n_iter {opts.n_iter} dt {opts.dt} tol {opts.mean_tol}/{opts.max_tol}: {fmt(r)}", flush=True)
(HERE / "data" / f"presets_{os.environ.get('LABEL', 'after')}.json").write_text(json.dumps(rows))
