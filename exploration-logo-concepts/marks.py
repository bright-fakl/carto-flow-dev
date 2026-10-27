"""Three logo mark concepts for carto-flow as SVG (96 x 96 viewBox), light and dark variants.

    uv run --with cairosvg --with pillow --project <carto-flow> python marks.py <out_dir>
"""
import math
import sys
from pathlib import Path

import numpy as np

PALETTES = {
    "light": {"blue": "#2c6e9e", "amber": "#d98200"},  # PlotStyle light: series_color, highlight_color
    "dark": {"blue": "#85b7e0", "amber": "#facc38"},  # PlotStyle dark: series_color, accent_color
}


def path(points, close=False):
    d = "M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in points)
    return d + (" Z" if close else "")


def warp(p, c, k, sigma):
    v = p - c
    return c + v * (1 + k * np.exp(-(v @ v) / sigma**2))


def mark_grid(pal):
    """A 3 x 3 grid warped so that the centre cell grows: areas rebalanced to data."""
    n, size, pad = 3, 76.0, 10.0
    c = np.array([48.0, 48.0])
    s = np.linspace(0, 1, 25)
    def line(fixed, vertical, idx):
        pts = []
        for t in s:
            u = idx / n
            p = np.array([u, t]) if vertical else np.array([t, u])
            q = pad + p * size
            pts.append(warp(q, c, 0.55, 22.0))
        return np.array(pts)
    lines = [line(None, True, i) for i in range(n + 1)] + [line(None, False, i) for i in range(n + 1)]
    cell = np.vstack([lines[1][8:17], lines[5][8:17][::-1]])  # placeholder, replaced below
    # centre cell polygon from the four warped lines
    lo, hi = 1 / n, 2 / n
    def seg(vertical, idx, a, b):
        ts = np.linspace(a, b, 12)
        out = []
        for t in ts:
            u = idx / n
            p = np.array([u, t]) if vertical else np.array([t, u])
            out.append(warp(pad + p * size, c, 0.55, 22.0))
        return out
    poly = seg(False, 1, lo, hi) + seg(True, 2, lo, hi) + seg(False, 2, hi, lo) + seg(True, 1, hi, lo)
    body = f'<path d="{path(poly, True)}" fill="{pal["amber"]}"/>'
    for ln in lines:
        body += f'<path d="{path(ln)}" fill="none" stroke="{pal["blue"]}" stroke-width="5.2" stroke-linecap="round" stroke-linejoin="round"/>'
    return body


def hexagon(cx, cy, r):
    return [(cx + r * math.cos(math.radians(60 * i + 30)), cy + r * math.sin(math.radians(60 * i + 30))) for i in range(6)]


def mark_hex(pal):
    """Seven hexagon tiles of different size: tile-cartogram reading of 'area follows data'."""
    pitch = 29.5
    centres = [(0, 0)] + [(pitch * math.cos(math.radians(60 * i)), pitch * math.sin(math.radians(60 * i))) for i in range(6)]
    radii = [16.0, 9.5, 12.5, 8.5, 11.0, 13.5, 10.0]
    out = ""
    for k, ((x, y), r) in enumerate(zip(centres, radii)):
        col = pal["amber"] if k == 0 else pal["blue"]
        out += f'<path d="{path(hexagon(48 + x, 48 + y, r), True)}" fill="{col}" stroke="{col}" stroke-width="3" stroke-linejoin="round"/>'
    return out


def squircle(c, r, n, dx=0.0, dy=0.0, m=90):
    t = np.linspace(0, 2 * math.pi, m, endpoint=False)
    x, y = np.cos(t), np.sin(t)
    px = np.sign(x) * np.abs(x) ** (2 / n)
    py = np.sign(y) * np.abs(y) ** (2 / n)
    return [(c + r * a + dx, c + r * b + dy) for a, b in zip(px, py)]


