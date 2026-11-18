# Usage: python scripts/make_brand.py custom_components/openmeteo_weather/brand  (needs Pillow)
"""Draw an original sun-behind-cloud icon and a logo with the integration name."""

import math
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
S = 2048  # draw large, then downscale for smooth edges
SUN = (255, 176, 32, 255)
CLOUD_LIGHT = (236, 242, 250, 255)
CLOUD_DARK = (196, 210, 228, 255)
BLUE = (38, 120, 210, 255)


def icon(size: int) -> Image.Image:
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # rounded square background
    d.rounded_rectangle([0, 0, S - 1, S - 1], radius=int(S * 0.22), fill=BLUE)
    # sun with rays
    cx, cy, r = int(S * 0.62), int(S * 0.38), int(S * 0.17)
    for i in range(10):
        a = i * math.tau / 10
        x1, y1 = cx + math.cos(a) * r * 1.35, cy + math.sin(a) * r * 1.35
        x2, y2 = cx + math.cos(a) * r * 1.75, cy + math.sin(a) * r * 1.75
        d.line([x1, y1, x2, y2], fill=SUN, width=int(S * 0.035))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=SUN)

    # cloud: shadow layer then light layer
    def cloud(dx, dy, color):
        parts = [
            (0.22, 0.60, 0.14),
            (0.38, 0.50, 0.19),
            (0.57, 0.55, 0.16),
            (0.71, 0.64, 0.12),
        ]
        for px, py, pr in parts:
            x, y, rr = S * px + dx, S * py + dy, S * pr
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=color)
        d.rounded_rectangle(
            [S * 0.17 + dx, S * 0.60 + dy, S * 0.81 + dx, S * 0.76 + dy],
            radius=int(S * 0.08),
            fill=color,
        )

    cloud(int(S * 0.02), int(S * 0.025), CLOUD_DARK)
    cloud(0, 0, CLOUD_LIGHT)
    return im.resize((size, size), Image.LANCZOS)


def logo(scale: int, dark: bool) -> Image.Image:
    w, h = 1400 * scale, 163 * scale
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ic = icon(h)
    im.paste(ic, (0, 0), ic)
    d = ImageDraw.Draw(im)
    font = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", int(62 * scale))
    color = (240, 244, 250, 255) if dark else (32, 40, 52, 255)
    d.text((h + 34 * scale, h // 2), "Open-Meteo Weather", font=font, fill=color, anchor="lm")
    # crop to content width
    bbox = im.getbbox()
    return im.crop((0, 0, bbox[2] + 4 * scale, h))


icon(256).save(out / "icon.png", optimize=True)
icon(512).save(out / "icon@2x.png", optimize=True)
for dark in (False, True):
    p = "dark_logo" if dark else "logo"
    logo(1, dark).save(out / f"{p}.png", optimize=True)
    logo(2, dark).save(out / f"{p}@2x.png", optimize=True)
