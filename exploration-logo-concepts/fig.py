"""Legibility figure: each mark at 128, 64, 32, 16 px on the light and dark surfaces of the docs."""
import io
import sys
from pathlib import Path

import cairosvg
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
from marks import MARKS, PALETTES, svg

SURF = {"light": "#ffffff", "dark": "#1b1f24"}
SIZES = [128, 64, 32, 16]
GAP = 24
cols = SIZES + [32]  # last column: one-colour (blue only, no amber) at 32 px
cell_w = [s + GAP for s in cols]
W = sum(cell_w) + GAP
SHOW = ['rings2', 'rings_small', 's0_right', 'cf', 'cf_solid', 'velocity']
row_h = 128 + GAP
H = row_h * len(SHOW) + GAP
canvas = Image.new("RGB", (W * 2 + 40, H), "#888888")
for half, variant in enumerate(("light", "dark")):
    pal = PALETTES[variant]
    panel = Image.new("RGB", (W, H), SURF[variant])
    for r, (name, fn) in enumerate((n, MARKS[n]) for n in SHOW):
        x = GAP
        for c, s in enumerate(cols):
            body = fn(pal) if c < 4 else fn({"blue": pal["blue"], "amber": pal["blue"]})
            png = cairosvg.svg2png(bytestring=svg(body).encode(), output_width=s, output_height=s)
            im = Image.open(io.BytesIO(png)).convert("RGBA")
            panel.paste(im, (x, GAP + r * row_h + (128 - s) // 2), im)
            x += s + GAP
    canvas.paste(panel, (half * (W + 40), 0))
canvas = canvas.resize((canvas.width * 2, canvas.height * 2), Image.NEAREST)
canvas.save(Path(__file__).parent / "fig1_marks.png")

# wordmark figure
from marks import wordmark
W2 = [400, 200, 120]
im2 = Image.new("RGB", (460 * 2 + 40, 3 * 160 + 40), "#888888")
for half, variant in enumerate(("light", "dark")):
    pal = PALETTES[variant]
    panel = Image.new("RGB", (460, 3 * 160 + 40), SURF[variant])
    tc = "#1b1f24" if variant == "light" else "#e8edf2"
    body = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 270 96">{wordmark(pal, tc)}</svg>'
    for r, w in enumerate(W2):
        png = cairosvg.svg2png(bytestring=body.encode(), output_width=w)
        im = Image.open(io.BytesIO(png)).convert("RGBA")
        panel.paste(im, (30, 30 + r * 160), im)
    im2.paste(panel, (half * 500, 0))
im2.save(Path(__file__).parent / "fig2_wordmark.png")
