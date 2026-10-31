"""glass-widgets — app screens recreated as frosted-glass widgets around you (behind your head)."""
import numpy as np
from PIL import Image, ImageDraw
from lib.core import *

NAME = "glass-widgets"
DESC = "стеклянные виджеты вокруг тебя"
DURATION = 3.0
REEL_DELAY = 0.55  # in the showcase reel, start the animation once the card is fullscreen
# (local time, sound) — collected by the renderer
SFX = [(0.05 + i * 0.09, "pop") for i in range(7)] + [(1.0, "chime")]

BARS = [0.55, 0.9, 0.7, 1.0, 0.62, 0.4, 0.8]


def _pop(tl, i):
    p = prog(tl, 0.05 + i * 0.09, 0.45)
    return ease_back(p, 2.2), clamp(p * 3)


def _box_scaled(box, s):
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    w, h = (x1 - x0) * s, (y1 - y0) * s
    return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)


def _content(size, draw_fn):
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(layer), layer)
    return layer


def _widget(img, box, s, a, draw_fn, tint=(255, 255, 255), alpha=.14, r=40):
    if s <= 0.02:
        return
    b = _box_scaled(box, s)
    glass(img, b, r=int(r * s), tint=tint, alpha=alpha, opacity=a)
    w, h = int(box[2] - box[0]), int(box[3] - box[1])
    lay = _content((w, h), draw_fn)
    lw, lh = max(2, int(w * s)), max(2, int(h * s))
    lay = lay.resize((lw, lh), Image.LANCZOS)
    if a < 1:
        al = lay.split()[3].point(lambda v: int(v * a))
        lay.putalpha(al)
    img.paste(lay, (int(b[0]), int(b[1])), lay)


def render(ctx, tl, ts):
    base, mask = ctx.src(ts, zoom=1.12, anchor=(540, 640))
    base = grade(base, sat=1.05, contrast=1.04)
    img = base.copy()
    t = tl
    W_ = (255, 255, 255)

    # 1 — big counter card
    def big(d, L):
        d.text((34, 26), "Claude", font=font("sans", 30, 600), fill=(255, 255, 255, 200))
        n = int(round(36 * ease_out(prog(t, 0.2, 0.9))))
        d.text((30, 50), f"{n}", font=font("oswald", 150, 700), fill=W_)
        d.text((36, 276), "эффектов", font=font("sans", 32, 600), fill=W_)
        d.text((36, 316), "один клип", font=font("sans", 28, 500), fill=(255, 255, 255, 190))
    s, a = _pop(t, 0)
    _widget(img, (56, 150, 396, 520), s, a, big)

    # 2 — render progress
    def rend(d, L):
        d.ellipse((30, 36, 48, 54), fill=(255, 92, 72))
        d.text((60, 28), "Рендер", font=font("sans", 30, 600), fill=W_)
        p = ease_in_out(prog(t, 0.3, 2.2))
        d.rounded_rectangle((30, 84, 410, 100), 8, fill=(255, 255, 255, 70))
        d.rounded_rectangle((30, 84, 30 + max(16, 380 * p), 100), 8, fill=W_)
        d.text((30, 116), f"4K · 30 fps · {int(p * 100)}%", font=font("mono", 24, 500), fill=(255, 255, 255, 200))
    s, a = _pop(t, 1)
    _widget(img, (584, 150, 1024, 316), s, a, rend)

    # 3 — profile chip
    def prof(d, L):
        d.text((30, 24), ctx.cfg["name"].split()[0], font=font("sans", 34, 700), fill=W_)
        d.text((30, 66), ctx.cfg["handle"], font=font("sans", 26, 500), fill=(255, 255, 255, 200))
        d.ellipse((330, 22, 410, 102), fill=(217, 119, 87))
        d.text((370, 62), ctx.cfg["name"][0], font=font("oswald", 46, 700), fill=W_, anchor="mm")
    s, a = _pop(t, 2)
    _widget(img, (584, 340, 1024, 466), s, a, prof)

    # 4 — top reels mini chart
    def chart(d, L):
        d.text((28, 22), "Топ рилс", font=font("sans", 26, 600), fill=W_)
        d.text((28, 56), "197K", font=font("oswald", 64, 700), fill=(255, 210, 120))
        for i, v in enumerate(BARS):
            g = ease_out(prog(t, 0.35 + i * 0.06, 0.5)) * v
            x = 30 + i * 40
            d.rounded_rectangle((x, 250 - 120 * g, x + 26, 250), 5, fill=(236, 92, 70) if i != 3 else W_)
    s, a = _pop(t, 3)
    _widget(img, (56, 548, 360, 830), s, a, chart)

    # 5 — 4K ring
    def ring(d, L):
        p = ease_out(prog(t, 0.4, 1.2))
        d.ellipse((22, 22, 178, 178), outline=(255, 255, 255, 60), width=12)
        d.arc((22, 22, 178, 178), -90, -90 + 360 * p, fill=(80, 220, 120), width=12)
        d.text((100, 100), "4K", font=font("oswald", 58, 700), fill=W_, anchor="mm")
    s, a = _pop(t, 4)
    _widget(img, (814, 560, 1014, 760), s, a, ring, r=100)

    # 6 — orange accent pill
    def pill(d, L):
        spark(d, 48, 55, 24, fill=W_)
        d.text((78, 22), "без таймлайна", font=font("sans", 30, 700), fill=W_)
        d.text((78, 62), "одна команда", font=font("sans", 24, 500), fill=(255, 255, 255, 210))
    s, a = _pop(t, 5)
    _widget(img, (56, 860, 400, 970), s, a, pill, tint=(217, 119, 87), alpha=.55, r=34)

    # person in front of all widgets
    if mask is not None:
        img = Image.fromarray((np.asarray(base, np.float32) * mask[..., None]
                               + np.asarray(img, np.float32) * (1 - mask[..., None])).astype(np.uint8))

    # 7 — "edited by Claude" pill (in front)
    def ed(d, L):
        f = font("sans", 34, 600)
        spark(d, 52, 45, 20, fill=(240, 140, 105))
        d.text((90, 24), "Смонтировано", font=f, fill=W_)
        d.text((90 + tw("Смонтировано ", f), 24), "Claude", font=font("sans", 34, 800), fill=(240, 140, 105))
    s, a = _pop(t, 6)
    _widget(img, (270, 1540, 810, 1630), s, a, ed, alpha=.22, r=45)
    return img