def mark_morph(pal):
    """Square-ish outline flowing into a round amber one: the morph itself."""
    out = ""
    steps = [(8.0, 0.0, 30.0, 0.28), (5.0, 0.0, 28.0, 0.5), (3.2, 0.0, 26.0, 0.78)]
    for n, _, r, op in steps:
        pass
    shapes = [(10.0, 30.0, -9, -9, 0.4), (5.0, 27.0, 0, 0, 0.7), (2.0, 24.0, 9, 9, 1.0)]
    for i, (n, r, dx, dy, op) in enumerate(shapes):
        pts = squircle(48, r, n, dx, dy)
        if i < 2:
            out += f'<path d="{path(pts, True)}" fill="none" stroke="{pal["blue"]}" stroke-opacity="{op}" stroke-width="4.2" stroke-linejoin="round"/>'
        else:
            out += f'<path d="{path(pts, True)}" fill="{pal["amber"]}"/>'
    return out


MARKS = {"grid": mark_grid, "hex": mark_hex, "morph": mark_morph}


def _cell(pad, size, n, c, k, sigma, i, j, m=10):
    """Polygon of grid cell (i, j) (column i, row j) of an n x n grid after the warp."""
    def pt(u, v):
        return warp(pad + np.array([u, v]) * size, c, k, sigma)
    a, b = i / n, (i + 1) / n
    e, f = j / n, (j + 1) / n
    ts = np.linspace(0, 1, m)
    return ([pt(a + (b - a) * t, e) for t in ts] + [pt(b, e + (f - e) * t) for t in ts]
            + [pt(b - (b - a) * t, f) for t in ts] + [pt(a, f - (f - e) * t) for t in ts])


def mark_filled(pal):
    """Warped grid as a choropleth: filled cells in three tints, centre cell amber and grown."""
    n, pad, size = 3, 10.0, 76.0
    c = np.array([48.0, 48.0])
    tints = [[0.35, 0.7, 0.45], [0.7, 1.0, 0.35], [0.45, 0.7, 0.55]]
    out = ""
    for j in range(n):
        for i in range(n):
            poly = _cell(pad, size, n, c, 0.6, 22.0, i, j)
            poly = [tuple(p) for p in poly]
            if (i, j) == (1, 1):
                out += f'<path d="{path(poly, True)}" fill="{pal["amber"]}" stroke="{pal["amber"]}" stroke-width="2" stroke-linejoin="round"/>'
            else:
                out += f'<path d="{path(poly, True)}" fill="{pal["blue"]}" fill-opacity="{tints[j][i]}" stroke="{pal["blue"]}" stroke-opacity="{tints[j][i]}" stroke-width="2" stroke-linejoin="round"/>'
    return out


def mark_halfway(pal):
    """The grid before and after: regular on the left, warped on the right (the morph in one frame)."""
    n, pad, size = 3, 10.0, 76.0
    c = np.array([48.0, 48.0])
    out = ""
    s = np.linspace(0, 1, 30)
    def k_of(x):  # warp strength grows left to right
        return 0.7 * min(1.0, max(0.0, (x - 20) / 50.0))
    def wp(q):
        return warp(q, c, k_of(q[0]), 22.0)
    for idx in range(n + 1):
        u = idx / n
        v = [wp(pad + np.array([u, t]) * size) for t in s]
        h = [wp(pad + np.array([t, u]) * size) for t in s]
        for ln in (v, h):
            out += f'<path d="{path(ln)}" fill="none" stroke="{pal["blue"]}" stroke-width="5.2" stroke-linecap="round" stroke-linejoin="round"/>'
    # grown amber cell on the right column, middle row
    ts = np.linspace(0, 1, 10)
    a, b, e, f = 2 / n, 3 / n, 1 / n, 2 / n
    P = lambda u, v: wp(pad + np.array([u, v]) * size)
    poly = [tuple(x) for x in ([P(a + (b - a) * t, e) for t in ts] + [P(b, e + (f - e) * t) for t in ts] + [P(b - (b - a) * t, f) for t in ts] + [P(a, f - (f - e) * t) for t in ts])]
    out += f'<path d="{path(poly, True)}" fill="{pal["amber"]}"/>'
    return out


