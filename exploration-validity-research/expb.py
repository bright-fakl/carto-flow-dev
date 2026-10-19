"""Alternatives on the baseline: higher-order / sub-stepped advection (ADV), value floor (VFLOOR), step size via MORPH_OPTS."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from numba import njit, prange
import harness
import carto_flow.flow_cartogram.algorithm as alg

@njit(cache=True, fastmath=True, inline="always")
def _vel(x, y, xc0, yc0, dxi, dyi, vx, vy, xc, yc):
    max_ix = vx.shape[1] - 2; max_iy = vy.shape[0] - 2
    ix = max(0, min(int((x - xc0) * dxi), max_ix)); iy = max(0, min(int((y - yc0) * dyi), max_iy))
    tx = (x - xc[ix]) * dxi; ty = (y - yc[iy]) * dyi
    w00 = (1 - tx) * (1 - ty); w10 = tx * (1 - ty); w01 = (1 - tx) * ty; w11 = tx * ty
    return (w00 * vx[iy, ix] + w10 * vx[iy, ix + 1] + w01 * vx[iy + 1, ix] + w11 * vx[iy + 1, ix + 1],
            w00 * vy[iy, ix] + w10 * vy[iy, ix + 1] + w01 * vy[iy + 1, ix] + w11 * vy[iy + 1, ix + 1])

@njit(cache=True, fastmath=True)
def displace_hi(coords, xc, yc, vx, vy, dt, dx, dy, mode, nsub):
    out = coords.copy(); dxi = 1.0 / dx; dyi = 1.0 / dy
    h = dt / nsub
    for i in range(coords.shape[0]):
        x = coords[i, 0]; y = coords[i, 1]
        for s in range(nsub):
            if mode == 0:  # Euler substeps
                u, v = _vel(x, y, xc[0], yc[0], dxi, dyi, vx, vy, xc, yc)
                x += h * u; y += h * v
            elif mode == 1:  # midpoint
                u, v = _vel(x, y, xc[0], yc[0], dxi, dyi, vx, vy, xc, yc)
                u2, v2 = _vel(x + 0.5 * h * u, y + 0.5 * h * v, xc[0], yc[0], dxi, dyi, vx, vy, xc, yc)
                x += h * u2; y += h * v2
            else:  # RK4
                k1x, k1y = _vel(x, y, xc[0], yc[0], dxi, dyi, vx, vy, xc, yc)
                k2x, k2y = _vel(x + 0.5 * h * k1x, y + 0.5 * h * k1y, xc[0], yc[0], dxi, dyi, vx, vy, xc, yc)
                k3x, k3y = _vel(x + 0.5 * h * k2x, y + 0.5 * h * k2y, xc[0], yc[0], dxi, dyi, vx, vy, xc, yc)
                k4x, k4y = _vel(x + h * k3x, y + h * k3y, xc[0], yc[0], dxi, dyi, vx, vy, xc, yc)
                x += h / 6 * (k1x + 2 * k2x + 2 * k3x + k4x); y += h / 6 * (k1y + 2 * k2y + 2 * k3y + k4y)
        out[i, 0] = x; out[i, 1] = y
    return out

adv = os.environ.get("ADV")
if adv:
    mode = {"euler": 0, "rk2": 1, "rk4": 2}[adv.rstrip("0123456789") if adv not in ("rk2", "rk4") else adv] if adv in ("rk2", "rk4") else 0
    nsub = int(os.environ.get("NSUB", "1"))
    def patched(coords, xc, yc, vx, vy, dt, dx, dy, use_parallel=True):
        return displace_hi(coords, xc, yc, vx, vy, dt, dx, dy, mode, nsub)
    alg.displace_coords_numba = patched
floor = float(os.environ.get("VFLOOR", "0"))
if floor > 0:
    _load = harness.load
    def load(dataset="county"):
        g, v = _load(dataset)
        g = g.assign(v=np.maximum(v, floor * np.median(v)))
        return g, v
    harness.load = load
    # run() unpacks load -> (gdf with floored v, original v) and measures errors against the original v
harness.run(sys.argv[1] if len(sys.argv) > 1 else "county", int(sys.argv[2]) if len(sys.argv) > 2 else 1000, os.environ.get("LABEL", "expb"))
