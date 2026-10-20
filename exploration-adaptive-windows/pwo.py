"""Optimized quadtree-window hook (after Miaji et al.): numba path without shapely round trips.

Per field window: graded quadtree from the density (pw.build), vertices inserted where a segment crosses a leaf edge or a fan
edge (pw2._count/_fill), vertices located in the fan triangles, nodes advected per iteration, piecewise-affine apply.
Inserted vertices of earlier windows are removed again (only inserted ones, never input vertices) when they lie within
`prune_tol` cells of the chord of their neighbors and the new chord crosses no segment (grid test, one pass).
Lineage: events ('rm', kept_idx) and ('ins', new_idx, pa, pb, pt); `backfill` lifts an earlier frame.
"""
import time
import numpy as np
from numba import njit, prange
import pw, pw2, xing
from carto_flow.flow_cartogram.displacement import displace_coords_numba as _disp
from vw import rebuild_metadata


@njit(cache=True)
def build_grid_m(c, first, marg, h, x0, y0, nx, ny):
    n = first.shape[0]
    cnt = np.zeros(nx * ny + 1, np.int64)
    for s in range(n):
        a = first[s]; b = a + 1
        i0 = max(xing._ci(min(c[a, 0], c[b, 0]), x0, h, nx) - marg[s], 0)
        i1 = min(xing._ci(max(c[a, 0], c[b, 0]), x0, h, nx) + marg[s], nx - 1)
        j0 = max(xing._ci(min(c[a, 1], c[b, 1]), y0, h, ny) - marg[s], 0)
        j1 = min(xing._ci(max(c[a, 1], c[b, 1]), y0, h, ny) + marg[s], ny - 1)
        for j in range(j0, j1 + 1):
            for i in range(i0, i1 + 1):
                cnt[j * nx + i + 1] += 1
    for k in range(nx * ny):
        cnt[k + 1] += cnt[k]
    items = np.empty(cnt[nx * ny], np.int64)
    pos = cnt[:-1].copy()
    for s in range(n):
        a = first[s]; b = a + 1
        i0 = max(xing._ci(min(c[a, 0], c[b, 0]), x0, h, nx) - marg[s], 0)
        i1 = min(xing._ci(max(c[a, 0], c[b, 0]), x0, h, nx) + marg[s], nx - 1)
        j0 = max(xing._ci(min(c[a, 1], c[b, 1]), y0, h, ny) - marg[s], 0)
        j1 = min(xing._ci(max(c[a, 1], c[b, 1]), y0, h, ny) + marg[s], ny - 1)
        for j in range(j0, j1 + 1):
            for i in range(i0, i1 + 1):
                items[pos[j * nx + i]] = s
                pos[j * nx + i] += 1
    return cnt, items


@njit(cache=True, inline="always")
def _pt_seg_dist2(px, py, ax, ay, bx, by):
    dx = bx - ax; dy = by - ay
    L2 = dx * dx + dy * dy
    t = 0.0
    if L2 > 0.0:
        t = ((px - ax) * dx + (py - ay) * dy) / L2
        t = min(max(t, 0.0), 1.0)
    qx = ax + t * dx - px; qy = ay + t * dy - py
    return qx * qx + qy * qy


@njit(cache=True)
def _on_run(c, ca, cb, x, y):
    for i in range(ca, cb + 1):
        if c[i, 0] == x and c[i, 1] == y:
            return True
    return False


