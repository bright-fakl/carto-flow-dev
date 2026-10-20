"""Prototype hook: quadtree + fan triangulation window with vertex insertion at triangle-edge crossings."""
import time, numpy as np, shapely
from numba import njit, prange
import pw, xing
from carto_flow.flow_cartogram.displacement import displace_coords_numba as _disp
from carto_flow.geo_utils.geometry import unpack_geometries

BUF = 512

@njit(cache=True)
def _seg_ts(ax, ay, bx, by, lid, bnd, nb, cen, nodes, buf):
    N = lid.shape[0]
    n = 0
    dxs = bx - ax; dys = by - ay
    if dxs != 0.0:
        lo = min(ax, bx); hi = max(ax, bx)
        for k in range(int(np.ceil(lo)), int(np.floor(hi)) + 1):
            if k <= 0 or k >= N:
                continue
            t = (k - ax) / dxs
            if t <= 1e-12 or t >= 1 - 1e-12:
                continue
            row = int(np.floor(ay + t * dys))
            if row < 0 or row >= N:
                continue
            if lid[row, k - 1] != lid[row, k] and n < BUF - 1:
                buf[n] = t; n += 1
    if dys != 0.0:
        lo = min(ay, by); hi = max(ay, by)
        for k in range(int(np.ceil(lo)), int(np.floor(hi)) + 1):
            if k <= 0 or k >= N:
                continue
            t = (k - ay) / dys
            if t <= 1e-12 or t >= 1 - 1e-12:
                continue
            col = int(np.floor(ax + t * dxs))
            if col < 0 or col >= N:
                continue
            if lid[k - 1, col] != lid[k, col] and n < BUF - 1:
                buf[n] = t; n += 1
    for i in range(1, n):
        v = buf[i]; j = i - 1
        while j >= 0 and buf[j] > v:
            buf[j + 1] = buf[j]; j -= 1
        buf[j + 1] = v
    m = n
    t0 = 0.0
    for j in range(n + 1):
        t1 = buf[j] if j < n else 1.0
        tm = 0.5 * (t0 + t1)
        col = min(max(int(np.floor(ax + tm * dxs)), 0), N - 1)
        row = min(max(int(np.floor(ay + tm * dys)), 0), N - 1)
        k = lid[row, col]
        c = cen[k]
        cx = nodes[c, 0]; cy = nodes[c, 1]
        for e in range(nb[k]):
            b = bnd[k, e]
            sx = nodes[b, 0] - cx; sy = nodes[b, 1] - cy
            den = dxs * sy - dys * sx
            if abs(den) < 1e-14:
                continue
            s = ((cx - ax) * sy - (cy - ay) * sx) / den
            r = ((cx - ax) * dys - (cy - ay) * dxs) / den
            if r >= 0.0 and r <= 1.0 and s > t0 + 1e-9 and s < t1 - 1e-9 and m < BUF:
                buf[m] = s; m += 1
        t0 = t1
    for i in range(1, m):
        v = buf[i]; j = i - 1
        while j >= 0 and buf[j] > v:
            buf[j + 1] = buf[j]; j -= 1
        buf[j + 1] = v
    # dedupe
    out = 0
    last = 0.0
    for i in range(m):
        if buf[i] - last > 1e-9 and 1.0 - buf[i] > 1e-9:
            buf[out] = buf[i]; out += 1; last = buf[i]
    return out

@njit(cache=True, parallel=True)
def _count(lat, rs, rn, lid, bnd, nb, cen, nodes):
    nr = rs.shape[0]
    cnt = np.zeros(nr, np.int64)
    for r in prange(nr):
        buf = np.empty(BUF)
        tot = 0
        for j in range(rn[r] - 1):
            p = rs[r] + j; q = p + 1
            if lat[p, 0] > lat[q, 0] or (lat[p, 0] == lat[q, 0] and lat[p, 1] > lat[q, 1]):
                a = q; b = p
            else:
                a = p; b = q
            tot += _seg_ts(lat[a, 0], lat[a, 1], lat[b, 0], lat[b, 1], lid, bnd, nb, cen, nodes, buf)
        cnt[r] = tot
    return cnt

@njit(cache=True, parallel=True)
def _fill(lat, phys, rs, rn, newstart, lid, bnd, nb, cen, nodes, x0, y0, dx, dy, outc, pa, pb, pt):
    nr = rs.shape[0]
    for r in prange(nr):
        buf = np.empty(BUF)
        o = newstart[r]
        for j in range(rn[r] - 1):
            p = rs[r] + j; q = p + 1
            outc[o, 0] = phys[p, 0]; outc[o, 1] = phys[p, 1]; pa[o] = p; pb[o] = p; pt[o] = 0.0; o += 1
            swap = lat[p, 0] > lat[q, 0] or (lat[p, 0] == lat[q, 0] and lat[p, 1] > lat[q, 1])
            if swap:
                a = q; b = p
            else:
                a = p; b = q
            ax = lat[a, 0]; ay = lat[a, 1]; bx = lat[b, 0]; by = lat[b, 1]
            n = _seg_ts(ax, ay, bx, by, lid, bnd, nb, cen, nodes, buf)
            for ii in range(n):
                i = n - 1 - ii if swap else ii
                t = buf[i]
                outc[o, 0] = x0 + (ax + t * (bx - ax)) * dx
                outc[o, 1] = y0 + (ay + t * (by - ay)) * dy
                pa[o] = p; pb[o] = q; pt[o] = (1.0 - t) if swap else t
                o += 1
        last = rs[r] + rn[r] - 1
        outc[o, 0] = phys[last, 0]; outc[o, 1] = phys[last, 1]; pa[o] = last; pb[o] = last; pt[o] = 0.0

