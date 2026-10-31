"""timeline — your edit renders live in a mini editor window above you."""
import math
import numpy as np
from PIL import Image, ImageDraw
from lib.core import *

NAME = "timeline"
DESC = "монтаж рендерится вживую над тобой"
DURATION = 3.0
SFX = [(0.0, "swoosh")] + [(0.35 + i * 0.16, "tick") for i in range(5)] + [(2.2, "chime")]
PAPER = (244, 238, 226)
WIN = (40, 28, 54)
WIN2 = (58, 42, 78)
ROWS = [("склейки", "паузы убраны"), ("субтитры", "синхрон по словам"), ("цвет", "тёплый"),
        ("эффекты", "7 подключено"), ("звук", "мягкие поп-звуки")]
COLS = [(236, 92, 70), (246, 196, 72), (155, 110, 240), (90, 200, 180)]


def editor(ctx, t, ts, w=960, h=700):
    p = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(p, "RGBA")
    d.rounded_rectangle((0, 0, w - 1, h - 1), 30, fill=WIN)
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse((26 + i * 30, 24, 44 + i * 30, 42), fill=c)
    d.text((130, 33), "CLAUDE CUT · РЕНДЕР", font=font("mono", 22, 600), fill=(255, 255, 255, 200), anchor="lm")
    d.text((w - 30, 33), "4K · 30FPS", font=font("mono", 22, 600), fill=(255, 255, 255, 150), anchor="rm")
    # preview
    fr = ctx.clip.frame(ts).resize((180, 320), Image.LANCZOS)
    p.paste(fr, (30, 70), rrect_mask((180, 320), 16))
    # rows
    for i, (a, b) in enumerate(ROWS):
        y = 90 + i * 60
        d.text((250, y), a, font=font("sans", 26, 600), fill=(255, 255, 255, 220), anchor="lm")
        if t >= 0.35 + i * 0.16:
            fb = font("sans", 24, 600)
            d.text((w - 40, y), b, font=fb, fill=(130, 235, 160), anchor="rm")
            cx = w - 40 - tw(b, fb) - 22
            d.line([(cx - 9, y), (cx - 3, y + 7), (cx + 9, y - 7)], fill=(130, 235, 160), width=4)
        else:
            d.text((w - 40, y), "…", font=font("sans", 24, 600), fill=(255, 255, 255, 90), anchor="rm")
        d.line((250, y + 30, w - 40, y + 30), fill=(255, 255, 255, 18), width=1)
    # tracks
    tx0, tx1 = 30, w - 30
    ty = 420
    # filmstrip
    n = 10
    cw = (tx1 - tx0) / n
    for i in range(n):
        th = ctx.clip.frame(i * ctx.clip.duration / n).resize((int(cw) - 4, 64), Image.LANCZOS, box=(0, 400, W, 1000))
        p.paste(th, (int(tx0 + i * cw) + 2, ty))
    # coloured clips
    y2 = ty + 80
    x = tx0
    rng = np.random.default_rng(3)
    k = 0
    while x < tx1:
        ww = rng.integers(70, 160)
        d.rounded_rectangle((x, y2, min(x + ww - 6, tx1), y2 + 34), 8, fill=COLS[k % 4] + (230,))
        x += ww; k += 1
    # text track
    y3 = y2 + 46
    for i in range(6):
        xx = tx0 + i * 150 + 20
        d.rounded_rectangle((xx, y3, xx + 110, y3 + 26), 6, fill=(255, 255, 255, 60))
    # waveform
    y4 = y3 + 70
    for xx in range(int(tx0), int(tx1), 6):
        a = abs(math.sin(xx * 0.05) * math.sin(xx * 0.013 + 1.3)) * 26 + 3
        d.line((xx, y4 - a, xx, y4 + a), fill=(236, 120, 80), width=3)
    # playhead + progress
    pr = ease_in_out(prog(t, 0.2, 2.0))
    px = tx0 + (tx1 - tx0) * pr
    d.line((px, ty - 12, px, y4 + 34), fill=(255, 255, 255), width=4)
    d.polygon([(px - 12, ty - 22), (px + 12, ty - 22), (px, ty - 6)], fill=(255, 255, 255))
    d.text((w - 30, h - 24), f"{int(pr * 100)}%", font=font("oswald", 40, 700), fill=(255, 255, 255), anchor="rb")
    return p


def render(ctx, tl, ts):
    t = tl
    out = Image.new("RGB", (W, H), PAPER)
    vid, _ = ctx.crop(ts, (0, 330, W, 330 + 960), (W, 960))
    out.paste(grade(vid, sat=1.05, contrast=1.05), (0, 960))
    d = ImageDraw.Draw(out)
    q = ease_out(prog(t, 0.0, 0.4))
    top = Image.new("RGB", (W, 960), PAPER)
    td = ImageDraw.Draw(top)
    f1, f2 = font("oswald", 80, 700), font("playfair", 84, 600)
    s1, s2 = "Claude ", "рендерит"
    x = (W - tw(s1, f1) - tw(s2, f2)) / 2
    td.text((x, 70), s1, font=f1, fill=INK)
    td.text((x + tw(s1, f1), 62), s2, font=f2, fill=(217, 119, 87))
    ed = editor(ctx, t, ts)
    sc = 0.9 + 0.1 * ease_back(prog(t, 0.05, 0.5))
    e2 = ed.resize((int(ed.width * sc), int(ed.height * sc)), Image.LANCZOS)
    top.paste(e2, (int(W / 2 - e2.width / 2), int(560 - e2.height / 2)), e2)
    out.paste(top, (0, int(-960 * (1 - q))))
    return out
