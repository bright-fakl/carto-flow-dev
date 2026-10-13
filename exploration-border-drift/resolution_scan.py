"""Border band z against grid size with the field recomputed every iteration (#86)."""
import json
import sys

import border_band as bb

rows = []
for grid in (int(a) for a in sys.argv[1:]):
    rows.append(bb.run(f"grid {grid}, recompute_every 1", grid=grid, recompute_every=1, recompute_on_rise=None))
(bb.HERE / "data" / f"resolution_scan_{'_'.join(sys.argv[1:])}.json").write_text(json.dumps(rows))
