"""Validated windows: after a window of iterations (the field is fixed inside a window), detect crossing segments in the
current state and split them at the midpoint of the window-start chord; the new vertices are advected through the
recorded steps of the window (replay), so they lie on the true flow path. Original vertices are never removed or moved.
"""
import time
import numpy as np
from numba import njit
from carto_flow.flow_cartogram.displacement import displace_coords_numba
import xing


@njit(cache=True)
def split_segments(S, E, B, offs, split, loc):
    """Insert the (canonical) midpoint of the window-start chord into the segments with split[k] True.

    Returns the new S, E, B (the new vertices hold the S midpoint in all three), the new offsets, the indices of the new
    vertices in the new structure and, for each, the index of its left end point in the old structure.
    """
    nr = offs.shape[0] - 1
    nsplit = 0
    for k in range(split.shape[0]):
        if split[k]:
            nsplit += 1
    n_new = S.shape[0] + nsplit
    So = np.empty((n_new, 2)); Eo = np.empty((n_new, 2)); Bo = np.empty((n_new, 2))
    noffs = np.empty(nr + 1, np.int64)
    new_idx = np.empty(nsplit, np.int64)
    nseg_new = split.shape[0] + nsplit
    loc_new = np.zeros(nseg_new, np.bool_)
    kn = 0
    left = np.empty(nsplit, np.int64)
    o = 0
    k = 0
    m = 0
    for r in range(nr):
        noffs[r] = o
        for i in range(offs[r], offs[r + 1] - 1):
            So[o] = S[i]; Eo[o] = E[i]; Bo[o] = B[i]
            o += 1
            if split[k]:
                ax, ay, bx, by = S[i, 0], S[i, 1], S[i + 1, 0], S[i + 1, 1]
                if ax > bx or (ax == bx and ay > by):
                    ax, ay, bx, by = bx, by, ax, ay
                mx = ax + 0.5 * (bx - ax)
                my = ay + 0.5 * (by - ay)
                So[o, 0] = mx; So[o, 1] = my
                Eo[o, 0] = mx; Eo[o, 1] = my
                Bo[o, 0] = mx; Bo[o, 1] = my
                new_idx[m] = o
                loc_new[kn] = loc[k]; loc_new[kn + 1] = loc[k]
                kn += 2
                left[m] = i
                m += 1
                o += 1
            else:
                loc_new[kn] = loc[k]
                kn += 1
            k += 1
        last = offs[r + 1] - 1
        So[o] = S[last]; Eo[o] = E[last]; Bo[o] = B[last]
        o += 1
    noffs[nr] = o
    return So, Eo, Bo, noffs, new_idx, left, loc_new


@njit(cache=True)
def lift_best(Bo, new_idx, left_new, B_old_of_new_left, B_old_of_new_right):
    for m in range(new_idx.shape[0]):
        Bo[new_idx[m], 0] = 0.5 * (B_old_of_new_left[m, 0] + B_old_of_new_right[m, 0])
        Bo[new_idx[m], 1] = 0.5 * (B_old_of_new_left[m, 1] + B_old_of_new_right[m, 1])


def rebuild_metadata(metadata, ring_sizes):
    out = []
    r = 0
    for m in metadata:
        t = m["type"]
        if t == "Polygon":
            nh = len(m["hole_sizes"])
            sizes = ring_sizes[r:r + 1 + nh]
            out.append({"type": "Polygon", "exterior_size": int(sizes[0]), "hole_sizes": [int(x) for x in sizes[1:]]})
            r += 1 + nh
        elif t == "MultiPolygon":
            pm = []
            for p in m["polygon_metadata"]:
                nh = len(p["hole_sizes"])
                sizes = ring_sizes[r:r + 1 + nh]
                pm.append({"type": "Polygon", "exterior_size": int(sizes[0]), "hole_sizes": [int(x) for x in sizes[1:]]})
                r += 1 + nh
            out.append({"type": "MultiPolygon", "polygon_metadata": pm})
        else:
            raise ValueError(t)
    assert r == len(ring_sizes)
    return out