def mark_streams(pal):
    """Streamlines of the flow field parting around a growing amber region."""
    c = np.array([48.0, 48.0])
    out = ""
    xs = np.linspace(10, 86, 40)
    for y0 in (16, 28, 40, 56, 68, 80):
        pts = []
        for x in xs:
            dy = (y0 - 48.0)
            push = 17.0 * math.exp(-((x - 48.0) ** 2) / 260.0) * math.copysign(1, dy) * math.exp(-abs(dy) / 22.0)
            pts.append((x, y0 + push))
        out += f'<path d="{path(pts)}" fill="none" stroke="{pal["blue"]}" stroke-width="5" stroke-linecap="round"/>'
    out += f'<ellipse cx="48" cy="48" rx="15" ry="9.5" fill="{pal["amber"]}"/>'
    return out


def mark_dorling(pal):
    """Dorling circles: area follows data, circles touch where regions were neighbors."""
    circles = [(34, 40, 21), (66, 34, 13), (70, 62, 17), (40, 72, 13), (22, 68, 9)]
    out = ""
    for k, (x, y, r) in enumerate(circles):
        col = pal["amber"] if k == 0 else pal["blue"]
        out += f'<circle cx="{x}" cy="{y}" r="{r}" fill="{col}"/>'
    return out


MARKS.update({"filled": mark_filled, "halfway": mark_halfway, "streams": mark_streams, "dorling": mark_dorling})


SHAPES = {
    "t0": dict(h=[(2, 0.10, 0.5), (3, 0.10, 1.3), (4, 0.05, 0.2), (5, 0.04, 0.9)], sx=0.82, sy=1.0, r=40.0),
    "t1": dict(h=[(2, 0.09, 2.2), (3, 0.12, 0.4), (5, 0.05, 1.7)], sx=0.85, sy=1.0, r=40.0),
    "t2": dict(h=[(2, 0.12, 1.0), (3, 0.08, 2.6), (4, 0.06, 0.5), (6, 0.03, 0.3)], sx=0.78, sy=1.0, r=40.0),
    "s0": dict(h=[(2, 0.07, 0.5), (3, 0.07, 1.3), (5, 0.035, 0.2)], sx=1.0, sy=0.9, r=36.0),
    "s1": dict(h=[(2, 0.12, 0.0), (3, 0.06, 2.0), (4, 0.04, 0.7)], sx=1.1, sy=0.78, r=33.0),
    "s2": dict(h=[(2, 0.04, 1.0), (3, 0.10, 0.3), (6, 0.03, 1.5)], sx=1.0, sy=0.95, r=35.0),
}


def _blob(cx=48.0, cy=48.0, r=36.0, m=240, shape=None):
    from shapely.geometry import Polygon
    t = np.linspace(0, 2 * math.pi, m, endpoint=False)
    sh = SHAPES[shape or 's0']
    r = sh['r']
    rad = 1 + sum(a * np.cos(k * t + ph) for k, a, ph in sh['h'])
    return Polygon(list(zip(cx + sh['sx'] * r * rad * np.cos(t), cy + sh['sy'] * r * rad * np.sin(t))))


