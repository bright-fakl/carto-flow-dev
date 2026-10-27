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


def _blob(cx=48.0, cy=48.0, r=36.0, m=240):
    from shapely.geometry import Polygon
    t = np.linspace(0, 2 * math.pi, m, endpoint=False)
    rad = 1 + 0.07 * np.cos(2 * t + 0.5) + 0.07 * np.cos(3 * t + 1.3) + 0.035 * np.cos(5 * t + 0.2)
    return Polygon(list(zip(cx + 1.0 * r * rad * np.cos(t), cy + 0.9 * r * rad * np.sin(t))))


def _split(amp, gap, cut_x=42.0, cut_y=52.0, fv=11.0, fh=14.0, tilt=0.0):
    """Blob minus one wavy vertical and one wavy horizontal line of width gap: four regions."""
    from shapely.geometry import LineString
    from shapely.ops import unary_union
    ys = np.linspace(0, 96, 120)
    xs = np.linspace(0, 96, 120)
    v = LineString([(cut_x + amp * math.sin(y / fv + 0.4), y) for y in ys])
    h = LineString([(x, cut_y + amp * math.sin(x / fh + 1.2)) for x in xs])
    cut = unary_union([v, h]).buffer(gap / 2, cap_style=2)
    if tilt:
        from shapely.affinity import rotate
        cut = rotate(cut, tilt, origin=(48, 48))
    pieces = _blob().difference(cut)
    return sorted(pieces.geoms, key=lambda g: (-g.centroid.y, g.centroid.x))


def _blob_mark(pal, amp, gap, tints, amber_idx, **kw):
    out = ""
    for k, g in enumerate(_split(amp, gap, **kw)):
        pts = list(g.exterior.coords)
        if k == amber_idx:
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


MARKS.update({"blob": mark_blob, "blob_wavy": mark_blob_wavy, "blob_small": mark_blob_small,
              "blob_tilt": mark_blob_tilt, "blob_small_tilt": mark_blob_small_tilt})


def svg(body, bg=None):
    rect = f'<rect width="96" height="96" fill="{bg}"/>' if bg else ""
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 96">{rect}{body}</svg>'


if __name__ == "__main__":
    out = Path(sys.argv[1])
    out.mkdir(exist_ok=True)
    for name, fn in MARKS.items():
        for variant, pal in PALETTES.items():
            (out / f"{name}-{variant}.svg").write_text(svg(fn(pal)))
