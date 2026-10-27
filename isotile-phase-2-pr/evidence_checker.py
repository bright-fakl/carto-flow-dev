"""Sampled polyline test against the certified clearance test and GEOS on random curved prototiles.

    cd /home/fakl/isotile-phase2 && uv run python /home/fakl/carto-flow-dev/isotile-phase-2-pr/evidence_checker.py <seed>

Random draws as in evidence_fit.py (81 types, amplitudes 0.1 to 2.0, 4 draws each). The sampled test is the
polyline test of the first version of the PR (tests/sampled_check.py, at the default sampling).
"""
import sys

import numpy as np
import shapely

sys.path.insert(0, "/home/fakl/carto-flow-dev/isotile-phase-2-pr")
sys.path.insert(0, "/home/fakl/isotile-phase2")
from evidence_fit import trial
from tests.sampled_check import check_outline

from isotile import check_prototile, get_type, tiling_types
from isotile.curves import native_edge_transforms, normalize_curves, outline

rng = np.random.default_rng(int(sys.argv[1]) if len(sys.argv) > 1 else 0)
rows = []
for amp in (0.1, 0.3, 0.6, 1.0, 2.0):
    for number in tiling_types():
        for _ in range(4):
            p, curves = trial(number, amp, rng)
            t = get_type(number)
            if not check_prototile(number, p).valid:
                continue
            points, starts = outline(t, native_edge_transforms(t, p), normalize_curves(t, curves, None))
            sampled_bad, sampled_message = check_outline(points, starts)
            report = check_prototile(number, p, edge_curves=curves)
            geos = shapely.Polygon(points).is_valid
            rows.append((number, amp, not sampled_bad, report.valid, geos, report.message))
a = np.array([(r[2], r[3], r[4]) for r in rows])
print(len(rows), "draws; valid: sampled", a[:, 0].sum(), "certified", a[:, 1].sum(), "GEOS on the samples", a[:, 2].sum())
print("sampled and GEOS differ:", int((a[:, 0] != a[:, 2]).sum()))
for name, mask in (("sampled valid, certified invalid", a[:, 0] & ~a[:, 1]), ("sampled invalid, certified valid", ~a[:, 0] & a[:, 1])):
    print(name, int(mask.sum()))
    for r in [rows[i] for i in np.flatnonzero(mask)]:
        print("   ", r)
