"""documentary — B&W doc-series look: pink glow behind you, title behind your head, lower third, follow click."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from lib.core import *

NAME = "documentary"
DESC = "док-серия: ч/б, титр за головой, подпись"
DURATION = 3.0
REEL_DELAY = 0.25  # in the showcase reel, start the animation once the card is fullscreen
SFX = [(0.1, "pop"), (0.3, "pop"), (0.5, "pop"), (0.75, "swoosh"), (1.55, "click")]

LINES = [[("ОДИН ", (255, 255, 255)), ("КЛИП.", PINK)],
         [("7 ЭФФЕКТОВ.", (255, 255, 255))],
         [("НОЛЬ ", PINK), ("ПРИЛОЖЕНИЙ.", (255, 255, 255))]]


def render(ctx, tl, ts):
    t = tl
    src, mask = ctx.src(ts, zoom=1.04, anchor=(540, 560))
    bw = grade(src, bw=True, contrast=1.22, bright=-18)
    # grain
    a = np.asarray(bw, np.float32)
    rng = np.random.default_rng(int(ts * 30))
    a = np.clip(a + rng.normal(0, 7, a.shape[:2])[..., None], 0, 255)
    bw = Image.fromarray(a.astype(np.uint8))

    hx, htop, hw = head_from_mask(mask) if mask is not None else (520, 330, 300)
    cy = htop + 230

    # layer behind the person: glow, ring, title
    back = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(g)
    p = ease_out(prog(t, 0.0, 0.6))
    R = 420 * (0.6 + 0.4 * p)
    gd.ellipse((hx - R, cy - R, hx + R, cy + R), fill=PINK + (int(170 * p),))
    g = g.filter(ImageFilter.GaussianBlur(70))
    back.alpha_composite(g)
    rd = ImageDraw.Draw(back)
    R2 = 250 * (0.7 + 0.3 * p)
    rd.ellipse((hx - R2, cy - R2, hx + R2, cy + R2), outline=PINK + (int(200 * p),), width=5)

    f = font("oswald", 138, 700)
    widest = max(sum(tw(s, f) for s, _ in line) for line in LINES)
    f = font("oswald", int(138 * min(0.9, 940 / widest)), 700)
    y = 105
    for i, line in enumerate(LINES):
        q = ease_out(prog(t, 0.1 + i * 0.2, 0.35))
        if q <= 0:
            y += 128; continue
        total = sum(tw(s, f) for s, _ in line)
        x = W - 70 - total
        for s, c in line:
            rd.text((x, y + (1 - q) * 40), s, font=f, fill=c + (int(255 * q),))
            x += tw(s, f)
        y += 128

    out = bw.convert("RGBA")
    out.alpha_composite(back)
    out = out.convert("RGB")
    if mask is not None:
        out = Image.fromarray((np.asarray(bw, np.float32) * mask[..., None]
                               + np.asarray(out, np.float32) * (1 - mask[..., None])).astype(np.uint8))
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)

    # top kicker
    d.text((W // 2, 64), ctx.cfg["series"], font=font("mono", 24, 600), fill=(255, 255, 255, 220), anchor="mm")

    # huge faded "ДЕНЬ 01"
    d.text((W - 40, 1770), "ДЕНЬ 01", font=font("oswald", 220, 700), fill=(255, 255, 255, 22), anchor="rs")

    # lower third
    q = ease_out(prog(t, 0.6, 0.4))
    if q > 0:
        name = ctx.cfg["name"].upper()
        fn = font("oswald", 64, 700)
        w = tw(name, fn) + 60
        x0 = -w + (w + 60) * q
        d.rectangle((x0, 1440, x0 + w, 1530), fill=PINK)
        d.text((x0 + 30, 1485), name, font=fn, fill=(255, 255, 255), anchor="lm")
        d.text((x0 + 30, 1580), ctx.cfg["handle"], font=font("sans", 36, 500), fill=(255, 255, 255, int(230 * q)), anchor="lm")

    # follow button + cursor
    q = ease_back(prog(t, 0.45, 0.4))
    if q > 0:
        bx, by, bw_, bh = 640, 1250, 340, 96
        clicked = t >= 1.55
        sc = 1 - 0.08 * max(0, 1 - abs(t - 1.55) / 0.08) if t > 1.45 else 1
        cx, cyy = bx + bw_ / 2, by + bh / 2
        ww, hh = bw_ * q * sc, bh * q * sc
        box = (cx - ww / 2, cyy - hh / 2, cx + ww / 2, cyy + hh / 2)
        if clicked:
            d.rounded_rectangle(box, 22, fill=(255, 255, 255), outline=(0, 0, 0), width=3)
            d.text((cx, cyy), "Вы подписаны", font=font("sans", 38, 700), fill=(10, 10, 10), anchor="mm")
        else:
            d.rounded_rectangle(box, 22, fill=(0, 149, 246))
            d.text((cx, cyy), "Подписаться", font=font("sans", 38, 700), fill=(255, 255, 255), anchor="mm")
        # cursor
        cp = ease_in_out(prog(t, 0.9, 0.6))
        if t > 0.8:
            px, py = lerp(1040, cx + 40, cp), lerp(1700, cyy + 20, cp)
            pts = [(px, py), (px, py + 62), (px + 16, py + 48), (px + 28, py + 74), (px + 40, py + 68), (px + 28, py + 44), (px + 48, py + 44)]
            d.polygon(pts, fill=(255, 255, 255), outline=(0, 0, 0))
    out = out.convert("RGBA"); out.alpha_composite(ov)
    return out.convert("RGB")
