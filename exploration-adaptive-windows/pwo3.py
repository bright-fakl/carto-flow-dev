"""Quadtree-window hook with remedies for inverted fan triangles (subclass of pwo.PWO).

fix = 'none'      : the fan center is the mean of the four corners (pwo.PWO); node substeps if a triangle inverts
      'kernel'    : a leaf whose fan inverts gets its center at the centroid of the kernel of the leaf polygon
                    (half-plane clipping); the fan combinatorics are unchanged
      'dp'        : a leaf whose fan inverts (and, if 'kernel+dp', whose kernel center fails) is triangulated without a
                    center node: the triangulation of the deformed leaf polygon that maximizes the minimum angle
                    (dynamic programming over the polygon, valid diagonals only, triangles non-degenerate in the
                    undeformed leaf); the vertices of the leaf are relocated in the undeformed triangulation
      'dpall'     : as 'dp' for every leaf and every iteration (the temporary triangulation of the paper)
      'kernel+dp' : kernel first, then dp for the leaves where it fails
Leaves that stay inverted go to the node substeps (if substep=True).
"""
import time
import numpy as np
from numba import njit, prange
import pwo, pw
from carto_flow.flow_cartogram.displacement import displace_coords_numba as _disp

MAXT = 6


@njit(cache=True)
def _bad_leaves(P, bnd, nb, cen, flag):
    cnt = 0
    tri = 0
    for k in range(nb.shape[0]):
        c = cen[k]
        m = nb[k]
        b = 0
        for t in range(m):
            a = bnd[k, t]; bb = bnd[k, (t + 1) % m]
            cr = (P[a, 0] - P[c, 0]) * (P[bb, 1] - P[c, 1]) - (P[a, 1] - P[c, 1]) * (P[bb, 0] - P[c, 0])
            if cr <= 0.0:
                b += 1
        flag[k] = b
        if b > 0:
            cnt += 1
            tri += b
    return cnt, tri


@njit(cache=True)
def _fan_ok(P, bnd, nb, k, cx, cy, thr):
    m = nb[k]
    for t in range(m):
        a = bnd[k, t]; bb = bnd[k, (t + 1) % m]
        cr = (P[a, 0] - cx) * (P[bb, 1] - cy) - (P[a, 1] - cy) * (P[bb, 0] - cx)
        if cr <= thr:
            return False
    return True


@njit(cache=True)
def _kernel_centroid(P, bnd, m, k, out):
    """Centroid of the kernel (intersection of the left half planes of the directed edges) of leaf k; False if empty."""
    xs = np.empty(40); ys = np.empty(40); xt = np.empty(40); yt = np.empty(40)
    x0 = 1e300; y0 = 1e300; x1 = -1e300; y1 = -1e300
    for i in range(m):
        a = bnd[k, i]
        x0 = min(x0, P[a, 0]); x1 = max(x1, P[a, 0]); y0 = min(y0, P[a, 1]); y1 = max(y1, P[a, 1])
    xs[0] = x0; ys[0] = y0; xs[1] = x1; ys[1] = y0; xs[2] = x1; ys[2] = y1; xs[3] = x0; ys[3] = y1
    n = 4
    for e in range(m):
        a = bnd[k, e]; b = bnd[k, (e + 1) % m]
        ax = P[a, 0]; ay = P[a, 1]
        ex = P[b, 0] - ax; ey = P[b, 1] - ay
        nn = 0
        for i in range(n):
            j = (i + 1) % n
            si = ex * (ys[i] - ay) - ey * (xs[i] - ax)
            sj = ex * (ys[j] - ay) - ey * (xs[j] - ax)
            if si >= 0.0:
                xt[nn] = xs[i]; yt[nn] = ys[i]; nn += 1
            if (si >= 0.0) != (sj >= 0.0):
                t = si / (si - sj)
                xt[nn] = xs[i] + t * (xs[j] - xs[i]); yt[nn] = ys[i] + t * (ys[j] - ys[i]); nn += 1
        if nn < 3:
            return False
        for i in range(nn):
            xs[i] = xt[i]; ys[i] = yt[i]
        n = nn
    A = 0.0; cx = 0.0; cy = 0.0
    for i in range(n):
        j = (i + 1) % n
        w = xs[i] * ys[j] - xs[j] * ys[i]
        A += w; cx += (xs[i] + xs[j]) * w; cy += (ys[i] + ys[j]) * w
    if A <= 0.0:
        return False
    out[0] = cx / (3.0 * A); out[1] = cy / (3.0 * A)
    return True


