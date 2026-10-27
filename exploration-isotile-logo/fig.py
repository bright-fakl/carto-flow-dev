"""Legibility figures: each mark at 128, 64, 32 and 16 px on the light and dark surfaces, plus one color at 32 px.

    uv run --project <carto-flow> --with <isotile> --with cairosvg --with pillow --with shapely --with matplotlib python fig.py
"""
import io
import sys
from pathlib import Path

import cairosvg
from PIL import Image, ImageDraw

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from marks import LOCKUPS, MARKS, PALETTES, SURFACE, TEXT, lockup, svg  # noqa: E402

SIZES = [128, 64, 32, 16]
GAP = 24
LABEL = 14


def render(body, s, w=None):
    png = cairosvg.svg2png(bytestring=svg(body).encode(), output_width=s, output_height=s)
    return Image.open(io.BytesIO(png)).convert("RGBA")


def legibility(names, out, marks=MARKS):
    """Rows: concepts. Left half light surface, right half dark; columns 128, 64, 32, 16 px and 32 px in one color."""
    cols = SIZES + [32]
    W = sum(s + GAP for s in cols) + GAP
    row_h = 128 + GAP
    H = row_h * len(names) + GAP
    canvas = Image.new("RGB", (W * 2 + 40, H), "#888888")
    for half, variant in enumerate(("light", "dark")):
        pal = PALETTES[variant]
        panel = Image.new("RGB", (W, H), SURFACE[variant])
        for r, name in enumerate(names):
            x = GAP
            for c, s in enumerate(cols):
                body = marks[name](pal if c < 4 else {**pal, "amber": pal["blue"]})
                im = render(body, s)
                panel.paste(im, (x, GAP + r * row_h + (128 - s) // 2), im)
                x += s + GAP
        canvas.paste(panel, (half * (W + 40), 0))
    canvas = canvas.resize((canvas.width * 2, canvas.height * 2), Image.NEAREST)
    canvas.save(HERE / out)


def lockups(out, widths=(360, 180)):
    """Mark + wordmark draft (live DejaVu Sans Bold text), light and dark, at two widths, for the concepts in LOCKUPS."""
    rows = [(n, w) for n in LOCKUPS for w in widths]
    panels = []
    for variant in ("light", "dark"):
        pal = PALETTES[variant]
        ims = []
        for n, w in rows:
            doc, total = lockup(MARKS[n](pal), variant)
            png = cairosvg.svg2png(bytestring=doc.encode(), output_width=w)
            ims.append(Image.open(io.BytesIO(png)).convert("RGBA"))
        W = max(widths) + 2 * GAP
        H = sum(i.height + GAP for i in ims) + GAP
        panel = Image.new("RGB", (W, H), SURFACE[variant])
        y = GAP
        for im in ims:
            panel.paste(im, (GAP, y), im)
            y += im.height + GAP
        panels.append(panel)
    canvas = Image.new("RGB", (panels[0].width * 2 + 40, panels[0].height), "#888888")
    canvas.paste(panels[0], (0, 0))
    canvas.paste(panels[1], (panels[0].width + 40, 0))
    canvas.save(HERE / out)


if __name__ == "__main__":
    legibility(["a_patch", "b_escher", "c_cell", "d_letter", "e_links"], "fig1_concepts.png")
    legibility(["a_patch_fav", "b_escher_fav", "c_cell_fav", "d_letter_fav", "e_links_fav"], "fig2_favicon_variants.png")
    lockups("fig3_lockups.png")