def _split(amp, gap, cut_x=42.0, cut_y=52.0, fv=11.0, fh=14.0, tilt=0.0, shape=None, tilt_v=0.0, tilt_h=0.0):
    """Blob minus one wavy vertical and one wavy horizontal line of width gap: four regions."""
    from shapely.geometry import LineString
    from shapely.ops import unary_union
    ys = np.linspace(0, 96, 120)
    xs = np.linspace(0, 96, 120)
    v = LineString([(cut_x + amp * math.sin(y / fv + 0.4), y) for y in ys])
    h = LineString([(x, cut_y + amp * math.sin(x / fh + 1.2)) for x in xs])
    if tilt_v or tilt_h:
        from shapely.affinity import rotate as _rot
        v = _rot(v, tilt_v, origin=(48, 48))
        h = _rot(h, tilt_h, origin=(48, 48))
    cut = unary_union([v, h]).buffer(gap / 2, cap_style=2)
    if tilt:
        from shapely.affinity import rotate
        cut = rotate(cut, tilt, origin=(48, 48))
    pieces = _blob(shape=shape).difference(cut)
    tot = _blob(shape=shape).area
    assert not (shape or '').startswith('t') or len(pieces.geoms) == 4 and min(g.area for g in pieces.geoms) > 0.08 * tot, (shape, tilt_v, tilt_h, [round(g.area / tot, 2) for g in pieces.geoms])
    return sorted(pieces.geoms, key=lambda g: (-g.centroid.y, g.centroid.x))


def _blob_mark(pal, amp, gap, tints, amber_idx, **kw):
    out = ""
    amber_idx = amber_idx if isinstance(amber_idx, (set, tuple, list, str)) else (amber_idx,)
    pieces = _split(amp, gap, **kw)
    if amber_idx == 'right':  # the two pieces with the largest centroid x
        amber_idx = tuple(sorted(range(4), key=lambda i: -pieces[i].centroid.x)[:2])
    for k, g in enumerate(pieces):
        pts = list(g.exterior.coords)
        if k in amber_idx:
            out += f'<path d="{path(pts, True)}" fill="{pal["amber"]}"/>'
        else:
            out += f'<path d="{path(pts, True)}" fill="{pal["blue"]}" fill-opacity="{tints[k]}"/>'
    return out


def mark_blob(pal):
    """A country-like blob cut into four regions by wavy gaps (background shows through); tints vary."""
    return _blob_mark(pal, 4.0, 5.0, [0.55, 1.0, 0.8, 0.0], 3)


def mark_blob_wavy(pal):
    """Same, stronger waves and one blue for all non-amber regions."""
    return _blob_mark(pal, 7.0, 5.0, [1.0, 1.0, 1.0, 0.0], 3)


def mark_blob_small(pal):
    """Favicon variant: thicker gaps, gentler waves."""
    return _blob_mark(pal, 5.0, 8.0, [1.0, 1.0, 1.0, 0.0], 3, fv=16.0, fh=20.0)


def mark_blob_tilt(pal):
    return _blob_mark(pal, 7.0, 5.0, [1.0, 1.0, 1.0, 0.0], 3, tilt=-13.0)


def mark_blob_small_tilt(pal):
    """Favicon: thick gaps, curvier waves (periods 12 and 15, amplitude 6), cross tilted."""
    return _blob_mark(pal, 6.0, 8.0, [1.0, 1.0, 1.0, 0.0], 3, fv=12.0, fh=15.0, tilt=-13.0)


def _variant(shape, amber):
    # region order: 0 bottom-left, 1 bottom-right, 2 top-left, 3 top-right
    return lambda pal: _blob_mark(pal, 5.0, 8.0, [1.0] * 4, amber, fv=16.0, fh=20.0, shape=shape)


for _sh in [k for k in SHAPES if k.startswith("s")]:
    MARKS[f"{_sh}_left"] = _variant(_sh, (0, 2))
    MARKS[f"{_sh}_right"] = _variant(_sh, (1, 3))

def _best_cut(shape, tv, th):
    """Cut position (x, y) with four pieces, the smallest as large as possible, largest/smallest >= 1.6."""
    best = None
    for cx in range(34, 60, 2):
        for cy in range(38, 62, 2):
            try:
                pcs = _split(5.0, 8.0, cut_x=cx, cut_y=cy, fv=16.0, fh=20.0, shape=shape, tilt_v=tv, tilt_h=th)
            except AssertionError:
                continue
            a = sorted(g.area for g in pcs)
            if a[-1] / a[0] >= 1.6 and (best is None or a[0] > best[0]):
                best = (a[0], cx, cy)
    return best[1], best[2]