@njit(cache=True, parallel=True)
def scan_q(c, first, cnt, items, h, x0, y0, nx, ny, query, flag, nseg, ca, cb, tol2, segsz, maxring):
    """Flag the chords (segments >= nseg) that cross a segment, or have a foreign vertex within sqrt(tol2) of them."""
    for cell in prange(nx * ny):
        lo = cnt[cell]; hi = cnt[cell + 1]
        if hi - lo < 2:
            continue
        anyq = False
        for u in range(lo, hi):
            if query[items[u]]:
                anyq = True
                break
        if not anyq:
            continue
        for u in range(lo, hi):
            s = items[u]
            if not query[s]:
                continue
            k = s - nseg
            a = first[s]; b = a + 1
            for w in range(lo, hi):
                t = items[w]
                if t == s:
                    continue
                p = first[t]; q = p + 1
                if t >= nseg:
                    if t < s:
                        continue
                    if xing._cross(c, a, b, p, q):
                        flag[s] = True
                        flag[t] = True
                    continue
                # t is a segment of the geometry
                tl = max(tol2, 0.0) ** 0.5
                if max(c[p, 0], c[q, 0]) < min(c[a, 0], c[b, 0]) - tl or min(c[p, 0], c[q, 0]) > max(c[a, 0], c[b, 0]) + tl:
                    continue
                if max(c[p, 1], c[q, 1]) < min(c[a, 1], c[b, 1]) - tl or min(c[p, 1], c[q, 1]) > max(c[a, 1], c[b, 1]) + tl:
                    continue
                if ca[k] <= p and p < cb[k]:
                    continue
                e1 = _on_run(c, ca[k], cb[k], c[p, 0], c[p, 1])
                e2 = _on_run(c, ca[k], cb[k], c[q, 0], c[q, 1])
                if e1 and e2:
                    continue
                if xing._cross(c, a, b, p, q):
                    flag[s] = True
                    continue
                touch = (c[p, 0] == c[a, 0] and c[p, 1] == c[a, 1]) or (c[p, 0] == c[b, 0] and c[p, 1] == c[b, 1]) or \
                        (c[q, 0] == c[a, 0] and c[q, 1] == c[a, 1]) or (c[q, 0] == c[b, 0] and c[q, 1] == c[b, 1])
                if touch or segsz[t] > maxring:
                    continue
                if tol2 > 0 and (not e1) and _pt_seg_dist2(c[p, 0], c[p, 1], c[a, 0], c[a, 1], c[b, 0], c[b, 1]) < tol2:
                    flag[s] = True
                    continue
                if tol2 > 0 and (not e2) and _pt_seg_dist2(c[q, 0], c[q, 1], c[a, 0], c[a, 1], c[b, 0], c[b, 1]) < tol2:
                    flag[s] = True


@njit(cache=True)
def _n_inverted(P, bnd, nb, cen):
    bad = 0
    for k in range(nb.shape[0]):
        c = cen[k]
        m = nb[k]
        for t in range(m):
            a = bnd[k, t]; b = bnd[k, (t + 1) % m]
            cr = (P[a, 0] - P[c, 0]) * (P[b, 1] - P[c, 1]) - (P[a, 1] - P[c, 1]) * (P[b, 0] - P[c, 0])
            if cr <= 0.0:
                bad += 1
    return bad


@njit(cache=True)
def _tri_areas(P, bnd, nb, cen):
    n = 0
    for k in range(nb.shape[0]):
        n += nb[k]
    out = np.empty(n)
    i = 0
    for k in range(nb.shape[0]):
        c = cen[k]
        m = nb[k]
        for t in range(m):
            a = bnd[k, t]; b = bnd[k, (t + 1) % m]
            out[i] = 0.5 * ((P[a, 0] - P[c, 0]) * (P[b, 1] - P[c, 1]) - (P[a, 1] - P[c, 1]) * (P[b, 0] - P[c, 0]))
            i += 1
    return out


@njit(cache=True, inline="always")
def _hash(x, y):
    h = np.int64(x * 1024.0) * np.int64(73856093) ^ np.int64(y * 1024.0) * np.int64(19349663)
    h = (h ^ (h >> 13)) * np.int64(1274126177)
    return h ^ (h >> 16)


