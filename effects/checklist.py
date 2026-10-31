"""checklist — a glass card where Claude ticks off every editing step."""
import numpy as np
from PIL import Image, ImageDraw
from lib.core import *

NAME = "checklist"
DESC = "Claude отмечает каждый шаг монтажа"
DURATION = 3.0
STEPS = [("Нашёл лицо", "каждый кадр"), ("Вырезал тебя из комнаты", "AI-маска"),
         ("Поставил текст за тобой", "глубина"), ("Покрасил цвет", "тёплый"), ("Отрендерил в 4K", "2160p")]
T0, DT = 0.45, 0.28
SFX = [(0.0, "swoosh")] + [(T0 + i * DT, "tick") for i in range(len(STEPS))] + [(T0 + 5 * DT + 0.1, "chime")]
GREEN = (52, 199, 89)


def render(ctx, tl, ts):
    t = tl
    img, _ = ctx.src(ts, zoom=1.08, anchor=(540, 600), with_mask=False)
    img = grade(img, sat=1.04, contrast=1.04)
    q = ease_out(prog(t, 0.0, 0.45))
    x0, x1 = 60, 1020
    h = 520
    y0 = lerp(1960, 1150, q)
    glass(img, (x0, y0, x1, y0 + h), r=44, tint=(20, 20, 22), alpha=0.55, border=0.25, blur=26)
    d = ImageDraw.Draw(img, "RGBA")
    done = sum(1 for i in range(len(STEPS)) if t >= T0 + i * DT)
    spark(d, x0 + 58, y0 + 62, 20, fill=CLAY)
    d.text((x0 + 92, y0 + 62), "Claude монтирует твой клип", font=font("sans", 36, 700), fill=(255, 255, 255), anchor="lm")
    d.text((x1 - 40, y0 + 62), f"{max(done, 1)} из 5", font=font("mono", 24, 500), fill=(255, 255, 255, 150), anchor="rm")
    for i, (s, tag) in enumerate(STEPS):
        y = y0 + 150 + i * 78
        st = T0 + i * DT
        ok = t >= st
        cx = x0 + 58
        if ok:
            pop = ease_back(prog(t, st, 0.25), 3)
            r = 22 * pop
            d.ellipse((cx - r, y - r, cx + r, y + r), fill=GREEN)
            if pop > 0.6:
                d.line([(cx - 10, y), (cx - 3, y + 8), (cx + 11, y - 8)], fill=(255, 255, 255), width=5, joint="curve")
        else:
            d.ellipse((cx - 22, y - 22, cx + 22, y + 22), outline=(255, 255, 255, 120), width=3)
        d.text((x0 + 100, y), s, font=font("sans", 36, 700 if ok else 500),
               fill=(255, 255, 255, 255 if ok else 140), anchor="lm")
        d.text((x1 - 40, y), tag, font=font("mono", 24, 500), fill=(120, 230, 150, 230) if ok else (255, 255, 255, 90), anchor="rm")
    return img