@njit(cache=True, parallel=True)
def _fix_kernel(P, bnd, nb, cen, lst, okout):
    for u in prange(lst.shape[0]):
        k = lst[u]
        out = np.empty(2)
        okout[u] = False
        if _kernel_centroid(P, bnd, nb[k], k, out):
            x0 = 1e300; x1 = -1e300; y0 = 1e300; y1 = -1e300
            for i in range(nb[k]):
                a = bnd[k, i]
                x0 = min(x0, P[a, 0]); x1 = max(x1, P[a, 0]); y0 = min(y0, P[a, 1]); y1 = max(y1, P[a, 1])
            thr = 1e-9 * (x1 - x0) * (y1 - y0)
            if _fan_ok(P, bnd, nb, k, out[0], out[1], thr):
                P[cen[k], 0] = out[0]; P[cen[k], 1] = out[1]
                okout[u] = True


@njit(cache=True, inline="always")
def _cr(ax, ay, bx, by, cx, cy):
    return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)


@njit(cache=True)
def _diag_ok(X, Y, m, i, j):
    # cone test at i
    i0 = (i - 1) % m; i1 = (i + 1) % m
    if _cr(X[i], Y[i], X[i1], Y[i1], X[i0], Y[i0]) >= 0.0:
        inc = _cr(X[i], Y[i], X[j], Y[j], X[i0], Y[i0]) > 0.0 and _cr(X[j], Y[j], X[i], Y[i], X[i1], Y[i1]) > 0.0
    else:
        inc = not (_cr(X[i], Y[i], X[j], Y[j], X[i1], Y[i1]) >= 0.0 and _cr(X[j], Y[j], X[i], Y[i], X[i0], Y[i0]) >= 0.0)
    if not inc:
        return False
    for e in range(m):
        f = (e + 1) % m
        if e == i or e == j or f == i or f == j:
            continue
        o1 = _cr(X[i], Y[i], X[j], Y[j], X[e], Y[e])
        o2 = _cr(X[i], Y[i], X[j], Y[j], X[f], Y[f])
        o3 = _cr(X[e], Y[e], X[f], Y[f], X[i], Y[i])
        o4 = _cr(X[e], Y[e], X[f], Y[f], X[j], Y[j])
        if o1 * o2 <= 0.0 and o3 * o4 <= 0.0:
            return False
    return True


@njit(cache=True)
def _tri_q(X, Y, X0, Y0, m, i, k, j, thr0, eps):
    cr = _cr(X[i], Y[i], X[k], Y[k], X[j], Y[j])
    if cr <= eps:
        return -1.0
    cr0 = _cr(X0[i], Y0[i], X0[k], Y0[k], X0[j], Y0[j])
    if cr0 <= thr0:
        return -1.0
    for v in range(m):
        if v == i or v == k or v == j:
            continue
        if _cr(X[i], Y[i], X[k], Y[k], X[v], Y[v]) >= 0.0 and _cr(X[k], Y[k], X[j], Y[j], X[v], Y[v]) >= 0.0 and _cr(X[j], Y[j], X[i], Y[i], X[v], Y[v]) >= 0.0:
            return -1.0
    l1 = (X[k] - X[i]) ** 2 + (Y[k] - Y[i]) ** 2
    l2 = (X[j] - X[k]) ** 2 + (Y[j] - Y[k]) ** 2
    l3 = (X[i] - X[j]) ** 2 + (Y[i] - Y[j]) ** 2
    mx = max(l1, l2, l3); mn = min(l1, l2, l3); md = l1 + l2 + l3 - mx - mn
    return cr / np.sqrt(mx * md)


