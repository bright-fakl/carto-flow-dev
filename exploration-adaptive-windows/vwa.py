"""Validated windows with an adaptive check interval (subclass of vwd.VW).

The check (crossing test and repair of vwd.VW) runs at a window start when the policy says it is due. The stored fields
(one per window since the last check) are bounded by `n_cap` windows and by `mem_budget_mb` in every policy.

policy = 'fixed'   : every n windows (vwd.VW.check_every)
         'dist'    : the distance of the fastest vertex since the last check reaches `dmax` cells (sum of dt * step factor)
         'dens'    : the risk integral sum(l^2 * d) over the windows since the last check reaches `r0`, with l the
                     `q` quantile of the segment length in cells now and d the distance of the fastest vertex in the window
         'backoff' : interval doubles after a check without crossings (up to n_cap), halves after a check with crossings
         'dens+backoff' : both conditions must... (the check is due when either says so)
"""
import time
import numpy as np
from numba import njit
import vwd

NB = 80  # histogram bins, log10 of the length in cells from 1e-3 to 1e2 (1/16 decade)


@njit(cache=True)
def _len_hist(c, offs, cell):
    h = np.zeros(NB, np.int64)
    mx = 0.0
    n = 0
    for r in range(offs.shape[0] - 1):
        for i in range(offs[r], offs[r + 1] - 1):
            dx = c[i + 1, 0] - c[i, 0]; dy = c[i + 1, 1] - c[i, 1]
            L = np.sqrt(dx * dx + dy * dy) / cell
            if L > mx:
                mx = L
            b = int((np.log10(max(L, 1e-9)) + 3.0) * 16.0)
            b = min(max(b, 0), NB - 1)
            h[b] += 1
            n += 1
    return h, mx, n


def len_quantile(h, n, q):
    cs = np.cumsum(h)
    b = int(np.searchsorted(cs, q * n))
    b = min(b, NB - 1)
    return 10.0 ** ((b + 1) / 16.0 - 3.0)  # upper edge of the bin


class VWA(vwd.VW):
    def __init__(self, *a, policy="fixed", n=10, n_cap=10, r0=2.0, q=0.99, dmax=20.0, start=1, **kw):
        super().__init__(*a, **kw)
        self.policy = policy
        self.n = n
        self.n_cap = n_cap
        self.r0 = r0
        self.q = q
        self.dmax = dmax
        self.cur_n = start
        self.start = start
        self.cell = None
        self.risk = 0.0
        self.dist = 0.0
        self.win_dist = 0.0
        self.maxv = 0.0
        self.clog = []
        self.n_checks = 0
        self.t_stats = 0.0
        self.max_nwin = 0

    def reset(self):
        super().reset()
        self.risk = 0.0; self.dist = 0.0; self.cur_n = self.start

    def start_window(self, fg, grid=None, best_state=None, step=0):
        if grid is not None:
            self.cell = float(min(grid.dx, grid.dy))
        self.win_dist = 0.0
        return super().start_window(fg, grid, best_state, step)

    def field(self, vx, vy):
        super().field(vx, vy)
        self.maxv = float(np.sqrt((vx * vx + vy * vy).max()))
        self.maxv = max(self.maxv, 1e-8)

    def record(self, dt):
        super().record(dt)
        # dt_prime * max_v is the distance of the fastest point (the algorithm's max_abs_velocity is the vector norm; the
        # component maximum is a lower bound within a factor sqrt(2))
        self.win_dist += dt * self.maxv / self.cell
        self.dist += dt * self.maxv / self.cell

    def _decide(self, fg):
        """True if a check is due (called at a window start with at least one completed window since the last check)."""
        k = self.nwin_span
        self.max_nwin = max(self.max_nwin, k)
        if k >= self.n_cap or self._over_budget():
            return True
        p = self.policy
        if p == "fixed":
            return k >= self.n
        if p == "dist":
            return self.dist >= self.dmax
        if p in ("dens", "dens+backoff"):
            t0 = time.perf_counter()
            h, mx, n = _len_hist(fg.coords, np.asarray(fg.ragged_offsets[0], dtype=np.int64), self.cell)
            l = len_quantile(h, n, self.q)
            self.t_stats += time.perf_counter() - t0
            self.risk += l * l * self.win_dist
            self.last_l = l
            if self.risk >= self.r0:
                return True
            if p == "dens":
                return False
        if p in ("backoff", "dens+backoff", "lazyu"):
            return k >= self.cur_n
        return False

    def repair(self, fg, grid, vx, vy, best_state, step, force=False):
        if self.S is None or not self.dts:
            return best_state
        if not force and not self._decide(fg):
            return best_state
        k = self.nwin_span
        ins0 = self.n_inserted; rep0 = self.n_windows_repaired; unr0 = self.unresolved
        self.check_every = 0
        out = super().repair(fg, grid, vx, vy, best_state, step, force=True)
        self.n_checks += 1
        found = self.n_windows_repaired > rep0
        self.clog.append((step, self.cell, k, int(found), self.n_inserted - ins0, round(self.dist, 2), round(self.risk, 2), round(getattr(self, "last_l", -1.0), 3)))
        self.risk = 0.0; self.dist = 0.0
        trouble = (self.unresolved > unr0) if self.policy == "lazyu" else found
        if trouble:
            self.cur_n = max(1, self.cur_n // 2)
        else:
            self.cur_n = min(self.cur_n * 2, self.n_cap)
        return out
