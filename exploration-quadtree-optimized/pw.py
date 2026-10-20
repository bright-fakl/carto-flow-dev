"""Prototype: piecewise-affine windows (quadtree + fan triangulation) inside the flow loop, by monkeypatching."""
import heapq, numpy as np
from numba import njit, prange
import carto_flow.flow_cartogram.algorithm as alg
from carto_flow.flow_cartogram.displacement import displace_coords_numba as _disp

@njit(cache=True)
def _grade(D):
    N = D.shape[0]
    changed = True
    while changed:
        changed = False
        for i in range(N):
            for j in range(N):
                d = D[i, j]
                for k in range(2):
                    ni = i + 1 if k == 0 else i
                    nj = j + 1 if k == 1 else j
                    if ni >= N or nj >= N:
                        continue
                    e = D[ni, nj]
                    if e > d + 1:
                        s = N >> d
                        i0 = i // s * s; j0 = j // s * s
                        D[i0:i0 + s, j0:j0 + s] = d + 1
                        changed = True
                    elif d > e + 1:
                        s = N >> e
                        i0 = ni // s * s; j0 = nj // s * s
                        D[i0:i0 + s, j0:j0 + s] = e + 1
                        changed = True

@njit(cache=True)
def _leaves(D):
    N = D.shape[0]
    nleaf = 0
    for i in range(N):
        for j in range(N):
            s = N >> D[i, j]
            if i % s == 0 and j % s == 0:
                nleaf += 1
    lid = np.empty((N, N), np.int32)
    org = np.empty((nleaf, 3), np.int32)  # row, col, size
    k = 0
    for i in range(N):
        for j in range(N):
            s = N >> D[i, j]
            if i % s == 0 and j % s == 0:
                org[k, 0] = i; org[k, 1] = j; org[k, 2] = s
                lid[i:i + s, j:j + s] = k
                k += 1
    # lattice node ids
    nid = -np.ones((N + 1) * (N + 1), np.int32)
    nodes = np.empty((nleaf * 8 + nleaf, 2))
    bnd = -np.ones((nleaf, 8), np.int32)
    nb = np.zeros(nleaf, np.int32)
    cen = np.empty(nleaf, np.int32)
    c4 = np.empty((nleaf, 4), np.int32)
    nn = 0
    for k in range(nleaf):
        i0 = org[k, 0]; j0 = org[k, 1]; s = org[k, 2]; d = D[i0, j0]
        # ccw in (x=col, y=row): bottom edge (row i0) left->right, right edge, top edge (row i0+s) right->left, left edge
        cnt = 0
        for side in range(4):
            if side == 0:
                cx, cy = j0, i0; ex, ey = s, 0
                nbi, nbj = i0 - 1, j0
            elif side == 1:
                cx, cy = j0 + s, i0; ex, ey = 0, s
                nbi, nbj = i0, j0 + s
            elif side == 2:
                cx, cy = j0 + s, i0 + s; ex, ey = -s, 0
                nbi, nbj = i0 + s, j0 + s - 1
            else:
                cx, cy = j0, i0 + s; ex, ey = 0, -s
                nbi, nbj = i0 + s - 1, j0 - 1
            for t in range(2):
                if t == 1:
                    # midpoint only when the neighbor across the edge is deeper
                    if nbi < 0 or nbj < 0 or nbi >= N or nbj >= N:
                        continue
                    if D[nbi, nbj] <= d:
                        continue
                    px = cx + ex // 2; py = cy + ey // 2
                else:
                    px = cx; py = cy
                key = py * (N + 1) + px
                if nid[key] < 0:
                    nid[key] = nn
                    nodes[nn, 0] = px; nodes[nn, 1] = py
                    nn += 1
                bnd[k, cnt] = nid[key]
                if t == 0:
                    c4[k, side] = nid[key]
                cnt += 1
            # order: corner, midpoint (if any) -> consistent ccw
        nb[k] = cnt
        nodes[nn, 0] = j0 + s / 2.0; nodes[nn, 1] = i0 + s / 2.0
        cen[k] = nn
        nn += 1
    return lid, org, bnd, nb, cen, nodes[:nn].copy(), c4

