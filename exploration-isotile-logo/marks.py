"""Logo mark concepts for isotile as SVG (96 x 96 viewBox), light and dark variants.

    uv run --project <carto-flow> --with <isotile> --with cairosvg --with pillow --with shapely python marks.py <out_dir>

Tile geometry comes from the isotile library (straight prototiles, lattice cells, adjacency). The curved edges of
the Escher-like concept are built here (isotile has no edge curves yet) from the canonical-edge convention of the
library: ``edge_transforms`` map the canonical edge (0, 0)-(1, 0) onto each prototile edge, ``edge_reversed`` tells
whether the edge is walked against its shape direction.
"""
import math
import sys
from pathlib import Path

import numpy as np
import shapely
from isotile import IsohedralTiling

PALETTES = {
    "light": {"blue": "#2c6e9e", "amber": "#c27400"},
    "dark": {"blue": "#85b7e0", "amber": "#facc38"},
}
for _k, _p in PALETTES.items():
    _p["mode"] = _k
TEXT = {"light": "#1b1f24", "dark": "#e8edf2"}
SURFACE = {"light": "#ffffff", "dark": "#1b1f24"}
SIZE = 96.0


def svg(body, w=96, h=96):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">{body}</svg>'


def pth(points, close=True):
    d = "M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in points)
    return d + (" Z" if close else "")


def poly_path(p):
    """SVG path of a shapely polygon (exterior only; all shapes here are simple)."""
    return pth(list(p.exterior.coords)[:-1])


# ---- geometry helpers ----------------------------------------------------------------------------------


def fit(polys, pad=7.0, extra=()):
    """Scale and center shapely polygons so that their joint bounds fill the mark box. Returns (polys, fn)."""
    x0, y0, x1, y1 = shapely.union_all(list(polys) + list(extra)).bounds
    s = (SIZE - 2 * pad) / max(x1 - x0, y1 - y0)
    ox = SIZE / 2 - s * (x0 + x1) / 2
    oy = SIZE / 2 - s * (y0 + y1) / 2

    def fn(p):
        return np.asarray(p, dtype=float) * s + [ox, oy]

    return [shapely.polygons(fn(p.exterior.coords)) for p in polys], fn, s


def shrink(p, gap):
    """Inset by half a gap with softly rounded corners."""
    q = p.buffer(-gap / 2 - 0.6, join_style="round").buffer(0.6, join_style="round")
    return q


def levels(pal, light=(1.0, 0.62, 0.34), dark=(1.0, 0.74, 0.5)):
    """Opacity levels of the blue tiles: lighter surfaces take lower levels, dark ones stay brighter."""
    return light if pal.get("mode", "light") == "light" else dark


def fill_attr(col, op):
    return f'fill="{col}"' + (f' fill-opacity="{op}"' if op < 1 else "")


def nearest(ts, k, center=None):
    c = ts.centroids
    if center is None:
        center = c.mean(axis=0)
    order = np.argsort(np.linalg.norm(c - center, axis=1))
    return order[:k]


# ---- curved edges (Escher-like) --------------------------------------------------------------------------


def catmull(pts, n=14):
    pts = np.asarray(pts, dtype=float)
    p = np.vstack([pts[0], pts, pts[-1]])
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t**2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t**3))
    out.append(p[-2])
    return np.array(out)


def canonical_curve(kind, ctrl):
    """Curve from (0, 0) to (1, 0). J: free; U: mirror symmetric about x = 1/2; S: point symmetric about (1/2, 0); I: straight."""
    if kind == "I":
        return np.array([[0.0, 0.0], [1.0, 0.0]])
    c = np.asarray(ctrl, dtype=float)
    if kind == "J":
        return catmull(np.vstack([[0, 0], c, [1, 0]]))
    if kind == "U":  # c ends at x = 1/2
        full = np.vstack([[0, 0], c, c[-2::-1] * [-1, 1] + [1, 0], [1, 0]]) if len(c) > 1 else np.vstack([[0, 0], c, [1, 0]])
        return catmull(full)
    if kind == "S":  # c ends at (1/2, 0)
        full = np.vstack([[0, 0], c, (c[-2::-1] * [-1, -1] + [1, 0]), [1, 0]])
        return catmull(full)
    raise ValueError(kind)