@njit(cache=True, parallel=True)
def prune_mask2(c, rs, rn, orig, tol):
    """Inserted vertices within tol of the chord of their neighbors that are local maxima of a coordinate hash:
    no two adjacent vertices are removed, and the two rings of a shared boundary decide alike."""
    keep = np.ones(c.shape[0], np.bool_)
    for r in prange(rs.shape[0]):
        for j in range(1, rn[r] - 1):
            i = rs[r] + j
            if orig[i]:
                continue
            ux = c[i - 1, 0]; uy = c[i - 1, 1]; wx = c[i + 1, 0]; wy = c[i + 1, 1]
            lx = wx - ux; ly = wy - uy
            L = np.sqrt(lx * lx + ly * ly)
            if L < 1e-300:
                continue
            dev = abs((c[i, 0] - ux) * ly - (c[i, 1] - uy) * lx) / L
            tpar = ((c[i, 0] - ux) * lx + (c[i, 1] - uy) * ly) / (L * L)
            if dev < tol and tpar > 0.0 and tpar < 1.0:
                hi = _hash(c[i, 0], c[i, 1])
                if hi > _hash(ux, uy) and hi > _hash(wx, wy):
                    keep[i] = False
    return keep


@njit(cache=True)
def _run_dev(c, ca, cb):
    out = np.zeros(ca.shape[0])
    for k in range(ca.shape[0]):
        a = ca[k]; b = cb[k]
        m = 0.0
        for i in range(a + 1, b):
            d = _pt_seg_dist2(c[i, 0], c[i, 1], c[a, 0], c[a, 1], c[b, 0], c[b, 1])
            if d > m:
                m = d
        out[k] = m
    return out


@njit(cache=True)
def _restore_runs(keep, ca, cb, bad):
    for k in range(ca.shape[0]):
        if bad[k]:
            for i in range(ca[k], cb[k] + 1):
                keep[i] = True


def backfill(coords, events):
    for ev in events:
        if ev[0] == "rm":
            coords = coords[ev[1]]
        else:
            _, new_idx, pa, pb, pt = ev
            n = len(coords) + len(new_idx)
            is_new = np.zeros(n, bool); is_new[new_idx] = True
            out = np.empty((n, 2)); out[~is_new] = coords
            out[new_idx] = coords[pa] * (1 - pt)[:, None] + coords[pb] * pt[:, None]
            coords = out
    return coords