@njit(cache=True, parallel=True)
def _prune_mask(c, rs, rn, orig, tol):
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
            # projection must fall within the chord
            tpar = ((c[i, 0] - ux) * lx + (c[i, 1] - uy) * ly) / (L * L)
            if dev < tol and tpar > 0.0 and tpar < 1.0:
                keep[i] = False
    return keep

def _match(old, oo, new, no):
    import pandas as pd
    ro = np.repeat(np.arange(len(oo) - 1), np.diff(oo)); rn_ = np.repeat(np.arange(len(no) - 1), np.diff(no))
    lo = np.ones(len(old), bool); lo[oo[1:] - 1] = False
    ln = np.ones(len(new), bool); ln[no[1:] - 1] = False
    om = pd.MultiIndex.from_arrays([ro[lo], old[lo, 0], old[lo, 1]])
    nm = pd.MultiIndex.from_arrays([rn_[ln], new[ln, 0], new[ln, 1]])
    if not om.is_unique:
        return -np.ones(len(new), np.int64)
    pos_old = np.flatnonzero(lo)
    k = om.get_indexer(nm)
    idx = -np.ones(len(new), np.int64)
    ok = k >= 0
    sel = np.flatnonzero(ln)
    idx[sel[ok]] = pos_old[k[ok]]
    idx[sel[~ok]] = -1
    idx[no[1:] - 1] = idx[no[:-1]]
    return idx

