"""Detection of crossing segments of a ring set with a uniform grid (numba).

Segments are the consecutive vertex pairs inside a ring (rings are closed lists, first == last).
A pair is reported if the two segments cross properly (strictly opposite orientations on both sides). Segments that
share an end point, identical segments of two rings (shared boundaries) and touching segments give an orientation of
exactly zero and are not reported.
"""
import numpy as np
from numba import njit, prange


@njit(cache=True, inline="always")
def _orient(ax, ay, bx, by, cx, cy):
    return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)


@njit(cache=True)
def _cross(c, a, b, p, q):
    ax, ay, bx, by = c[a, 0], c[a, 1], c[b, 0], c[b, 1]
    px, py, qx, qy = c[p, 0], c[p, 1], c[q, 0], c[q, 1]
    d1 = _orient(ax, ay, bx, by, px, py)
    d2 = _orient(ax, ay, bx, by, qx, qy)
    if not (d1 * d2 < 0):
        return False
    d3 = _orient(px, py, qx, qy, ax, ay)
    d4 = _orient(px, py, qx, qy, bx, by)
    return d3 * d4 < 0


@njit(cache=True, inline="always")
def _ci(x, x0, h, n):
    return max(0, min(int((x - x0) / h), n - 1))


@njit(cache=True)
def segment_first(offs):
    """Index of the first vertex of every segment (the segments of a ring are consecutive pairs)."""
    nr = offs.shape[0] - 1
    n = 0
    for r in range(nr):
        n += max(offs[r + 1] - offs[r] - 1, 0)
    first = np.empty(n, np.int64)
    k = 0
    for r in range(nr):
        for i in range(offs[r], offs[r + 1] - 1):
            first[k] = i
            k += 1
    return first


@njit(cache=True)
def grid_params(c, first, factor, maxfac):
    n = first.shape[0]
    mean = 0.0
    xmin = 1e300; ymin = 1e300; xmax = -1e300; ymax = -1e300
    for s in range(n):
        a = first[s]
        mean += np.hypot(c[a + 1, 0] - c[a, 0], c[a + 1, 1] - c[a, 1])
        xmin = min(xmin, c[a, 0], c[a + 1, 0]); xmax = max(xmax, c[a, 0], c[a + 1, 0])
        ymin = min(ymin, c[a, 1], c[a + 1, 1]); ymax = max(ymax, c[a, 1], c[a + 1, 1])
    mean /= max(n, 1)
    h = max(mean * factor, 1e-12)
    x0 = xmin - h
    y0 = ymin - h
    nx = int((xmax - x0) / h) + 2
    ny = int((ymax - y0) / h) + 2
    while nx * ny > maxfac * n + 1000:
        h *= 1.25
        nx = int((xmax - x0) / h) + 2
        ny = int((ymax - y0) / h) + 2
    return h, x0, y0, nx, ny


@njit(cache=True)
def build_grid(c, first, h, x0, y0, nx, ny):
    n = first.shape[0]
    cnt = np.zeros(nx * ny + 1, np.int64)
    for s in range(n):
        a = first[s]
        b = a + 1
        i0 = _ci(min(c[a, 0], c[b, 0]), x0, h, nx)
        i1 = _ci(max(c[a, 0], c[b, 0]), x0, h, nx)
        j0 = _ci(min(c[a, 1], c[b, 1]), y0, h, ny)
        j1 = _ci(max(c[a, 1], c[b, 1]), y0, h, ny)
        for j in range(j0, j1 + 1):
            for i in range(i0, i1 + 1):
                cnt[j * nx + i + 1] += 1
    for k in range(nx * ny):
        cnt[k + 1] += cnt[k]
    items = np.empty(cnt[nx * ny], np.int64)
    pos = cnt[:-1].copy()
    for s in range(n):
        a = first[s]
        b = a + 1
        i0 = _ci(min(c[a, 0], c[b, 0]), x0, h, nx)
        i1 = _ci(max(c[a, 0], c[b, 0]), x0, h, nx)
        j0 = _ci(min(c[a, 1], c[b, 1]), y0, h, ny)
        j1 = _ci(max(c[a, 1], c[b, 1]), y0, h, ny)
        for j in range(j0, j1 + 1):
            for i in range(i0, i1 + 1):
                items[pos[j * nx + i]] = s
                pos[j * nx + i] += 1
    return cnt, items