class PWO:
    def __init__(self, frac=2.0 ** -6, prune_tol=0.02, prune_every=1, budget=0, factor=6.0, rebuild_every=1, diag=False, substep=True, min_ratio=0.0, dist_test=True, maxring=64):
        self.maxring = maxring
        self.dist_test = dist_test
        self.substep = substep; self.n_retry = 0; self.n_retry_fail = 0; self.min_ratio = min_ratio
        self.diag = diag; self.inv_iters = 0; self.inv_tri = 0
        self.rebuild_every = rebuild_every; self.n_rebuilds = 0; self.n_forced = 0; self.wcount = 0
        self.frac = frac; self.prune_tol = prune_tol; self.prune_every = prune_every; self.budget = budget; self.factor = factor
        self.events = []; self.level_marks = []
        self.orig = None; self.win = None; self.nwin = 0
        self.nverts = []; self.t = {}; self.n_pruned = 0; self.n_inserted = 0; self.n_restored_runs = 0

    def _t(self, k, t0):
        self.t[k] = self.t.get(k, 0.0) + time.perf_counter() - t0

    def reset(self):
        self.level_marks.append(len(self.events)); self.win = None; self.wcount = 0

    def _write(self, fg, coords, offs):
        fg.coords = coords
        fg.ragged_offsets = (offs.astype(fg.ragged_offsets[0].dtype),) + tuple(fg.ragged_offsets[1:])
        fg.metadata = rebuild_metadata(fg.metadata, np.diff(offs))
        fg._ring_info = None; fg._polygon_indices = None
        fg.invalidate_cache()

    def _prune(self, coords, offs, orig, tolabs):
        rn = np.diff(offs); rs = offs[:-1]
        keep = prune_mask2(coords, rs, rn, orig, tolabs)
        if keep.all():
            return None
        N = len(coords)
        ringid = np.repeat(np.arange(len(rs)), rn)
        idx = np.flatnonzero(keep)
        a = idx[:-1]; b = idx[1:]
        cm = (ringid[a] == ringid[b]) & (b - a > 1)
        ca = a[cm]; cb = b[cm]; m = len(ca)
        if m == 0:
            return None
        dev = _run_dev(coords, ca, cb)
        tooflat = dev > tolabs * tolabs
        ta = time.perf_counter()
        cc = np.empty((N + 2 * m, 2)); cc[:N] = coords; cc[N::2] = coords[ca]; cc[N + 1::2] = coords[cb]
        f0 = xing.segment_first(offs)
        first = np.concatenate([f0, N + 2 * np.arange(m)])
        query = np.zeros(len(first), np.bool_); query[len(f0):] = True
        G = xing.Grid(cc, None, self.factor, first=first)
        h = max(G.h, 4.0 * tolabs)
        if h != G.h:
            G.h = h
            G.nx = int((cc[:, 0].max() - G.x0) / h) + 2; G.ny = int((cc[:, 1].max() - G.y0) / h) + 2
        marg = np.zeros(len(first), np.int64); marg[len(f0):] = 1
        cnt, items = build_grid_m(cc, first, marg, G.h, G.x0, G.y0, G.nx, G.ny)
        flag = np.zeros(len(first), np.bool_)
        segsz = np.concatenate([np.repeat(rn, np.maximum(rn - 1, 0)), np.zeros(m, np.int64)]).astype(np.int64)
        scan_q(cc, first, cnt, items, G.h, G.x0, G.y0, G.nx, G.ny, query, flag, len(f0), ca, cb, (1.05 * tolabs) ** 2 if self.dist_test else -1.0, segsz, self.maxring)
        self._t("prune_check", ta)
        bad = flag[len(f0):] | tooflat
        if bad.any():
            _restore_runs(keep, ca, cb, bad)
            self.n_restored_runs += int(bad.sum())
        return keep

    def begin(self, fg, rho, grid, step):
        t0 = time.perf_counter()
        self.wcount += 1
        if self.win is not None and self.rebuild_every > 1 and self.wcount % self.rebuild_every != 1 and len(self.win["ids"]) == len(fg.coords):
            W = self.win
            ok = _n_inverted(W["P"], W["bnd"], W["nb"], W["cen"]) == 0
            if ok and self.min_ratio > 0:
                ok = float((_tri_areas(W["P"], W["bnd"], W["nb"], W["cen"]) / W["A0"]).min()) >= self.min_ratio
            if ok:
                self._t("begin", t0)
                return
            self.n_forced += 1
        self.n_rebuilds += 1
        dx, dy = grid.dx, grid.dy
        x0 = grid.x_coords[0] - dx / 2; y0 = grid.y_coords[0] - dy / 2
        ta = time.perf_counter()
        (lid, org, bnd, nb, cen, nodes, c4), N = pw.build(rho, self.frac)
        self._t("mesh", ta)
        coords = fg.coords
        offs = np.asarray(fg.ragged_offsets[0], dtype=np.int64)
        if self.orig is None or len(self.orig) != len(coords):
            self.orig = np.ones(len(coords), bool)
        changed = False
        if self.prune_tol > 0 and (self.nwin % self.prune_every == 0 or (self.budget and len(coords) > self.budget)):
            ta = time.perf_counter()
            keep = self._prune(coords, offs, self.orig, self.prune_tol * min(dx, dy))
            if keep is not None and not keep.all():
                idx = np.flatnonzero(keep)
                ringid = np.repeat(np.arange(len(offs) - 1), np.diff(offs))
                offs = np.concatenate([[0], np.cumsum(np.bincount(ringid[idx], minlength=len(offs) - 1))]).astype(np.int64)
                self.n_pruned += len(coords) - len(idx)
                coords = coords[idx]; self.orig = self.orig[idx]
                self.events.append(("rm", idx)); changed = True
            self._t("prune", ta)
        ta = time.perf_counter()
        lat = np.column_stack([(coords[:, 0] - x0) / dx, (coords[:, 1] - y0) / dy])
        rs = offs[:-1]; rn = np.diff(offs)
        cnt = pw2._count(lat, rs, rn, lid, bnd, nb, cen, nodes)
        if cnt.sum() > 0:
            newn = rn + cnt
            newstart = np.concatenate([[0], np.cumsum(newn)[:-1]]).astype(np.int64)
            tot = int(newn.sum())
            outc = np.empty((tot, 2)); pa = np.empty(tot, np.int64); pb = np.empty(tot, np.int64); pt = np.empty(tot)
            pw2._fill(lat, coords, rs, rn, newstart, lid, bnd, nb, cen, nodes, x0, y0, dx, dy, outc, pa, pb, pt)
            offs = np.concatenate([[0], np.cumsum(newn)]).astype(np.int64)
            new = pa != pb
            ni = np.flatnonzero(new)
            self.events.append(("ins", ni, pa[ni], pb[ni], pt[ni]))
            self.n_inserted += len(ni)
            self.orig = (~new) & self.orig[pa]
            coords = outc; changed = True
            lat = np.column_stack([(coords[:, 0] - x0) / dx, (coords[:, 1] - y0) / dy])
        self._t("insert", ta)
        if changed:
            ta = time.perf_counter()
            self._write(fg, coords, offs)
            self._t("write", ta)
        ta = time.perf_counter()
        ids, w = pw._locate(lat[:, 0].copy(), lat[:, 1].copy(), lid, bnd, nb, cen, nodes)
        P = np.column_stack([x0 + nodes[:, 0] * dx, y0 + nodes[:, 1] * dy])
        self.win = dict(ids=ids, w=w, P=P, cen=cen, c4=c4, bnd=bnd, nb=nb, A0=_tri_areas(P, bnd, nb, cen))
        self._t("locate", ta)
        self.nverts.append(len(coords)); self.nwin += 1
        self._t("begin", t0)

    def advance(self, grid, vx, vy, dt):
        t0 = time.perf_counter()
        W = self.win
        P0 = W["P"]
        P = _disp(P0, grid.x_coords, grid.y_coords, vx, vy, dt, grid.dx, grid.dy, False)
        P[W["cen"]] = P[W["c4"]].mean(axis=1)
        if self.substep and _n_inverted(P, W["bnd"], W["nb"], W["cen"]):
            self.n_retry += 1
            for n in (2, 4, 8, 16):
                P = P0
                for _ in range(n):
                    P = _disp(P, grid.x_coords, grid.y_coords, vx, vy, dt / n, grid.dx, grid.dy, False)
                    P[W["cen"]] = P[W["c4"]].mean(axis=1)
                if not _n_inverted(P, W["bnd"], W["nb"], W["cen"]):
                    break
            else:
                self.n_retry_fail += 1
        W["P"] = P
        if self.diag:
            nb_ = _n_inverted(W["P"], W["bnd"], W["nb"], W["cen"])
            if nb_:
                self.inv_iters += 1; self.inv_tri += int(nb_)
        r = pw._apply(W["ids"], W["w"], W["P"])
        self._t("advance", t0)
        return r

    def structure(self, fg):
        return (np.asarray(fg.ragged_offsets[0], dtype=np.int64).copy(), self.orig.copy(), len(self.events))

    def restore(self, fg, coords, nev):
        offs, orig, nev_len = nev
        self.orig = orig
        del self.events[nev_len:]
        self._write(fg, coords, offs)