def _variant2(shape, tv, th, amber='right'):
    cx, cy = _best_cut(shape, tv, th)
    return lambda pal: _blob_mark(pal, 5.0, 8.0, [1.0] * 4, amber, fv=16.0, fh=20.0, shape=shape, tilt_v=tv, tilt_h=th, cut_x=cx, cut_y=cy)


for _sh, _tv, _th in [("t0", 8, -10), ("t0", -10, 8), ("t1", 10, -8), ("t1", -8, 12), ("t2", 7, -9)]:
    MARKS[f"{_sh}_v{_tv}_h{_th}"] = _variant2(_sh, _tv, _th)

MARKS.update({"blob": mark_blob, "blob_wavy": mark_blob_wavy, "blob_small": mark_blob_small,
              "blob_tilt": mark_blob_tilt, "blob_small_tilt": mark_blob_small_tilt})


def mark_cmono(pal):
    """A 'c' of three wavy concentric streamlines, open to the right, with an amber region in the opening."""
    out = ""
    for R, w in ((33, 5.5), (23, 5.5), (13, 5.5)):
        t = np.radians(np.linspace(42, 318, 80))
        rr = R + 1.6 * np.sin(5 * t + R)
        pts = [(48 + r * math.cos(a), 48 - r * math.sin(a)) for r, a in zip(rr, t)]
        out += f'<path d="{path(pts)}" fill="none" stroke="{pal["blue"]}" stroke-width="{w}" stroke-linecap="round"/>'
    out += f'<circle cx="68" cy="48" r="9" fill="{pal["amber"]}"/>'
    return out


def mark_twist(pal):
    """A 3 x 3 grid twisted around its centre; the centre cell is amber."""
    n, pad, size = 3, 12.0, 72.0
    c = np.array([48.0, 48.0])
    def tw(q):
        v = q - c
        r = math.hypot(*v)
        a = 1.15 * math.exp(-(r / 30.0) ** 2)
        ca, sa = math.cos(a), math.sin(a)
        return c + np.array([ca * v[0] - sa * v[1], sa * v[0] + ca * v[1]])
    s_ = np.linspace(0, 1, 40)
    out = ""
    cell = [tw(pad + np.array(p) * size) for p in
            [(1 / n + (1 / n) * t, 1 / n) for t in np.linspace(0, 1, 12)] + [(2 / n, 1 / n + (1 / n) * t) for t in np.linspace(0, 1, 12)]
            + [(2 / n - (1 / n) * t, 2 / n) for t in np.linspace(0, 1, 12)] + [(1 / n, 2 / n - (1 / n) * t) for t in np.linspace(0, 1, 12)]]
    out += f'<path d="{path([tuple(p) for p in cell], True)}" fill="{pal["amber"]}"/>'
    for i in range(n + 1):
        u = i / n
        for ln in ([tw(pad + np.array([u, t]) * size) for t in s_], [tw(pad + np.array([t, u]) * size) for t in s_]):
            out += f'<path d="{path([tuple(p) for p in ln])}" fill="none" stroke="{pal["blue"]}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>'
    return out


def mark_rings(pal):
    """Nested wobbly isolines of a density field around an amber core, centres drifting like a hill."""
    out = ""
    t = np.linspace(0, 2 * math.pi, 120, endpoint=False)
    for k, (R, dx, dy) in enumerate([(36, 0, 0), (27, 2, -1.5), (18, 4, -3)]):
        rr = R * (1 + 0.07 * np.cos(2 * t + 0.4 + k) + 0.05 * np.cos(3 * t + 1.1 * k))
        pts = [(48 + dx + r * math.cos(a), 48 + dy + r * math.sin(a)) for r, a in zip(rr, t)]
        out += f'<path d="{path(pts, True)}" fill="none" stroke="{pal["blue"]}" stroke-width="5" stroke-linejoin="round"/>'
    t2 = t
    rr = 9 * (1 + 0.06 * np.cos(2 * t2 + 1))
    out += f'<path d="{path([(52 + r * math.cos(a), 45 + r * math.sin(a)) for r, a in zip(rr, t2)], True)}" fill="{pal["amber"]}"/>'
    return out