def curved_prototile(tiling, spec):
    """Outline of the prototile with curved edges; ``spec`` maps shape id -> control points of its canonical curve."""
    n = len(tiling.vertices)
    E, rev = tiling.edge_transforms, tiling.edge_reversed
    ids, kinds = tiling.edge_shape_ids, tiling.edge_shapes
    pts = []
    for i in range(n):
        c = canonical_curve(kinds[i], spec.get(int(ids[i])))
        P = c @ E[i][:, :2].T + E[i][:, 2]
        if rev[i]:
            P = P[::-1]
        pts.extend(P[:-1])
    return np.array(pts)


def curved_tiles(ts, spec):
    proto = curved_prototile(ts.tiling, spec)
    return [shapely.polygons(proto @ T[:, :2].T + T[:, 2]) for T in ts.transforms]


# ---- concepts ---------------------------------------------------------------------------------------------


def vertex_center(ts, valence):
    """A point of the patch where ``valence`` tiles meet (the vertex closest to the middle of the region)."""
    V = np.round(ts.vertices().reshape(-1, 2), 6)
    keys, inv, cnt = np.unique(V, axis=0, return_inverse=True, return_counts=True)
    cand = keys[cnt == valence]
    return cand[np.argmin(np.linalg.norm(cand - 0.5, axis=1))]


def patch(pal, ttype, k=8, tints=None, gap=2.6, n_tiles=40, rotate=0.0, pad=6.0, params=None, valence=None, amber=None):
    """A small patch of an actual tiling: the k tiles nearest a center (the middle, or a vertex where ``valence``
    tiles meet), one amber."""
    tints = tints or levels(pal)
    t = IsohedralTiling(ttype, params)
    if rotate:
        t = t.rotated(rotate)
    ts = t.fill_region((0, 0, 1, 1), n_tiles=n_tiles)
    c0 = np.array([0.5, 0.5]) if valence is None else vertex_center(ts, valence)
    sel = nearest(ts, k, c0)
    ts = ts.select(sel)
    polys = ts.polygons()
    col = ts.colors()
    centre = int(np.argmin(np.linalg.norm(ts.centroids - c0, axis=1))) if amber is None else amber
    fp, _, s = fit(polys, pad)
    out = ""
    for i, p in enumerate(fp):
        q = shrink(p, gap)
        if i == centre:
            out += f'<path d="{poly_path(q)}" fill="{pal["amber"]}"/>'
        else:
            out += f'<path d="{poly_path(q)}" {fill_attr(pal["blue"], tints[col[i] % len(tints)])}/>'
    return out


def connected_patch(ts, k):
    """Indices of k edge-connected tiles grown from the middle tile, each step adding the neighbor nearest the middle."""
    c = ts.centroids
    mid = np.array([0.5, 0.5])
    A = ts.adjacency("edge").toarray()
    cur = [int(np.argmin(np.linalg.norm(c - mid, axis=1)))]
    while len(cur) < k:
        cand = [j for j in np.nonzero(A[cur].any(axis=0))[0] if j not in cur]
        cur.append(int(min(cand, key=lambda j: np.linalg.norm(c[j] - mid))))
    return np.array(cur)


def escher(pal, spec, ttype=1, k=7, tints=None, gap=1.6, pad=6.0, rotate=0.0, centre=None, keep=None, connected=False):
    """Interlocking curved tiles: one prototile with curved edges, repeated by the tiling's symmetries."""
    tints = tints or levels(pal)
    t = IsohedralTiling(ttype)
    if rotate:
        t = t.rotated(rotate)
    ts = t.fill_region((0, 0, 1, 1), n_tiles=30)
    sel = nearest(ts, k, np.array([0.5, 0.5])) if not connected else connected_patch(ts, k)
    ts = ts.select(sel)
    polys = curved_tiles(ts, spec)
    ci = int(np.argmin(np.linalg.norm(ts.centroids - np.array([0.5, 0.5]), axis=1))) if centre is None else centre
    col = ts.colors()
    fp, _, s = fit(polys, pad)
    out = ""
    for i, p in enumerate(fp):
        q = p.buffer(-gap / 2, join_style="round")
        if i == ci:
            out += f'<path d="{poly_path(q)}" fill="{pal["amber"]}"/>'
        else:
            out += f'<path d="{poly_path(q)}" {fill_attr(pal["blue"], tints[col[i] % len(tints)])}/>'
    return out


