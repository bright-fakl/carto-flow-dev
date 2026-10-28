"""Cost of re-validation in with_frame / fill_region.

`IsohedralTiling.with_frame` builds a new IsohedralTiling, whose constructor runs check_prototile and check_curves again,
although a frame does not change validity (docs/curves.md: "Validity does not depend on the frame"). fill_region calls
with_frame once (twice with a nonzero offset). The script times, for the presets with curves: the constructor, with_frame,
fill_region(outline="straight"), and the share of check_curves in the latter.

Run: python with_frame_cost.py > with_frame_cost.txt
"""
import cProfile
import io
import pstats
import time
import warnings

import numpy as np

warnings.simplefilter("ignore")
import isotile  # noqa: E402
from isotile import IsohedralTiling as IT  # noqa: E402

W = (-1, -0.3, 1, 0.3)


def ms(fn, k=10):
    t0 = time.perf_counter()
    for _ in range(k):
        fn()
    return (time.perf_counter() - t0) / k * 1000


print(f"{'preset':22s} {'constructor':>12s} {'with_frame':>11s} {'fill straight':>14s} {'check_curves share of fill straight':>38s}")
rows = []
for name in isotile.list_presets():
    t = IT.from_preset(name)
    if not t.edge_curves:
        continue
    a = ms(lambda: IT(t.type, t.parameters, edge_curves=t.edge_curves, edge_curve_modes=t.edge_curve_modes))
    b = ms(lambda: t.with_frame(np.eye(3)[:2] * 0.1))
    c = ms(lambda: t.fill_region(W, n_tiles=100, margin=0.25, outline="straight"))
    pr = cProfile.Profile()
    pr.enable()
    for _ in range(10):
        t.fill_region(W, n_tiles=100, margin=0.25, outline="straight")
    pr.disable()
    st = pstats.Stats(pr)
    total = st.total_tt
    cc = sum(v[3] for k, v in st.stats.items() if k[2] == "check_curves")
    rows.append((a, b, c, cc / total))
    print(f"{name:22s} {a:10.2f} ms {b:9.2f} ms {c:12.2f} ms {100 * cc / total:36.0f} %")
r = np.array(rows)
print(f"median over {len(rows)} presets with curves: constructor {np.median(r[:, 0]):.2f} ms, with_frame {np.median(r[:, 1]):.2f} ms, fill_region(straight) {np.median(r[:, 2]):.2f} ms, check_curves share {100 * np.median(r[:, 3]):.0f} %")
