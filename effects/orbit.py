"""orbit — mini reels orbit around you, passing behind and in front of you."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from lib.core import *

NAME = "orbit"
DESC = "рилс-карточки летают вокруг тебя"
DURATION = 3.0
SFX = [(0.0, "whoosh"), (0.9, "whoosh"), (1.8, "whoosh")]

N = 8


def _cards(ctx):
    if ctx.thumbs:
        return [ctx.thumbs[i % len(ctx.thumbs)] for i in range(N)]
    # fall back: stills of the clip with different grades
    out = []
    for i in range(N):
        f = ctx.clip.frame((i * 2.7) % ctx.clip.duration)
        out.append(grade(f, sat=0.6 + 0.15 * i, contrast=1.1, bw=(i % 3 == 0)))
    return out


def _card(img, w, h):
    c = img.resize((w, h), Image.LANCZOS)
    m = rrect_mask((w, h), int(w * 0.09))
    o = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    o.paste(c, (0, 0), m)
    ImageDraw.Draw(o).rounded_rectangle((0, 0, w - 1, h - 1), int(w * .09), outline=(255, 255, 255, 220), width=3)
    return o


def render(ctx, tl, ts):
    t = tl
    base, mask = ctx.src(ts, zoom=1.1, anchor=(540, 700))
    base = grade(base, sat=1.04, contrast=1.05)
    hx, htop, hw = head_from_mask(mask) if mask is not None else (520, 360, 300)
    cx, cy = hx, htop + 430
    grow = ease_out(prog(t, 0.0, 0.7))
    rx, ry = 470 * grow, 170 * grow
    tilt = -0.18
    cards = _cards(ctx)
    items = []
    for i in range(N):
        a = i / N * math.tau + t * 1.25 + 0.3
        x = math.cos(a) * rx
        y = math.sin(a) * ry
        x, y = x * math.cos(tilt) - y * math.sin(tilt), x * math.sin(tilt) + y * math.cos(tilt)
        depth = math.sin(a)            # >0 front, <0 behind
        s = (0.78 + 0.32 * (depth + 1) / 2) * (0.4 + 0.6 * grow)
        items.append((depth, cx + x, cy + y - 120, s, cards[i]))
    items.sort(key=lambda v: v[0])

    def draw(layer, sel):
        for depth, x, y, s, im in sel:
            w, h = int(170 * s), int(302 * s)
            c = _card(im, w, h)
            if depth < 0:
                dark = Image.new("RGBA", c.size, (0, 0, 0, int(70 * -depth)))
                c = Image.alpha_composite(c, Image.composite(dark, Image.new("RGBA", c.size), c.split()[3]))
            sh = Image.new("RGBA", (w + 60, h + 60), (0, 0, 0, 0))
            ImageDraw.Draw(sh).rounded_rectangle((30, 40, w + 30, h + 40), 14, fill=(0, 0, 0, 120))
            sh = sh.filter(ImageFilter.GaussianBlur(14))
            layer.alpha_composite(sh, (int(x - w / 2 - 30), int(y - h / 2 - 30)))
            layer.alpha_composite(c, (int(x - w / 2), int(y - h / 2)))

    back = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw(back, [v for v in items if v[0] < 0])
    out = base.convert("RGBA"); out.alpha_composite(back); out = out.convert("RGB")
    if mask is not None:
        out = Image.fromarray((np.asarray(base, np.float32) * mask[..., None]
                               + np.asarray(out, np.float32) * (1 - mask[..., None])).astype(np.uint8))
    front = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw(front, [v for v in items if v[0] >= 0])
    out = out.convert("RGBA"); out.alpha_composite(front)
    return out.convert("RGB")