def rand_spec(seed, n_ids=3, n=2, amp=0.36):
    """Three free curves with two control points each, drawn from a seeded generator (type 1 has J edges only)."""
    rng = np.random.default_rng(seed)
    spec = {}
    for i in range(n_ids):
        xs = np.linspace(0.3, 0.7, n) + rng.uniform(-0.06, 0.06, n)
        ys = rng.uniform(-amp, amp, n)
        spec[i] = list(zip(xs, ys))
    return spec


def lattice(pal, ttype=33, tints=(0.55, 0.3), gap=2.0, pad=6.0, ctx=0.2, shift=(0.0, 0.0), amber_aspect=0, ring=1.5, dots=0, min_piece=0.0):
    """Lattice cell: the parallelogram spanned by the two translations, cut into the pieces of the aspect tiles
    that fall into it (one aspect amber); the surrounding tiles are drawn faintly so that the repeat shows."""
    ts = IsohedralTiling(ttype).fill_region((0, 0, 1, 1), n_tiles=80)
    u, v = ts.tiling.translation_u, ts.tiling.translation_v
    centre = np.array([0.5, 0.5]) + np.array(shift) * np.linalg.norm(u)
    para = np.array([-(u + v) / 2, (u - v) / 2, (u + v) / 2, (v - u) / 2]) + centre
    P = shapely.polygons(para)
    polys = ts.polygons()
    asp = ts.aspect
    inside = []
    for p, a in zip(polys, asp):
        q = p.intersection(P)
        if q.area > 1e-9 * P.area:
            inside.append((q, int(a)))
    near = [(p, int(a)) for p, a in zip(polys, asp) if p.intersection(P).area < 1e-9 * P.area and p.distance(P) < ring * np.linalg.norm(u)]
    _, fn, s = fit([P], pad)
    out = ""
    ordered = sorted(set(a for _, a in inside))
    for p, a in near if ctx else []:
        q = shrink(shapely.polygons(fn(p.exterior.coords)), gap).intersection(shapely.box(2, 2, 94, 94))
        if not q.is_empty and q.geom_type == "Polygon":
            out += f'<path d="{poly_path(q)}" {fill_attr(pal["blue"], ctx)}/>'
    for q, a in inside:
        for g in (q.geoms if hasattr(q, "geoms") else [q]):
            if g.area < max(1e-9, min_piece * P.area):
                continue
            h = shrink(shapely.polygons(fn(g.exterior.coords)), gap)
            if h.is_empty:
                continue
            if a == amber_aspect:
                out += f'<path d="{poly_path(h)}" fill="{pal["amber"]}"/>'
            else:
                out += f'<path d="{poly_path(h)}" {fill_attr(pal["blue"], tints[(ordered.index(a) - 1) % len(tints)] + 0.45)}/>'
    if dots:
        for c in fn(para):
            out += f'<circle cx="{c[0]:.2f}" cy="{c[1]:.2f}" r="{dots}" fill="{pal["blue"]}"/>'
    return out


LETTERS = {  # (column, row) on the flat-top hexagon lattice; odd columns sit half a row lower
    "i": {"amber": [(0, 0)], "blue": [(0, 2), (0, 3), (0, 4)]},
    "i2": {"amber": [(0, 0), (1, 0.5)], "blue": [(0, 2), (0, 3), (0, 4), (1, 2.5), (1, 3.5), (1, 4.5)]},
    "it": {"amber": [(0, 0)], "blue": [(0, 2), (0, 3), (0, 4), (3, 1.5), (3, 2.5), (3, 3.5), (3, 4.5), (2, 2), (4, 2)]},
}