@njit(cache=True, parallel=True)
def scan(c, first, cnt, items, h, x0, y0, nx, ny, flag):
    """Flag the segments that cross another segment."""
    ncell = nx * ny
    for cell in prange(ncell):
        lo = cnt[cell]
        hi = cnt[cell + 1]
        if hi - lo < 2:
            continue
        ci = cell % nx
        cj = cell // nx
        for u in range(lo, hi):
            s = items[u]
            a = first[s]
            b = a + 1
            for w in range(u + 1, hi):
                t = items[w]
                p = first[t]
                q = p + 1
                # test the pair only in the cell that holds the min corner of the intersection of the boxes
                mx = max(min(c[a, 0], c[b, 0]), min(c[p, 0], c[q, 0]))
                my = max(min(c[a, 1], c[b, 1]), min(c[p, 1], c[q, 1]))
                if _ci(mx, x0, h, nx) != ci or _ci(my, y0, h, ny) != cj:
                    continue
                if _cross(c, a, b, p, q):
                    flag[s] = True
                    flag[t] = True


@njit(cache=True, parallel=True)
def twins(c, first, cnt, items, h, x0, y0, nx, ny, flag, out):
    """out[t] True for every segment t identical (as a point pair) to a flagged segment, flagged ones included."""
    n = flag.shape[0]
    for s in prange(n):
        if not flag[s]:
            continue
        a = first[s]
        b = a + 1
        out[s] = True
        # the cell of the first end point: identical segments cover it too
        i = _ci(min(c[a, 0], c[b, 0]), x0, h, nx)
        j = _ci(min(c[a, 1], c[b, 1]), y0, h, ny)
        cell = j * nx + i
        for u in range(cnt[cell], cnt[cell + 1]):
            t = items[u]
            p = first[t]
            q = p + 1
            if (c[a, 0] == c[p, 0] and c[a, 1] == c[p, 1] and c[b, 0] == c[q, 0] and c[b, 1] == c[q, 1]) or \
               (c[a, 0] == c[q, 0] and c[a, 1] == c[q, 1] and c[b, 0] == c[p, 0] and c[b, 1] == c[p, 1]):
                out[t] = True


@njit(cache=True)
def near_mask(c, first, cnt, items, h, x0, y0, nx, ny, flag, margin):
    """Segments that share a grid cell (or a cell within `margin` cells) with a flagged segment."""
    n = flag.shape[0]
    marked = np.zeros(nx * ny, np.bool_)
    for s in range(n):
        if not flag[s]:
            continue
        a = first[s]
        b = a + 1
        i0 = max(_ci(min(c[a, 0], c[b, 0]), x0, h, nx) - margin, 0)
        i1 = min(_ci(max(c[a, 0], c[b, 0]), x0, h, nx) + margin, nx - 1)
        j0 = max(_ci(min(c[a, 1], c[b, 1]), y0, h, ny) - margin, 0)
        j1 = min(_ci(max(c[a, 1], c[b, 1]), y0, h, ny) + margin, ny - 1)
        for j in range(j0, j1 + 1):
            for i in range(i0, i1 + 1):
                marked[j * nx + i] = True
    near = np.zeros(n, np.bool_)
    for cell in range(nx * ny):
        if marked[cell]:
            for u in range(cnt[cell], cnt[cell + 1]):
                near[items[u]] = True
    return near


class Grid:
    def __init__(self, c, offs=None, factor=3.0, maxfac=4, first=None):
        self.c = c
        if not np.isfinite(c).all():
            raise FloatingPointError('non-finite coordinates')
        self.first = segment_first(np.asarray(offs, dtype=np.int64)) if first is None else first
        self.h, self.x0, self.y0, self.nx, self.ny = grid_params(c, self.first, factor, maxfac)
        self.cnt, self.items = build_grid(c, self.first, self.h, self.x0, self.y0, self.nx, self.ny)

    def crossing(self):
        flag = np.zeros(len(self.first), np.bool_)
        scan(self.c, self.first, self.cnt, self.items, self.h, self.x0, self.y0, self.nx, self.ny, flag)
        return flag

    def near(self, flag, margin=1):
        return near_mask(self.c, self.first, self.cnt, self.items, self.h, self.x0, self.y0, self.nx, self.ny, flag, margin)

    def with_twins(self, flag):
        out = np.zeros(len(self.first), np.bool_)
        twins(self.c, self.first, self.cnt, self.items, self.h, self.x0, self.y0, self.nx, self.ny, flag, out)
        return out