MARKS.update({"cmono": mark_cmono, "twist": mark_twist, "rings": mark_rings})


def _rings(pal, radii, width, core, drift=(1.2, -1.0), wob=0.035):
    """Nested isolines that never cross: spacing exceeds wobble plus drift plus stroke width."""
    from shapely.geometry import LinearRing
    out = ""
    t = np.linspace(0, 2 * math.pi, 160, endpoint=False)
    rings = []
    for k, R in enumerate(radii):
        rr = R * (1 + wob * np.cos(2 * t + 0.4 + 0.5 * k) + 0.6 * wob * np.cos(3 * t + 1.1 * k))
        pts = [(48 + drift[0] * k + r * math.cos(a), 49 + drift[1] * k + r * math.sin(a)) for r, a in zip(rr, t)]
        rings.append(LinearRing(pts).buffer(width / 2))
        out += f'<path d="{path(pts, True)}" fill="none" stroke="{pal["blue"]}" stroke-width="{width}" stroke-linejoin="round"/>'
    for a, b in zip(rings, rings[1:]):
        assert not a.intersects(b), "rings touch"
    rr = core * (1 + 0.05 * np.cos(2 * t + 1))
    cx, cy = 48 + drift[0] * len(radii), 49 + drift[1] * len(radii)
    out += f'<path d="{path([(cx + r * math.cos(a), cy + r * math.sin(a)) for r, a in zip(rr, t)], True)}" fill="{pal["amber"]}"/>'
    return out


def mark_rings2(pal):
    return _rings(pal, (36, 25.5, 15), 5.0, 6.5)


def mark_rings_small(pal):
    """Favicon: two rings and a core, thicker strokes."""
    return _rings(pal, (35, 21), 7.5, 8.0, drift=(1.5, -1.2))


def _stripes(line, offsets, width, color):
    from shapely.geometry import LineString
    out = ""
    for o in offsets:
        ln = line if o == 0 else line.offset_curve(o)
        out += f'<path d="{path(list(ln.coords))}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>'
    return out


def _cf_lines():
    from shapely.geometry import LineString
    t = np.radians(np.linspace(38, 322, 60))
    c = LineString([(29 + 19 * math.cos(a), 54 - 19 * math.sin(a)) for a in t])
    u = np.linspace(0, 1, 30)
    stem = [(66, 86 - 50 * x) for x in u]
    hook = [(66 + 15 * (1 - math.cos(math.pi / 2 * x)) * 1.0, 36 - 12 * math.sin(math.pi / 2 * x)) for x in np.linspace(0, 1, 15)]
    f = LineString(stem + hook)
    bar = LineString([(52, 54), (82, 54)])
    return c, f, bar


def mark_cf(pal):
    """'cf' drawn as three parallel streamlines per stroke; the crossbar of the f is the amber region."""
    c, f, bar = _cf_lines()
    return (_stripes(c, (-4.5, 0, 4.5), 2.8, pal["blue"]) + _stripes(f, (-4.5, 0, 4.5), 2.8, pal["blue"])
            + _stripes(bar, (-3.0, 0, 3.0), 2.8, pal["amber"]))


def mark_cf_solid(pal):
    c, f, bar = _cf_lines()
    return (_stripes(c, (0,), 9.0, pal["blue"]) + _stripes(f, (0,), 9.0, pal["blue"]) + _stripes(bar, (0,), 9.0, pal["amber"]))


def _arrow(x, y, dx, dy, w, color):
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    hx, hy = x + dx, y + dy
    nx, ny = -uy, ux
    hl = min(7.0, 0.55 * L)
    head = [(hx, hy), (hx - hl * ux + 0.55 * hl * nx, hy - hl * uy + 0.55 * hl * ny), (hx - hl * ux - 0.55 * hl * nx, hy - hl * uy - 0.55 * hl * ny)]
    return (f'<path d="{path([(x, y), (hx - 0.6 * hl * ux, hy - 0.6 * hl * uy)])}" stroke="{color}" stroke-width="{w}" stroke-linecap="round"/>'
            f'<path d="{path(head, True)}" fill="{color}"/>')