def monogram(pal, word="i", gap=2.0, pad=6.0):
    """Letters from flat-top hexagons of the regular hexagonal tiling (type 20): the dot of the `i` is amber."""
    t = IsohedralTiling.hexagon(pointy_top=False)
    ts = t.fill_region((-12, -12, 12, 12), tile_size=math.sqrt(1.5 * math.sqrt(3)))  # circumradius 1
    cent = ts.centroids
    polys_all = ts.polygons()
    h = math.sqrt(3)
    js = []
    for colr, cells in (("amber", LETTERS[word]["amber"]), ("blue", LETTERS[word]["blue"])):
        for c, r in cells:
            js.append((int(np.argmin(np.linalg.norm(cent - [1.5 * c, h * r], axis=1))), colr))
    fp, fn, s = fit([polys_all[j] for j, _ in js], pad)
    out = ""
    for p, (_, c) in zip(fp, js):
        out += f'<path d="{poly_path(shrink(p, gap))}" fill="{pal[c]}"/>'
    return out


def neighbors(pal, ttype=29, gap=2.4, n_tiles=40, pad=6.0, lw=3.0, rad=4.2, faint=1.0):
    """One tile (amber) with links to its edge neighbors, drawn on the neighbor tiles."""
    t = IsohedralTiling(ttype)
    ts = t.fill_region((0, 0, 1, 1), n_tiles=n_tiles)
    ci = int(np.argmin(np.linalg.norm(ts.centroids - 0.5, axis=1)))
    A = ts.adjacency("edge").tocsr()
    nb = [int(j) for j in np.nonzero(A.toarray()[ci])[0]]
    sel = [ci] + nb
    sub = ts.select(np.array(sel))
    polys = sub.polygons()
    cen = sub.centroids
    fp, fn, s = fit(polys, pad)
    out = ""
    for i, p in enumerate(fp):
        if i and faint:
            q = shrink(p, gap)
            out += f'<path d="{poly_path(q)}" fill="{pal["blue"]}" fill-opacity="{(0.3 if pal['mode'] == 'light' else 0.4) * faint}"/>'
    c0 = fn(cen)[0]
    for i in range(1, len(sel)):
        c = fn(cen)[i]
        out += f'<path d="{pth([c0, c], False)}" stroke="{pal["blue"]}" stroke-width="{lw}" stroke-linecap="round"/>'
    out += f'<path d="{poly_path(shrink(fp[0], gap))}" fill="{pal["amber"]}"/>'
    for i in range(1, len(sel)):
        c = fn(cen)[i]
        out += f'<circle cx="{c[0]:.2f}" cy="{c[1]:.2f}" r="{rad}" fill="{pal["blue"]}"/>'
    return out


# Designed edge curves in canonical edge coordinates (edge from (0, 0) to (1, 0)); the kind of each edge (J, S, U, I)
# is fixed by the tiling type, so the symmetry rule is applied by `canonical_curve`: J free, S point symmetric
# about (1/2, 0) (control points end at (1/2, 0)), U mirror symmetric about x = 1/2 (control points end at x = 1/2).
KNOB = [(0.32, 0.0), (0.40, 0.06), (0.36, 0.17), (0.50, 0.28), (0.64, 0.17), (0.60, 0.06), (0.68, 0.0)]  # rounded tab
KNOB_IN = [(x, -y) for x, y in KNOB]  # the same tab pointing the other way
WAVE = [(0.2, 0.3), (0.5, 0.0)]  # S: one crest and one trough
WAVE_SOFT = [(0.25, 0.2), (0.5, 0.0)]
LOBE = [(0.25, 0.12), (0.5, 0.2)]  # U: one symmetric lobe
FLOW = [(0.5, 0.2)]  # J: a single lobe, the neighbor receives it as a dent