@njit(cache=True)
def long_mask(c, offs, thr2):
    nr = offs.shape[0] - 1
    n = 0
    for r in range(nr):
        n += max(offs[r + 1] - offs[r] - 1, 0)
    m = np.zeros(n, np.bool_)
    k = 0
    for r in range(nr):
        for i in range(offs[r], offs[r + 1] - 1):
            dx = c[i + 1, 0] - c[i, 0]
            dy = c[i + 1, 1] - c[i, 1]
            if dx * dx + dy * dy > thr2:
                m[k] = True
            k += 1
    return m


class VW:
    def __init__(self, depth=14, factor=6.0, local=True, max_len=0.0, min_len=1e-7, check_every=1, stop_rounds=0, check_best=True, f32=False, mem_budget_mb=0):
        self.f32 = f32
        self.mem_budget = int(mem_budget_mb * 2 ** 20)
        self.max_field_bytes = 0
        self.check_best = check_best
        self.check_every = check_every
        self.stop_rounds = stop_rounds
        self.min_len = min_len
        self.max_len = max_len
        self.local = local
        self.verbose = False
        self.level_marks = []
        self.dump_fail = None
        self.depth = depth
        self.factor = factor
        self.S = None
        self.dts = []
        self.fields = []
        self.span = 0
        self.nwin_span = 0
        self.best_span = -1
        self.best_window = -1
        self.best_k = None  # number of steps after the window start at which the best state was reached
        self.best_offs = None
        self.events = []  # (pa, pb, pt, step) per insertion round
        self.t_detect = 0.0
        self.t_repair = 0.0
        self.n_rounds = 0
        self.n_windows_repaired = 0
        self.n_windows = 0
        self.n_inserted = 0
        self.n_inserted_long = 0
        self.unresolved = 0
        self.log = []
        self.tm = {}

    def _t(self, k, t0):
        self.tm[k] = self.tm.get(k, 0.0) + time.perf_counter() - t0

    # -- loop interface -------------------------------------------------
    def reset(self):
        self.S = None; self.dts = []; self.fields = []; self.span = 0; self.nwin_span = 0; self.best_span = -1; self.best_k = None; self.best_offs = None; self.level_marks.append(len(self.events))

    def split_long(self, fg, grid, best_state, step):
        """Split the segments longer than max_len cells (midpoint of the chord); the polygon does not change."""
        thr2 = (self.max_len * min(grid.dx, grid.dy)) ** 2
        for rnd in range(12):
            offs = np.asarray(fg.ragged_offsets[0], dtype=np.int64)
            m = long_mask(fg.coords, offs, thr2)
            if not m.any():
                break
            E = fg.coords
            B = best_state[0] if best_state is not None else E
            S0 = self.S if self.S is not None else E
            So, Eo, Bo, noffs, new_idx, left, _ = split_segments(S0, E, B, offs, m, np.zeros(len(m), np.bool_))
            Eo[new_idx] = 0.5 * (E[left] + E[left + 1])
            if best_state is not None:
                Bo[new_idx] = 0.5 * (B[left] + B[left + 1])
                best_state = (Bo,) + tuple(best_state[1:])
                self.best_offs = noffs.copy()
            if self.S is not None:
                self.S = So
            self.events.append((new_idx, left, 0.5, step))
            self.n_inserted_long += len(new_idx)
            if self.verbose: print(f'  split_long step {step} round {rnd} n {len(new_idx)} total {len(Eo)}', flush=True)
            self._write(fg, Eo, noffs)
        return best_state

    def _write(self, fg, E, offs):
        fg.coords = E
        fg.ragged_offsets = (offs.astype(fg.ragged_offsets[0].dtype),) + tuple(fg.ragged_offsets[1:])
        fg.metadata = rebuild_metadata(fg.metadata, np.diff(offs))
        fg._ring_info = None; fg._polygon_indices = None
        fg.invalidate_cache()

    def start_window(self, fg, grid=None, best_state=None, step=0):
        if self.max_len > 0 and grid is not None:
            best_state = self.split_long(fg, grid, best_state, step)
        if self.S is None or self.nwin_span == 0:
            self.S = fg.coords.copy()
            self.fields = []
            self.span += 1
        self.nwin_span += 1
        self.dts = []
        self.fields.append([None, None, self.dts])
        self.n_windows += 1
        return best_state

    def field(self, vx, vy):
        dt_ = np.float32 if self.f32 else vx.dtype
        self.fields[-1][0] = vx.astype(dt_)
        self.fields[-1][1] = vy.astype(dt_)
        nb = sum(f[0].nbytes + f[1].nbytes for f in self.fields if f[0] is not None)
        self.max_field_bytes = max(self.max_field_bytes, nb)

    def record(self, dt):
        self.dts.append(dt)

    def mark_best(self, fg):
        self.best_k = sum(len(f[2]) for f in self.fields)
        self.best_span = self.span
        self.best_offs = np.asarray(fg.ragged_offsets[0], dtype=np.int64).copy()

    def _over_budget(self):
        if not self.mem_budget:
            return False
        return sum(f[0].nbytes + f[1].nbytes for f in self.fields if f[0] is not None) >= self.mem_budget

    def _replay(self, P, grid, vx, vy, upto):
        out = {}
        k = 0
        for fvx, fvy, dts in self.fields:
            if fvx is None:
                fvx, fvy = vx, vy
            for dt in dts:
                P = displace_coords_numba(P, grid.x_coords, grid.y_coords, fvx, fvy, dt, grid.dx, grid.dy, use_parallel=False)
                k += 1
                out[k] = P
        return out

    def repair(self, fg, grid, vx, vy, best_state, step, force=False):
        """Split the crossing segments of the current state. Returns the (possibly updated) best_state."""
        if self.S is None or not self.dts:
            return best_state
        if not force and self.nwin_span < self.check_every and not self._over_budget():
            return best_state
        self.nwin_span = 0
        t0 = time.perf_counter()
        E = fg.coords
        offs = np.asarray(fg.ragged_offsets[0], dtype=np.int64)
        g = xing.Grid(E, offs, self.factor)
        if self.verbose: print(f'  detect step {step} nseg {len(g.first)} grid {g.nx}x{g.ny} t_build {time.perf_counter()-t0:.2f}', flush=True)
        flag = g.crossing()
        has_best = best_state is not None
        B = best_state[0] if has_best else E
        best_in_window = has_best and self.best_span == self.span and self.check_best
        if best_in_window:
            gB = xing.Grid(B, offs, self.factor)
            flag |= gB.crossing()
        self.t_detect += time.perf_counter() - t0
        if self.verbose: print(f'  detect step {step} flagged {int(flag.sum())} t {time.perf_counter()-t0:.2f}', flush=True)
        if not flag.any():
            return best_state
        t1 = time.perf_counter()
        S = self.S
        self.S0, self.E0, self.offs0 = S.copy(), E.copy(), offs.copy()
        best_in_window = has_best and self.best_span == self.span
        nd = sum(len(f[2]) for f in self.fields)
        loc = g.near(flag) if self.local else np.ones(len(flag), np.bool_)
        hist = [int(flag.sum())]
        for rnd in range(self.depth):
            ta = time.perf_counter()
            if rnd == 0 or not self.local:
                split = g.with_twins(flag)
            else:
                split = np.zeros(len(loc), np.bool_)
                split[lidx[g.with_twins(flag)]] = True
            split &= long_mask(S, offs, (2.0 * self.min_len * min(grid.dx, grid.dy)) ** 2)
            if not split.any():
                break
            self._t('twins', ta); ta = time.perf_counter()
            So, Eo, Bo, noffs, new_idx, left, loc = split_segments(S, E, B, offs, split, loc)
            self._t('split', ta); ta = time.perf_counter()
            traj = self._replay(So[new_idx], grid, vx, vy, nd)
            Eo[new_idx] = traj[nd]
            if has_best:
                if best_in_window:
                    Bo[new_idx] = traj[self.best_k]
                else:
                    Bo[new_idx] = 0.5 * (B[left] + B[left + 1])
            self._t('replay', ta)
            self.events.append((new_idx, left, 0.5, step))
            self.n_inserted += len(new_idx)
            S, E, B, offs = So, Eo, Bo, noffs
            self.n_rounds += 1
            ta = time.perf_counter()
            if self.local:
                lidx = np.flatnonzero(loc)
                g = xing.Grid(E, None, self.factor, first=xing.segment_first(offs)[lidx])
            else:
                g = xing.Grid(E, offs, self.factor)
            flag = g.crossing()
            if best_in_window and self.check_best:
                gB = xing.Grid(B, None, self.factor, first=g.first)
                flag |= gB.crossing()
            self._t('redetect', ta)
            if self.verbose: print(f'  step {step} round {rnd} new {len(new_idx)} flagged {int(flag.sum())} local {int(loc.sum())} nseg {len(loc)} t {time.perf_counter()-ta:.2f}', flush=True)
            if not flag.any():
                break
            hist.append(int(flag.sum()))
            if self.stop_rounds and len(hist) > self.stop_rounds and min(hist[-self.stop_rounds:]) >= min(hist[:-self.stop_rounds]):
                break
        self.unresolved += int(flag.sum())
        if self.dump_fail and flag.any():
            np.savez(self.dump_fail, S=self.S0, E0=self.E0, offs0=self.offs0, S1=S, E1=E, offs1=offs, vx=vx, vy=vy, dts=np.array(self.dts[:1]),
                     x_coords=grid.x_coords, y_coords=grid.y_coords, dx=grid.dx, dy=grid.dy, flagseg=np.flatnonzero(flag), first=g.first, step=step)
            print('dumped failure at step', step, flush=True); self.dump_fail = None
        ta = time.perf_counter()
        ring_sizes = np.diff(offs)
        fg.coords = E
        fg.ragged_offsets = (offs.astype(fg.ragged_offsets[0].dtype),) + tuple(fg.ragged_offsets[1:])
        fg.metadata = rebuild_metadata(fg.metadata, ring_sizes)
        fg._ring_info = None; fg._polygon_indices = None
        fg.invalidate_cache()
        self._t('meta', ta)
        self.S = S
        if has_best:
            best_state = (B,) + tuple(best_state[1:])
            self.best_offs = offs.copy()
        self.n_windows_repaired += 1
        self.t_repair += time.perf_counter() - t1
        return best_state

    def restore(self, fg, coords):
        offs = self.best_offs
        ring_sizes = np.diff(offs)
        fg.ragged_offsets = (offs.astype(fg.ragged_offsets[0].dtype),) + tuple(fg.ragged_offsets[1:])
        fg.metadata = rebuild_metadata(fg.metadata, ring_sizes)
        fg._ring_info = None; fg._polygon_indices = None


def backfill(coords, events):
    """Lift the coordinates of an earlier frame to a later vertex structure.

    `events` are the (new_idx, left, t, step) rounds recorded after that frame, in order. The inserted vertex
    new_idx[m] lies at fraction t of the segment (left[m], left[m] + 1) of the structure before the round.
    """
    for new_idx, left, t, _ in events:
        n = len(coords) + len(new_idx)
        is_new = np.zeros(n, bool)
        is_new[new_idx] = True
        out = np.empty((n, 2))
        out[~is_new] = coords
        out[new_idx] = coords[left] * (1 - t) + coords[left + 1] * t
        coords = out
    return coords
