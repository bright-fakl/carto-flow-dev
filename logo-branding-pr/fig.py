"""Figure of the logo assets on a light and a dark surface at 16, 32, 64 and 128 px.

    uv run --with cairosvg --with pillow python fig.py <assets dir> <output dir>
"""
import io
import sys
from pathlib import Path

import cairosvg
from PIL import Image

assets, out = Path(sys.argv[1]), Path(sys.argv[2])
SURF = {"light": "#ffffff", "dark": "#1b1f24"}
FILES = {
    "light": ["mark-light.svg", "favicon.svg", "mark-mono.svg", "wordmark-light.svg"],
    "dark": ["mark-dark.svg", "favicon.svg", "mark-mono.svg", "wordmark-dark.svg"],
}


def render(f, h):
    b = io.BytesIO()
    cairosvg.svg2png(url=str(assets / f), write_to=b, output_height=h)
    return Image.open(b).convert("RGBA")


def surface(kind):
    bg = SURF[kind]
    rows = []
    for h in (16, 32, 64, 128):
        ims = [render(f, h) for f in FILES[kind]]
        row = Image.new("RGBA", (sum(i.width + 24 for i in ims) + 24, h + 16), bg)
        x = 12
        for i in ims:
            row.alpha_composite(i, (x, 8))
            x += i.width + 24
        rows.append(row)
    W = max(r.width for r in rows)
    img = Image.new("RGBA", (W, sum(r.height for r in rows)), bg)
    y = 0
    for r in rows:
        img.alpha_composite(r, (0, y))
        y += r.height
    return img


a, b = surface("light"), surface("dark")
touch = Image.open(assets / "apple-touch-icon-180.png").convert("RGBA")
fav = Image.open(assets / "favicon-32.png").convert("RGBA")
social = Image.open(assets / "social-preview-1280x640.png").convert("RGBA").resize((640, 320))
top = Image.new("RGBA", (a.width + b.width, max(a.height, b.height)), "#888888")
top.alpha_composite(a, (0, 0))
top.alpha_composite(b, (a.width, 0))
bot = Image.new("RGBA", (top.width, 340), "#888888")
bot.alpha_composite(touch, (10, 10))
bot.alpha_composite(fav, (210, 10))
bot.alpha_composite(social, (270, 10))
fig = Image.new("RGBA", (top.width, top.height + bot.height), "#888888")
fig.alpha_composite(top, (0, 0))
fig.alpha_composite(bot, (0, top.height))
fig = fig.resize((fig.width * 2, fig.height * 2), Image.NEAREST)
fig.convert("RGB").save(out / "fig1_assets.png")