@njit(cache=True)
def _dp_leaf(P, P0, bnd, m, k, tri):
    """Triangulation of the deformed leaf polygon maximizing the minimum angle (sin of it); returns the triangle count."""
    X = np.empty(m); Y = np.empty(m); X0 = np.empty(m); Y0 = np.empty(m)
    sx = 1e300; ex = -1e300; sy = 1e300; ey = -1e300
    dx0 = 1e300; dx1 = -1e300; dy0 = 1e300; dy1 = -1e300
    for i in range(m):
        a = bnd[k, i]
        X[i] = P[a, 0]; Y[i] = P[a, 1]; X0[i] = P0[a, 0]; Y0[i] = P0[a, 1]
        sx = min(sx, X[i]); ex = max(ex, X[i]); sy = min(sy, Y[i]); ey = max(ey, Y[i])
        dx0 = min(dx0, X0[i]); dx1 = max(dx1, X0[i]); dy0 = min(dy0, Y0[i]); dy1 = max(dy1, Y0[i])
    thr0 = 1e-6 * (dx1 - dx0) * (dy1 - dy0)
    eps = 1e-12 * max((ex - sx) * (ey - sy), 1e-300)
    ok = np.zeros((m, m), np.bool_)
    for i in range(m):
        for j in range(m):
            if i == j:
                continue
            d = (j - i) % m
            if d == 1 or d == m - 1:
                ok[i, j] = True
            else:
                ok[i, j] = _diag_ok(X, Y, m, i, j)
    best = np.full((m, m), -1.0)
    ch = np.full((m, m), -1, np.int64)
    for ln in range(2, m):
        for i in range(0, m - ln):
            j = i + ln
            if not ok[i, j]:
                continue
            bq = -1.0; bk = -1
            for kk in range(i + 1, j):
                if not (ok[i, kk] and ok[kk, j]):
                    continue
                q = _tri_q(X, Y, X0, Y0, m, i, kk, j, thr0, eps)
                if q <= 0.0:
                    continue
                if kk > i + 1:
                    if best[i, kk] <= 0.0:
                        continue
                    q = min(q, best[i, kk])
                if j > kk + 1:
                    if best[kk, j] <= 0.0:
                        continue
                    q = min(q, best[kk, j])
                if q > bq:
                    bq = q; bk = kk
            best[i, j] = bq; ch[i, j] = bk
    if best[0, m - 1] <= 0.0:
        return 0
    stack = np.empty((2 * m, 2), np.int64)
    sp = 0
    stack[0, 0] = 0; stack[0, 1] = m - 1; sp = 1
    nt = 0
    while sp > 0:
        sp -= 1
        i = stack[sp, 0]; j = stack[sp, 1]
        kk = ch[i, j]
        if nt >= tri.shape[0]:
            return 0
        tri[nt, 0] = i; tri[nt, 1] = kk; tri[nt, 2] = j
        nt += 1
        if kk > i + 1:
            stack[sp, 0] = i; stack[sp, 1] = kk; sp += 1
        if j > kk + 1:
            stack[sp, 0] = kk; stack[sp, 1] = j; sp += 1
    return nt


@njit(cache=True, parallel=True)
def _dp_leaves(P, P0, bnd, nb, lst, tri, nt):
    for u in prange(lst.shape[0]):
        k = lst[u]
        t = np.zeros((MAXT, 3), np.int64)
        n = _dp_leaf(P, P0, bnd, nb[k], k, t)
        nt[k] = n
        for a in range(n):
            for b in range(3):
                tri[k, a, b] = t[a, b]


