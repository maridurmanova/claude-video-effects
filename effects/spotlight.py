"""spotlight — dark room, spotlight on you, neon word glowing behind your head."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from lib.core import *

NAME = "spotlight"
DESC = "прожектор и неон за головой"
DURATION = 3.0
REEL_DELAY = 0.8  # in the showcase reel, start the animation once the card is fullscreen
SFX = [(0.0, "buzz"), (0.25, "buzz"), (0.45, "neon")]
WORD = "CLAUDE"
NEON = (255, 112, 92)


def _flicker(t):
    if t < 0:
        return 0
    seq = [(0.0, .9), (0.06, 0), (0.14, .7), (0.2, 0), (0.28, 1), (0.33, .25), (0.45, 1)]
    v = 0
    for st, val in seq:
        if t >= st:
            v = val
    return v


def render(ctx, tl, ts):
    t = tl
    src, mask = ctx.src(ts, zoom=1.16, anchor=(540, 600))
    hx, htop, hw = head_from_mask(mask) if mask is not None else (520, 330, 300)
    # dark grade + spotlight
    a = np.asarray(grade(src, sat=0.85, contrast=1.15), np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    on = ease_out(prog(t, 0.0, 0.5))
    r = np.sqrt(((xx - hx) / 520) ** 2 + ((yy - (htop + 480)) / 760) ** 2)
    light = np.clip(1.25 - r, 0.12, 1.0) ** 1.6
    k = 1 - on * (1 - light)
    a = a * k[..., None] * (1 - 0.25 * on)
    a[..., 0] *= 1.04; a[..., 2] *= 0.9
    dark = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

    fl = _flicker(t)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if fl > 0:
        f = font("playfair", 250, 900)
        f = font("playfair", int(250 * min(1.0, 980 / tw(WORD, f))), 900)
        y = htop - 70
        txt = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(txt).text((W // 2, y), WORD, font=f, fill=NEON + (255,), anchor="mm")
        glow = txt.filter(ImageFilter.GaussianBlur(26))
        glow2 = txt.filter(ImageFilter.GaussianBlur(8))
        core = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(core).text((W // 2, y), WORD, font=f, fill=(255, 225, 210, 255), anchor="mm")
        for lay, mul in ((glow, 1.0), (glow, 0.8), (glow2, 1.0), (core, 1.0)):
            al = lay.split()[3].point(lambda v: int(min(255, v * fl * mul)))
            l2 = lay.copy(); l2.putalpha(al)
            layer.alpha_composite(l2)
        # wall reflection
        refl = glow.resize((W, H)).filter(ImageFilter.GaussianBlur(60))
        al = refl.split()[3].point(lambda v: int(v * 0.5 * fl)); refl.putalpha(al)
        layer.alpha_composite(refl)
    out = dark.convert("RGBA"); out.alpha_composite(layer); out = out.convert("RGB")
    if mask is not None:
        out = Image.fromarray((np.asarray(dark, np.float32) * mask[..., None]
                               + np.asarray(out, np.float32) * (1 - mask[..., None])).astype(np.uint8))
    q = ease_out(prog(t, 0.6, 0.4))
    if q > 0:
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(ov).text((W // 2, 1640), "в главной роли — ты", font=font("playfair", 52, 500), fill=(255, 225, 210, int(235 * q)), anchor="mm")
        out = out.convert("RGBA"); out.alpha_composite(ov); out = out.convert("RGB")
    return out
