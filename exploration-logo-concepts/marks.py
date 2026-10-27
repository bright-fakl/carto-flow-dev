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


def svg(body, bg=None):
    rect = f'<rect width="96" height="96" fill="{bg}"/>' if bg else ""
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 96">{rect}{body}</svg>'


if __name__ == "__main__":
    out = Path(sys.argv[1])
    out.mkdir(exist_ok=True)
    for name, fn in MARKS.items():
        for variant, pal in PALETTES.items():
            (out / f"{name}-{variant}.svg").write_text(svg(fn(pal)))
