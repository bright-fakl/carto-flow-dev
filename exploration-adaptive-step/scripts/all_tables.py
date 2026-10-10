"""Write every table to data/tables.md."""

import io
import runpy
import sys
from contextlib import redirect_stdout
from pathlib import Path

import tables as T

D = Path(__file__).resolve().parent.parent / "data"
out = []
for name, args in [("spikes", ()), ("accuracy", ()), ("accuracy", (0.6,)), ("robustness", ()), ("bydt", ()), ("counties", ()), ("restart_summary", ()), ("multires_summary", ()), ("stall", ())]:
    out.append(f"## {name} {args}\n\n{getattr(T, name)(*args)}\n")
buf = io.StringIO()
with redirect_stdout(buf):
    sys.argv = ["timing_table.py"]
    runpy.run_path(str(Path(__file__).parent / "timing_table.py"))
out.append("## timing\n\n" + buf.getvalue())
(D / "tables.md").write_text("\n".join(out))
