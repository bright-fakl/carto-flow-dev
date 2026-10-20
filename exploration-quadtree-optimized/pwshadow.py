"""Shadow mode: the dynamics is the baseline's; at each window start a mesh is built, vertices located, the nodes advected with the
same steps, and at the next window start the piecewise-affine image of the window is compared with the baseline's per-vertex
positions (error in cells). No insertion, no pruning."""
import sys, os, time; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, harness, pw, pwo2
from carto_flow.flow_cartogram.displacement import displace_coords_numba as _disp
import carto_flow.flow_cartogram.algorithm as alg
E = os.environ.get

class Shadow(pwo2.PWO):
    def __init__(self, *a, **k):
        super().__init__(*a, **k); self.errs = []; self.fg = None
    def begin(self, fg, rho, grid, step, vx=None, vy=None):
        if self.win is not None and self.fg is not None and len(self.win["ids"]) == len(fg.coords):
            X = pw._apply(self.win["ids"], self.win["w"], self.win["P"])
            d = np.hypot(*(X - fg.coords).T) / min(grid.dx, grid.dy)
            self.errs.append((step, grid.sx, float(d.mean()), float(np.percentile(d, 99)), float(d.max())))
        self.fg = fg
        dx, dy = grid.dx, grid.dy
        x0 = grid.x_coords[0] - dx / 2; y0 = grid.y_coords[0] - dy / 2
        crit = rho if (self.crit == 'density' or vx is None) else pwo2.curvature(vx, vy)
        (lid, org, bnd, nb, cen, nodes, c4), N = pw.build(crit, self.frac)
        coords = fg.coords
        lat0 = (coords[:, 0] - x0) / dx; lat1 = (coords[:, 1] - y0) / dy
        ids, w = pw._locate(lat0.copy(), lat1.copy(), lid, bnd, nb, cen, nodes)
        P = np.column_stack([x0 + nodes[:, 0] * dx, y0 + nodes[:, 1] * dy])
        self.win = dict(ids=ids, w=w, P=P, cen=cen, c4=c4, bnd=bnd, nb=nb); self.nleaves = len(org)
    def structure(self, fg):
        return None
    def restore(self, fg, coords, nev):
        pass
    def advance(self, grid, vx, vy, dt):
        W = self.win
        P = _disp(W["P"], grid.x_coords, grid.y_coords, vx, vy, dt, grid.dx, grid.dy, False)
        P[W["cen"]] = P[W["c4"]].mean(axis=1); W["P"] = P
        return _disp(self.fg.coords, grid.x_coords, grid.y_coords, vx, vy, dt, grid.dx, grid.dy, False)

h = Shadow(2.0 ** -float(E("BITS", "6")), prune_tol=0, crit=E("CRIT", "density"))
alg.PW_HOOK = h
harness.run("county", 1000, "shadow")
e = np.array(h.errs); fine = e[e[:, 1] >= 2000]
print(f"BITS {E('BITS','6')} CRIT {E('CRIT','density')}: windows {len(e)}; finest level windows {len(fine)}: window-end error in cells: mean of means {fine[:,2].mean():.4f}, mean p99 {fine[:,3].mean():.3f}, mean max {fine[:,4].mean():.2f}, max of max {fine[:,4].max():.2f}; all levels mean of means {e[:,2].mean():.4f} p99 {e[:,3].mean():.3f}")
