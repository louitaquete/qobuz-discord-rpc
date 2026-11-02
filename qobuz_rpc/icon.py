"""Icone do app (desenhado por codigo: barras de equalizador sobre fundo escuro)."""

import os
import sys

from PIL import Image, ImageDraw

BG = (24, 24, 28, 255)
ACCENT = (88, 101, 242, 255)
BARS = (0.38, 0.72, 0.52, 0.88, 0.45)   # alturas relativas


def make_image(size=256):
    scale = 4  # desenha maior e reduz, para bordas suaves
    s = size * scale
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((0, 0, s - 1, s - 1), radius=int(s * 0.22), fill=BG)

    n = len(BARS)
    margin = s * 0.20
    gap = s * 0.045
    bar_w = (s - 2 * margin - gap * (n - 1)) / n
    for i, h in enumerate(BARS):
        height = (s - 2 * margin) * h
        x0 = margin + i * (bar_w + gap)
        y0 = (s - height) / 2
        draw.rounded_rectangle((x0, y0, x0 + bar_w, y0 + height), radius=bar_w / 2, fill=ACCENT)
    return img.resize((size, size), Image.LANCZOS)


def save_ico(path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    make_image(256).save(path, format="ICO", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])


if __name__ == "__main__":
    # python -m qobuz_rpc.icon assets/icon.ico
    save_ico(sys.argv[1] if len(sys.argv) > 1 else "icon.ico")