class Hook:
    def __init__(self, frac=2.0 ** -6, insert=True):
        self.frac = frac; self.insert = insert
        self.events = []; self.win = None
        self.nverts = []; self.t_build = 0.0; self.t_insert = 0.0
        self.orig = None; self.tol = 0.02; self.pruned = 0; self.dbg = False; self.log = []; self.inv = []

    def begin(self, fg, rho, grid, step):
        t = time.perf_counter()
        if self.win is not None and self.dbg:
            self.inv.append((step, self.inverted(self.win)))
        dx, dy = grid.dx, grid.dy
        x0 = grid.x_coords[0] - dx / 2; y0 = grid.y_coords[0] - dy / 2
        (lid, org, bnd, nb, cen, nodes, c4), N = pw.build(rho, self.frac)
        coords = fg.coords
        if self.orig is None or len(self.orig) != len(coords):
            self.orig = np.ones(len(coords), bool)
        if getattr(self,'dbg',False):
            self._n_before = int((~shapely.is_valid(shapely.from_ragged_array(fg.ragged_geometry_type, coords, fg.ragged_offsets))).sum())
        if self.insert and getattr(self, "cov", 0) > 0:
            offs = fg.ragged_offsets[0]
            rn = np.diff(offs).astype(np.int64)
            geoms = shapely.from_ragged_array(fg.ragged_geometry_type, coords, fg.ragged_offsets)
            simp = shapely.coverage_simplify(geoms, self.cov * min(dx, dy))
            _gt, newc, noffs = shapely.to_ragged_array(simp)
            nrn = np.diff(noffs[0]).astype(np.int64)
            if len(newc) < len(coords) and len(nrn) == len(rn):
                idx = _match(coords, offs.astype(np.int64), newc, noffs[0].astype(np.int64))
                if (idx >= 0).all():
                    self._restructure(fg, newc, noffs[0].astype(offs.dtype))
                    self.events.append((idx, idx, np.zeros(len(idx))))
                    self.pruned += len(coords) - len(newc)
                    coords = newc
                else:
                    self.nomatch = getattr(self, "nomatch", 0) + 1
        if self.insert and self.tol > 0 and getattr(self, "cov", 0) == 0:
            offs = fg.ragged_offsets[0]
            rs = np.asarray(offs[:-1], dtype=np.int64); rn = np.diff(offs).astype(np.int64)
            keep = _prune_mask(coords, rs, rn, self.orig, self.tol * min(dx, dy))
            if getattr(self, 'safe', False) and not keep.all():
                ringid = np.repeat(np.arange(len(rs)), rn)
                for it in range(30):
                    idx = np.flatnonzero(keep)
                    newn = np.bincount(ringid[idx], minlength=len(rs))
                    no = np.concatenate([[0], np.cumsum(newn)]).astype(np.int64)
                    G = xing.Grid(coords[idx], no, 6.0)
                    fl = G.crossing()
                    if not fl.any():
                        break
                    fs = G.first[fl]
                    for a_, b_ in zip(idx[fs], idx[fs + 1]):
                        keep[a_:b_ + 1] = True
                    self.safe_restored = getattr(self, 'safe_restored', 0) + int(fl.sum())
            if not keep.all():
                idx = np.flatnonzero(keep)
                ringid = np.repeat(np.arange(len(rs)), rn)
                newn = np.bincount(ringid[idx], minlength=len(rs))
                new_offs = np.concatenate([[0], np.cumsum(newn)]).astype(offs.dtype)
                outc = coords[idx]
                self._restructure(fg, outc, new_offs)
                self.events.append((idx, idx, np.zeros(len(idx))))
                self.orig = self.orig[idx]
                self.pruned += int((~keep).sum())
                coords = outc
        if getattr(self,'dbg',False):
            na = int((~shapely.is_valid(shapely.from_ragged_array(fg.ragged_geometry_type, coords, fg.ragged_offsets))).sum())
            self.log.append((step, len(coords), self._n_before, na))
        if self.insert:
            ti = time.perf_counter()
            lat = np.column_stack([(coords[:, 0] - x0) / dx, (coords[:, 1] - y0) / dy])
            offs = fg.ragged_offsets[0]
            rs = np.asarray(offs[:-1], dtype=np.int64); rn = np.diff(offs).astype(np.int64)
            cnt = pw._count_ = _count(lat, rs, rn, lid, bnd, nb, cen, nodes)
            if cnt.sum() > 0:
                newn = rn + cnt
                newstart = np.concatenate([[0], np.cumsum(newn)[:-1]]).astype(np.int64)
                tot = int(newn.sum())
                outc = np.empty((tot, 2)); pa = np.empty(tot, np.int64); pb = np.empty(tot, np.int64); pt = np.empty(tot)
                _fill(lat, coords, rs, rn, newstart, lid, bnd, nb, cen, nodes, x0, y0, dx, dy, outc, pa, pb, pt)
                new_offs = np.concatenate([[0], np.cumsum(newn)]).astype(offs.dtype)
                self._restructure(fg, outc, new_offs)
                self.events.append((pa, pb, pt))
                self.orig = np.concatenate([self.orig, np.zeros(0, bool)])[:0] if False else (pt == 0.0) & (pa == pb) & self.orig[pa]
                coords = outc
            self.t_insert += time.perf_counter() - ti
        u = (coords[:, 0] - x0) / dx; v = (coords[:, 1] - y0) / dy
        ids, w = pw._locate(u, v, lid, bnd, nb, cen, nodes)
        P = np.column_stack([x0 + nodes[:, 0] * dx, y0 + nodes[:, 1] * dy])
        self.win = dict(ids=ids, w=w, P=P, cen=cen, c4=c4, bnd=bnd, nb=nb)
        self.nverts.append(len(coords)); self.t_build += time.perf_counter() - t

    def _restructure(self, fg, outc, new_offs):
        geoms = list(shapely.from_ragged_array(fg.ragged_geometry_type, outc, (new_offs,) + tuple(fg.ragged_offsets[1:])))
        info = unpack_geometries(geoms)
        fg.coords = outc
        fg.metadata = info.metadata
        fg.ragged_offsets = info.ragged_offsets
        fg._ring_info = None; fg._polygon_indices = None
        fg.invalidate_cache()

    @staticmethod
    def inverted(W):
        P = W["P"]; bnd = W["bnd"]; nb = W["nb"]; cen = W["cen"]
        bad = 0; tot = 0
        for t in range(8):
            ok = nb > t
            a = bnd[ok, t]; b = bnd[ok, (t + 1) % 8] if False else None
        # per leaf triangle (c, b_t, b_{t+1 mod nb})
        K = len(nb)
        idx = np.arange(K)
        for t in range(8):
            ok = nb > t
            a = bnd[idx[ok], t]
            b = bnd[idx[ok], (t + 1) % nb[ok]]
            c = cen[ok]
            cr = (P[a, 0] - P[c, 0]) * (P[b, 1] - P[c, 1]) - (P[a, 1] - P[c, 1]) * (P[b, 0] - P[c, 0])
            bad += int((cr <= 0).sum()); tot += len(cr)
        return bad, tot

    def advance(self, grid, vx, vy, dt):
        W = self.win
        W["P"] = _disp(W["P"], grid.x_coords, grid.y_coords, vx, vy, dt, grid.dx, grid.dy, False)
        W["P"][W["cen"]] = W["P"][W["c4"]].mean(axis=1)
        return pw._apply(W["ids"], W["w"], W["P"])

    def structure(self, fg):
        return tuple(np.array(o) for o in fg.ragged_offsets)

    def restore(self, fg, coords, offsets):
        self._restructure_full(fg, coords, offsets)

    def _restructure_full(self, fg, outc, offsets):
        geoms = list(shapely.from_ragged_array(fg.ragged_geometry_type, outc, offsets))
        info = unpack_geometries(geoms)
        fg.coords = outc
        fg.metadata = info.metadata
        fg.ragged_offsets = info.ragged_offsets
        fg._ring_info = None; fg._polygon_indices = None
        fg.invalidate_cache()

    def lift(self, c, since):
        for pa, pb, pt in self.events[since:]:
            c = c[pa] * (1 - pt)[:, None] + c[pb] * pt[:, None]
        return c