@njit(cache=True, parallel=True)
def _locate(u, v, lid, bnd, nb, cen, nodes):
    n = u.shape[0]
    N = lid.shape[0]
    ids = np.empty((n, 3), np.int32)
    w = np.empty((n, 3))
    for p in prange(n):
        col = min(max(int(np.floor(u[p])), 0), N - 1)
        row = min(max(int(np.floor(v[p])), 0), N - 1)
        k = lid[row, col]
        c = cen[k]
        cxy0 = nodes[c, 0]; cxy1 = nodes[c, 1]
        best = -1e300
        m = nb[k]
        for t in range(m):
            a = bnd[k, t]; b = bnd[k, (t + 1) % m]
            ax = nodes[a, 0] - cxy0; ay = nodes[a, 1] - cxy1
            bx = nodes[b, 0] - cxy0; by = nodes[b, 1] - cxy1
            px = u[p] - cxy0; py = v[p] - cxy1
            det = ax * by - ay * bx
            wa = (px * by - py * bx) / det
            wb = (ax * py - ay * px) / det
            wc = 1.0 - wa - wb
            mn = min(wa, wb, wc)
            if mn > best:
                best = mn
                ids[p, 0] = c; ids[p, 1] = a; ids[p, 2] = b
                w[p, 0] = wc; w[p, 1] = wa; w[p, 2] = wb
    return ids, w

@njit(cache=True, parallel=True)
def _apply(ids, w, P):
    n = ids.shape[0]
    out = np.empty((n, 2))
    for p in prange(n):
        a = ids[p, 0]; b = ids[p, 1]; c = ids[p, 2]
        out[p, 0] = w[p, 0] * P[a, 0] + w[p, 1] * P[b, 0] + w[p, 2] * P[c, 0]
        out[p, 1] = w[p, 0] * P[a, 1] + w[p, 1] * P[b, 1] + w[p, 2] * P[c, 1]
    return out

def build(rho, frac):
    ny, nx = rho.shape
    L = int(np.ceil(np.log2(max(nx, ny)))); N = 1 << L
    pad = np.full((N, N), rho.mean()); pad[:ny, :nx] = rho
    mx = [None] * (L + 1); mn = [None] * (L + 1)
    mx[L] = pad; mn[L] = pad
    for d in range(L - 1, -1, -1):
        a = mx[d + 1]; b = mn[d + 1]
        mx[d] = np.maximum.reduce([a[0::2, 0::2], a[1::2, 0::2], a[0::2, 1::2], a[1::2, 1::2]])
        mn[d] = np.minimum.reduce([b[0::2, 0::2], b[1::2, 0::2], b[0::2, 1::2], b[1::2, 1::2]])
    D = np.zeros((N, N), np.int8)
    target = max(int(nx * ny * frac), 4)
    heap = [(-(mx[0][0, 0] - mn[0][0, 0]), 0, 0, 0)]
    leaves = 1
    while heap and leaves < target:
        r, d, i, j = heapq.heappop(heap)
        if r == 0 or d == L:
            break
        s = N >> d
        D[i * s:(i + 1) * s, j * s:(j + 1) * s] = d + 1
        leaves += 3
        for di in (0, 1):
            for dj in (0, 1):
                ci, cj = 2 * i + di, 2 * j + dj
                if d + 1 < L:
                    heapq.heappush(heap, (-(mx[d + 1][ci, cj] - mn[d + 1][ci, cj]), d + 1, ci, cj))
    _grade(D)
    return _leaves(D), N

class State:
    frac = 2.0 ** -8
    center = 'mean'
    rho = None
    window = None
    stats = []
    t_build = 0.0

def _density(orig):
    def f(*a, **k):
        out = orig(*a, **k)
        State.rho = out[0]
        State.window = None
        return out
    return f

def _displace(coords, xc, yc, vx, vy, dt, dx, dy, use_parallel=True):
    import time
    W = State.window
    if W is None:
        t = time.perf_counter()
        ny, nx = len(yc), len(xc)
        x0 = xc[0] - dx / 2; y0 = yc[0] - dy / 2
        (lid, org, bnd, nb, cen, nodes, c4), N = build(State.rho, State.frac)
        u = (coords[:, 0] - x0) / dx; v = (coords[:, 1] - y0) / dy
        ids, w = _locate(u, v, lid, bnd, nb, cen, nodes)
        P = np.column_stack([x0 + nodes[:, 0] * dx, y0 + nodes[:, 1] * dy])
        W = State.window = dict(ids=ids, w=w, P=P, cen=cen, c4=c4)
        State.stats.append((len(nodes), len(org)))
        State.t_build += time.perf_counter() - t
    W["P"] = _disp(W["P"], xc, yc, vx, vy, dt, dx, dy, False)
    if State.center == "mean":
        W["P"][W["cen"]] = W["P"][W["c4"]].mean(axis=1)
    return _apply(W["ids"], W["w"], W["P"])

def install(frac=2.0 ** -8):
    State.frac = frac; State.stats = []; State.t_build = 0.0
    alg.compute_density_field_from_geometries = _density(alg.compute_density_field_from_geometries)
    alg.displace_coords_numba = _displace