MARKS = {
    "a_patch": lambda pal: patch(pal, 28, k=7, params=[0.3153, 0.5], valence=4),
    "b_escher": lambda pal: escher(pal, rand_spec(105, amp=0.5), 1, k=4, gap=2.0),
    "c_cell": lambda pal: lattice(pal, 34, ctx=0, dots=4.2),
    "d_letter": lambda pal: monogram(pal, "it"),
    "d_letter_i": lambda pal: monogram(pal, "i"),
    "d_letter_i2": lambda pal: monogram(pal, "i2"),
    "e_links": lambda pal: neighbors(pal, 29),
    # improved Escher-like variants (designed curves)
    "b1_jigsaw": lambda pal: escher(pal, {0: KNOB, 1: KNOB_IN}, 41, k=6, gap=2.0, connected=True),
    "b2_pinwheel": lambda pal: escher(pal, {0: WAVE}, 62, k=5, gap=2.4),
    "b3_trefoil": lambda pal: escher(pal, {0: LOBE}, 18, k=7, gap=2.4, connected=True),
    "b4_flow": lambda pal: escher(pal, {0: FLOW}, 34, k=5, gap=2.2, connected=True),
    "b5_swirl": lambda pal: escher(pal, {0: WAVE_SOFT, 1: WAVE_SOFT, 2: WAVE_SOFT}, 84, k=7, gap=2.4),
    # favicon variants: fewer tiles, wider gaps, thicker lines
    "a_patch_fav": lambda pal: patch(pal, 28, k=5, params=[0.3153, 0.5], valence=4, gap=4.4, pad=4.0, tints=levels(pal, (1.0, 0.55), (1.0, 0.65))),
    "b_escher_fav": lambda pal: escher(pal, rand_spec(105, amp=0.5), 1, k=3, gap=3.6, pad=4.0, tints=levels(pal, (1.0, 0.55), (1.0, 0.65))),
    "c_cell_fav": lambda pal: lattice(pal, 34, ctx=0, dots=5.0, gap=3.6, pad=7.0, min_piece=0.04, tints=(0.3,)),
    "d_letter_fav": lambda pal: monogram(pal, "i2", gap=3.4, pad=4.0),
    "b1_jigsaw_fav": lambda pal: escher(pal, {0: KNOB, 1: KNOB_IN}, 41, k=4, gap=3.6, pad=4.0, tints=levels(pal, (1.0, 0.55), (1.0, 0.65)), connected=True),
    "b2_pinwheel_fav": lambda pal: escher(pal, {0: WAVE}, 62, k=3, gap=3.8, pad=4.0, tints=levels(pal, (1.0, 0.55), (1.0, 0.65))),
    "b3_trefoil_fav": lambda pal: escher(pal, {0: LOBE}, 18, k=4, gap=4.0, pad=4.0, tints=levels(pal, (1.0, 0.55), (1.0, 0.65)), connected=True),
    "b4_flow_fav": lambda pal: escher(pal, {0: FLOW}, 34, k=4, gap=3.8, pad=4.0, tints=levels(pal, (1.0, 0.55), (1.0, 0.65)), connected=True),
    "b5_swirl_fav": lambda pal: escher(pal, {0: WAVE_SOFT, 1: WAVE_SOFT, 2: WAVE_SOFT}, 84, k=4, gap=4.0, pad=4.0, tints=levels(pal, (1.0, 0.55), (1.0, 0.65))),
    "e_links_fav": lambda pal: neighbors(pal, 29, gap=3.0, pad=5.0, lw=4.4, rad=6.0, faint=0.0),
}


def text_width(text, size, bold=True):
    """Advance width of ``text`` in DejaVu Sans (Bold) at ``size``, from the font file (live-text draft only)."""
    from fontTools.ttLib import TTFont

    import matplotlib

    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    font = TTFont(Path(matplotlib.get_data_path()) / "fonts" / "ttf" / name)
    cmap, hmtx, upm = font.getBestCmap(), font["hmtx"], font["head"].unitsPerEm
    return sum(hmtx[cmap[ord(c)]][0] for c in text) * size / upm


def lockup(mark_body, variant, text="isotile", size=50.0, gap=14.0):
    """Horizontal lockup: the 96 x 96 mark, then the name in live DejaVu Sans Bold (draft; the final one is outlined)."""
    w = text_width(text, size)
    total = 96 + gap + w + 4
    base = 48 + 0.36 * size  # x-height centered on the mark
    t = (f'<text x="{96 + gap:.1f}" y="{base:.1f}" font-family="DejaVu Sans, Verdana, sans-serif" font-weight="700" '
         f'font-size="{size}" fill="{TEXT[variant]}">{text}</text>')
    return svg(mark_body + t, total, 96), total


LOCKUPS = ("a_patch", "b_escher", "b3_trefoil")  # concepts with a lockup draft


def main(out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for name, fn in MARKS.items():
        for variant, pal in PALETTES.items():
            (out / f"{name}-{variant}.svg").write_text(svg(fn(pal)))
    for name in LOCKUPS:
        for variant, pal in PALETTES.items():
            (out / f"lockup-{name}-{variant}.svg").write_text(lockup(MARKS[name](pal), variant)[0])


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "svg")