@njit(cache=True, parallel=True)
def _remap(vleaf, Q, changed, nt, tri, bnd, P0, ids0, w0, ids, w):
    for p in prange(vleaf.shape[0]):
        k = vleaf[p]
        if not changed[k]:
            continue
        if nt[k] == 0:
            ids[p, 0] = ids0[p, 0]; ids[p, 1] = ids0[p, 1]; ids[p, 2] = ids0[p, 2]
            w[p, 0] = w0[p, 0]; w[p, 1] = w0[p, 1]; w[p, 2] = w0[p, 2]
            continue
        best = -1e300
        for t in range(nt[k]):
            a = bnd[k, tri[k, t, 0]]; b = bnd[k, tri[k, t, 1]]; c = bnd[k, tri[k, t, 2]]
            det = (P0[b, 0] - P0[a, 0]) * (P0[c, 1] - P0[a, 1]) - (P0[b, 1] - P0[a, 1]) * (P0[c, 0] - P0[a, 0])
            wb = ((Q[p, 0] - P0[a, 0]) * (P0[c, 1] - P0[a, 1]) - (Q[p, 1] - P0[a, 1]) * (P0[c, 0] - P0[a, 0])) / det
            wc = ((P0[b, 0] - P0[a, 0]) * (Q[p, 1] - P0[a, 1]) - (P0[b, 1] - P0[a, 1]) * (Q[p, 0] - P0[a, 0])) / det
            wa = 1.0 - wb - wc
            mn = min(wa, wb, wc)
            if mn > best:
                best = mn
                ids[p, 0] = a; ids[p, 1] = b; ids[p, 2] = c
                w[p, 0] = wa; w[p, 1] = wb; w[p, 2] = wc


