"""Slider limits from the current state (editor_model.slider_limits) against a fine sweep, and the cost.

For each of the 128 parameters of the 55 types with parameters: at the defaults and at 4 random valid states in [0, 1]^k,
the interval found by slider_limits is compared with the connected valid interval around the current value found by a sweep
with step 0.002 over [0, 1]. Also compared: TilingType.safe_ranges clipped to [0, 1] at the defaults.

Run: python slider_limits.py > slider_limits.txt
"""
import statistics
import time
import warnings

import numpy as np

warnings.simplefilter("ignore")
from isotile import check_prototile, get_type, tiling_types  # noqa: E402
import editor_model as em  # noqa: E402

rng = np.random.default_rng(5)


def truth(n, p, k):
    grid = np.arange(0.0, 1.0 + 1e-9, 0.002)

    def ok(v):
        q = list(p)
        q[k] = v
        return check_prototile(n, q).valid

    v0 = p[k]
    i0 = int(np.argmin(np.abs(grid - v0)))
    lo = hi = grid[i0]
    for i in range(i0, -1, -1):
        if not ok(grid[i]):
            break
        lo = grid[i]
    for i in range(i0, len(grid)):
        if not ok(grid[i]):
            break
        hi = grid[i]
    return lo, hi


rows = []
times = []
n_cases = n_match = n_safe_match = n_safe_state = n_state = 0
worst = 0.0
for n in tiling_types():
    t = get_type(n)
    for k in range(t.n_params):
        starts = [list(t.default_params)]
        while len(starts) < 5:
            p = rng.uniform(0, 1, t.n_params)
            if check_prototile(n, p).valid:
                starts.append(list(p))
        for si, p in enumerate(starts):
            d = em.Draft.of(n, p)
            t0 = time.perf_counter()
            lo, hi = em.slider_limits(d, k)
            times.append((time.perf_counter() - t0) * 1000)
            tl, th = truth(n, p, k)
            n_cases += 1
            err = max(abs(lo - tl), abs(hi - th))
            worst = max(worst, err)
            n_match += err <= 4e-3
            slo, shi = t.safe_ranges[k]
            same_safe = max(abs(max(slo, 0.0) - tl), abs(min(shi, 1.0) - th)) <= 4e-3
            if si == 0:
                n_safe_match += same_safe
            else:
                n_state += 1
                n_safe_state += same_safe
print(f"{n_cases} (parameter, state) cases: slider_limits within 0.004 of the sweep in {n_match}, largest difference {worst:.3f}")
print(f"safe_ranges clipped to [0, 1] equals the sweep at the defaults in {n_safe_match} of {sum(get_type(n).n_params for n in tiling_types())} parameters")
print(f"... and at random valid states (other parameters not at their defaults): equals the sweep in {n_safe_state} of {n_state} cases")
print(f"cost of slider_limits (both ends): median {statistics.median(times):.1f} ms, 95th percentile {np.percentile(times, 95):.1f} ms, max {max(times):.1f} ms")
