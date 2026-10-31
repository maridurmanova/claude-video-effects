"""chart-split — top half: animated bar chart on paper, bottom half: you talking."""
import numpy as np
from PIL import Image, ImageDraw
from lib.core import *

NAME = "chart-split"
DESC = "график растёт сверху, ты снизу"
DURATION = 3.0
SFX = [(0.0, "swoosh")] + [(0.3 + i * 0.1, "tick") for i in range(7)] + [(1.2, "chime")]

DATA = [("Нейро", 197), ("Claude", 140), ("Промпты", 124), ("Монтаж", 83),
        ("Голос", 50), ("Идеи", 40), ("Рилс", 38)]
PAPER = (244, 238, 226)
RED = (226, 82, 52)
YEL = (246, 196, 72)


def chart_panel(t, w=W, h=960, title=("Мои топ-7 рилс", "по", "просмотрам")):
    p = Image.new("RGB", (w, h), PAPER)
    d = ImageDraw.Draw(p, "RGBA")
    for x in range(0, w, 40):
        d.line((x, 0, x, h), fill=(0, 0, 0, 12))
    for y in range(0, h, 40):
        d.line((0, y, w, y), fill=(0, 0, 0, 12))
    d.text((70, 70), title[0], font=font("oswald", 84, 700), fill=INK)
    fs = font("oswald", 84, 700)
    d.text((70, 170), title[1], font=fs, fill=INK)
    fi = font("playfair", 88, 600)
    x = 70 + tw(title[1] + " ", fs)
    d.text((x, 160), title[2], font=fi, fill=RED)
    ul = ease_out(prog(t, 0.5, 0.5))
    d.line((x, 278, x + tw(title[2], fi) * ul, 278), fill=RED, width=5)
    # axes
    x0, x1, yb, ytop = 150, w - 60, h - 110, 360
    for i, v in enumerate([0, 50, 100, 150, 200]):
        y = yb - (yb - ytop) * v / 200
        d.line((x0, y, x1, y), fill=(0, 0, 0, 30), width=2)
        d.text((x0 - 20, y), f"{v}K" if v else "0", font=font("mono", 22, 500), fill=(0, 0, 0, 140), anchor="rm")
    bw = (x1 - x0) / len(DATA)
    for i, (lab, v) in enumerate(DATA):
        g = ease_out(prog(t, 0.3 + i * 0.1, 0.55))
        hgt = (yb - ytop) * v / 200 * g
        bx = x0 + i * bw + bw * 0.16
        col = YEL if i == 0 else RED
        d.rectangle((bx, yb - hgt, bx + bw * 0.68, yb), fill=col)
        if g > 0.05:
            d.text((bx + bw * 0.34, yb - hgt - 14), f"{int(v * g)}K", font=font("oswald", 36 if i else 46, 700),
                   fill=INK, anchor="ms")
        d.text((bx + bw * 0.34, yb + 40), lab, font=font("sans", 22, 600), fill=(0, 0, 0, 170), anchor="mm")
    a = ease_out(prog(t, 1.2, 0.4))
    if a > 0:
        y = yb - (yb - ytop) * 96 / 200
        for xx in range(int(x0), int(x0 + (x1 - x0) * a), 26):
            d.line((xx, y, xx + 14, y), fill=RED, width=3)
        d.text((x1, y - 12), "в среднем 96K", font=font("mono", 22, 600), fill=RED, anchor="rs")
    return p


def render(ctx, tl, ts):
    t = tl
    out = Image.new("RGB", (W, H), PAPER)
    vid, _ = ctx.crop(ts, (0, 330, W, 330 + 960), (W, 960))
    vid = grade(vid, sat=1.05, contrast=1.05)
    out.paste(vid, (0, 960))
    slide = ease_out(prog(t, 0.0, 0.4))
    panel = chart_panel(t)
    out.paste(panel, (0, int(-960 * (1 - slide))))
    d = ImageDraw.Draw(out)
    d.line((0, 960, W, 960), fill=INK, width=4)
    return out