class PWO3(pwo.PWO):
    def __init__(self, *a, fix="kernel", dump=False, rof=False, limit=False, **kw):
        super().__init__(*a, **kw)
        self.fix = fix
        self.rof = rof
        self.limit = limit
        self.n_rof = 0; self.n_limit = 0; self.n_limit_fail = 0
        self.dump = dump
        self.dumps = []
        # counters
        self.raw_iters = 0; self.raw_tri = 0; self.raw_leaves = 0
        self.n_kernel = 0; self.n_kernel_fail = 0; self.n_dp = 0; self.n_dp_fail = 0
        self.surv_iters = 0; self.surv_leaves = 0
        self.n_remap = 0

    def begin(self, fg, rho, grid, step):
        old = self.win
        if self.rof and old is not None and old.get("dirty") and self.rebuild_every > 1:
            self.wcount = (self.wcount // self.rebuild_every + 1) * self.rebuild_every
            self.n_rof += 1
        super().begin(fg, rho, grid, step)
        W = self.win
        if W is old or W is None or "vleaf" in W:
            return
        cen = W["cen"]
        K = len(cen)
        leaf_of_cen = np.full(len(W["P"]), -1, np.int32)
        leaf_of_cen[cen] = np.arange(K, dtype=np.int32)
        W["vleaf"] = leaf_of_cen[W["ids"][:, 0]]
        W["Q"] = np.ascontiguousarray(fg.coords)
        W["P0"] = W["P"].copy()
        W["ids0"] = W["ids"]; W["w0"] = W["w"]
        W["ids"] = W["ids0"].copy(); W["w"] = W["w0"].copy()
        W["nt"] = np.zeros(K, np.int64)
        W["tri"] = np.zeros((K, MAXT, 3), np.int64)
        W["flag"] = np.zeros(K, np.int32)
        W["dirty"] = False

    def _resolve(self, W, P):
        """Set centers/triangulations for the current node positions P. Returns the number of unresolved leaves."""
        t0 = time.perf_counter()
        bnd, nb, cen = W["bnd"], W["nb"], W["cen"]
        flag = W["flag"]
        nbad, ntri = _bad_leaves(P, bnd, nb, cen, flag)
        if self.fix == "none":
            if self.dump and nbad and len(self.dumps) < 30:
                for k in np.flatnonzero(flag > 0)[:3]:
                    self.dumps.append((P[bnd[k, :nb[k]]].copy(), W["P0"][bnd[k, :nb[k]]].copy(), P[cen[k]].copy()))
            return nbad, nbad, ntri
        nt_new = np.zeros_like(W["nt"])
        tri_new = W["tri"].copy() if "dp" in self.fix else W["tri"]
        bad = np.flatnonzero(flag > 0)
        if self.dump and len(bad) and len(self.dumps) < 30:
            for k in bad[:3]:
                self.dumps.append((P[bnd[k, :nb[k]]].copy(), W["P0"][bnd[k, :nb[k]]].copy(), P[cen[k]].copy()))
        unres = 0
        fix = self.fix
        if fix == "dpall":
            lst = np.arange(len(nb), dtype=np.int64)
            tri_new[:] = 0
            _dp_leaves(P, W["P0"], bnd, nb, lst, tri_new, nt_new)
            failed = lst[nt_new == 0]
            self.n_dp += len(lst)
            # leaves without a valid triangulation use the fan if it is valid
            fb = failed[flag[failed] == 0]
            self.n_dp_fail += len(failed)
            unres = int((flag[failed] > 0).sum())
            nt_new[fb] = 0
        elif len(bad):
            rem = bad
            if "kernel" in fix:
                okk = np.zeros(len(rem), np.bool_)
                _fix_kernel(P, bnd, nb, cen, rem, okk)
                self.n_kernel += int(okk.sum()); self.n_kernel_fail += int((~okk).sum())
                rem = rem[~okk]
            if "dp" in fix and len(rem):
                _dp_leaves(P, W["P0"], bnd, nb, rem, tri_new, nt_new)
                self.n_dp += len(rem)
                okd = nt_new[rem] > 0
                self.n_dp_fail += int((~okd).sum())
                rem = rem[~okd]
            unres = len(rem)
        changed = (nt_new != W["nt"]) | (nt_new > 0) & (tri_new != W["tri"]).reshape(len(nb), -1).any(1)
        if changed.any():
            _remap(W["vleaf"], W["Q"], changed, nt_new, tri_new, bnd, W["P0"], W["ids0"], W["w0"], W["ids"], W["w"])
            self.n_remap += 1
        W["nt"] = nt_new; W["tri"] = tri_new
        self._t("resolve", t0)
        return unres, nbad, ntri

    def _unres_leaves(self, W, P):
        """Leaves that stay unresolved at the node positions P (without changing the map state)."""
        flag = np.zeros(len(W["nb"]), np.int32)
        _bad_leaves(P, W["bnd"], W["nb"], W["cen"], flag)
        bad = np.flatnonzero(flag > 0)
        if len(bad) == 0:
            return bad
        Pc = P.copy()
        okk = np.zeros(len(bad), np.bool_)
        rem = bad
        if "kernel" in self.fix:
            _fix_kernel(Pc, W["bnd"], W["nb"], W["cen"], rem, okk)
            rem = rem[~okk]
        if "dp" in self.fix and len(rem):
            t = np.zeros((len(W["nb"]), MAXT, 3), np.int64); n = np.zeros(len(W["nb"]), np.int64)
            _dp_leaves(Pc, W["P0"], W["bnd"], W["nb"], rem, t, n)
            rem = rem[n[rem] == 0]
        return rem

    def advance(self, grid, vx, vy, dt):
        t0 = time.perf_counter()
        W = self.win
        P0 = W["P"]
        P = _disp(P0, grid.x_coords, grid.y_coords, vx, vy, dt, grid.dx, grid.dy, False)
        P[W["cen"]] = P[W["c4"]].mean(axis=1)
        unres, nbad, ntri = self._resolve(W, P)
        if nbad:
            self.raw_iters += 1; self.raw_tri += ntri; self.raw_leaves += nbad
            W["dirty"] = True
        if unres and self.limit:
            self.n_limit += 1
            Pn = P
            cur = P
            node_bad = np.zeros(len(Pn), bool)
            for rnd in range(6):
                lst = self._unres_leaves(W, cur)
                if len(lst) == 0:
                    break
                bn = W["bnd"][lst]
                node_bad[bn[bn >= 0]] = True
                node_bad[W["cen"][lst]] = True
                s_ = 0.5 ** (rnd + 1) if rnd < 5 else 0.0
                cur = P0 + np.where(node_bad[:, None], s_, 1.0) * (Pn - P0)
                cur[W["cen"]] = cur[W["c4"]].mean(axis=1)
            P = cur
            unres, _, _ = self._resolve(W, P)
            if unres:
                self.n_limit_fail += 1
        if unres and self.substep:
            self.n_retry += 1
            for n in (2, 4, 8, 16):
                P = P0
                for _ in range(n):
                    P = _disp(P, grid.x_coords, grid.y_coords, vx, vy, dt / n, grid.dx, grid.dy, False)
                    P[W["cen"]] = P[W["c4"]].mean(axis=1)
                unres, _, _ = self._resolve(W, P)
                if not unres:
                    break
            else:
                self.n_retry_fail += 1
        if unres:
            self.surv_iters += 1; self.surv_leaves += unres
        W["P"] = P
        r = pw._apply(W["ids"], W["w"], W["P"])
        self._t("advance", t0)
        return r


class NetHook:
    """Safety net: the crossing test and repair of validated windows, run only after a window in which an inversion
    survived. Plugs into the VW_HOOK sites of the algorithm; the repair (vwd.VW) splits the crossing segments at the
    midpoint of the window-start chord and replays the new vertices through the recorded steps of the window."""

    def __init__(self, pw):
        import vwd
        self.pw = pw
        self.nv = vwd.VW(min_len=1e-6, stop_rounds=3, skip_s_cross=True)
        self.S = None  # the algorithm tests `VW_HOOK.S is not None`
        self.n_checks = 0; self.n_repairs = 0; self.n_found = 0

    def reset(self):
        self.nv.reset(); self.S = None

    def start_window(self, fg, grid=None, best_state=None, step=0):
        self.nv.nwin_span = 0
        self.nv.start_window(fg, grid, best_state, step)
        self.S = self.nv.S
        return best_state

    def field(self, vx, vy):
        self.nv.field(vx, vy)

    def record(self, dt):
        self.nv.record(dt)

    def mark_best(self, fg):
        pass

    def restore(self, fg, coords):
        pass

    def repair(self, fg, grid, vx, vy, best_state, step, force=False):
        pw = self.pw
        if not pw.net_dirty:
            return best_state
        pw.net_dirty = False
        self.n_checks += 1
        nv = self.nv
        ne = len(nv.events)
        rep0 = nv.n_windows_repaired
        nv.repair(fg, grid, vx, vy, None, step, force=True)
        for new_idx, left, t, _ in nv.events[ne:]:
            n = len(pw.orig) + len(new_idx)
            is_new = np.zeros(n, bool); is_new[new_idx] = True
            o = np.zeros(n, bool); o[~is_new] = pw.orig; pw.orig = o
            pw.events.append(("ins", new_idx, left, left + 1, np.full(len(new_idx), float(t))))
        if nv.n_windows_repaired > rep0:
            self.n_repairs += 1
            self.n_found += len(nv.events[ne:][0][0]) if nv.events[ne:] else 0
        return best_state


class PWO3N(PWO3):
    def __init__(self, *a, net=False, **kw):
        super().__init__(*a, **kw)
        self.net = net
        self.net_dirty = False
        self.hook = NetHook(self) if net else None

    def advance(self, grid, vx, vy, dt):
        r = super().advance(grid, vx, vy, dt)
        if self.net:
            W = self.win
            # the last call of _resolve left the map state; survivors are detected from the counters
            if self.surv_iters != getattr(self, "_surv_seen", 0):
                self.net_dirty = True
                self._surv_seen = self.surv_iters
        return r