def mark_velocity(pal):
    """Velocity field of a growing region: arrows pointing away from the amber source, longer near it."""
    out = ""
    cx = cy = 48.0
    pts = [(x, y) for x in (14, 31, 48, 65, 82) for y in (14, 31, 48, 65, 82) if (x, y) != (48, 48)]
    for x, y in pts:
        dx, dy = x - cx, y - cy
        r = math.hypot(dx, dy)
        L = 4 + 150 / (r + 12)  # shorter further out
        out += _arrow(x - dx / r * L / 2, y - dy / r * L / 2, dx / r * L, dy / r * L, 3.6, pal["blue"])
    out += f'<circle cx="48" cy="48" r="9" fill="{pal["amber"]}"/>'
    return out


MARKS.update({"rings2": mark_rings2, "rings_small": mark_rings_small, "cf": mark_cf, "cf_solid": mark_cf_solid, "velocity": mark_velocity})


def mark_velocity2(pal):
    """Fewer, larger arrows pointing away from the amber source (4 x 4 grid, source at the centre)."""
    out = ""
    for x in (20, 40, 60, 80):
        for y in (20, 40, 60, 80):
            dx, dy = x - 50, y - 50
            r = math.hypot(dx, dy)
            L = 16.0 if r < 30 else 12.0
            out += _arrow(x - dx / r * L / 2, y - dy / r * L / 2, dx / r * L, dy / r * L, 4.6, pal["blue"])
    out += f'<circle cx="50" cy="50" r="9" fill="{pal["amber"]}"/>'
    return out


def mark_velocity3(pal):
    """A uniform stream deflected around an amber region: arrows follow the potential flow past a disc."""
    out = ""
    R = 12.0
    for x in (16, 36, 56, 76):
        for y in (18, 38, 58, 78):
            px, py = x - 48.0, y - 48.0
            r2 = px * px + py * py
            if r2 < (R + 9) ** 2:
                continue
            # potential flow past a cylinder, U = 1
            vx = 1 - R * R * (px * px - py * py) / (r2 * r2)
            vy = -2 * R * R * px * py / (r2 * r2)
            n = math.hypot(vx, vy)
            L = 15.0
            out += _arrow(x - vx / n * L / 2, y - vy / n * L / 2, vx / n * L, vy / n * L, 4.6, pal["blue"])
    out += f'<circle cx="48" cy="48" r="{R}" fill="{pal["amber"]}"/>'
    return out


MARKS.update({"velocity2": mark_velocity2, "velocity3": mark_velocity3})


def wordmark(pal, text_color):
    """Wordmark as live SVG text with a blue hyphen and an amber 'o' in flow (exploration only; the final
    wordmark needs outlined letters)."""
    return (f'<text x="2" y="62" font-family="Poppins, Nunito, Helvetica, Arial, sans-serif" font-size="44" '
            f'font-weight="600" fill="{text_color}">carto<tspan fill="{pal["blue"]}">-</tspan>fl'
            f'<tspan fill="{pal["amber"]}">o</tspan>w</text>')


def svg(body, bg=None):
    rect = f'<rect width="96" height="96" fill="{bg}"/>' if bg else ""
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 96">{rect}{body}</svg>'


if __name__ == "__main__":
    out = Path(sys.argv[1])
    out.mkdir(exist_ok=True)
    for name, fn in MARKS.items():
        for variant, pal in PALETTES.items():
            (out / f"{name}-{variant}.svg").write_text(svg(fn(pal)))
    for variant, pal in PALETTES.items():
        tc = "#1b1f24" if variant == "light" else "#e8edf2"
        (out / f"wordmark-{variant}.svg").write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 270 96">{wordmark(pal, tc)}</svg>')
