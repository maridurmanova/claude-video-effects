"""Claude-app style phone UI: composer + keyboard, chat with dot-matrix render, zoom to fullscreen."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from .core import *

KB_ROWS = ["qwertyuiop", "asdfghjkl", "zxcvbnm"]
KB_Y = 1250
CARD = (60, 520, 60 + 560, 520 + 996)


def _base():
    img = Image.new("RGB", (W, H), UI_BG)
    d = ImageDraw.Draw(img)
    # top bar
    for i in range(3):
        d.line((60, 100 + i * 14, 100, 100 + i * 14), fill=UI_DIM, width=4)
    d.rounded_rectangle((370, 78, 710, 150), 36, fill=UI_PANEL)
    d.rounded_rectangle((545, 86, 702, 142), 30, fill=(78, 78, 74))
    d.text((457, 114), "Чат", font=font("sans", 32, 500), fill=UI_DIM, anchor="mm")
    d.text((623, 114), "Код", font=font("sans", 32, 700), fill=UI_TEXT, anchor="mm")
    d.rounded_rectangle((980, 92, 1024, 136), 8, outline=UI_DIM, width=4)
    return img, d


def _thumb(img, size, r=18):
    t = img.resize(size, Image.LANCZOS)
    o = Image.new("RGBA", size, (0, 0, 0, 0))
    o.paste(t, (0, 0), rrect_mask(size, r))
    return o


def keyboard(img, pressed=None, typed_word=""):
    d = ImageDraw.Draw(img)
    d.rectangle((0, KB_Y, W, H), fill=(30, 30, 30))
    # suggestion strip
    if typed_word:
        d.text((W // 2, KB_Y + 52), f"«{typed_word}»", font=font("sans", 34, 500), fill=UI_TEXT, anchor="mm")
    kw, kh, gap = 98, 118, 10
    keys = {}
    y = KB_Y + 120
    for r, row in enumerate(KB_ROWS):
        total = len(row) * kw + (len(row) - 1) * gap
        x = (W - total) / 2
        for ch in row:
            d.rounded_rectangle((x, y, x + kw, y + kh), 14, fill=(92, 92, 90))
            d.text((x + kw / 2, y + kh / 2), ch, font=font("sans", 50, 400), fill=(255, 255, 255), anchor="mm")
            keys[ch] = (x, y)
            x += kw + gap
        y += kh + 26
    # bottom row
    d.rounded_rectangle((20, y, 230, y + kh), 14, fill=(60, 60, 58))
    d.text((125, y + kh / 2), "123", font=font("sans", 38, 500), fill=(255, 255, 255), anchor="mm")
    d.rounded_rectangle((250, y, 820, y + kh), 14, fill=(92, 92, 90))
    d.text((535, y + kh / 2), "пробел", font=font("sans", 38, 500), fill=(255, 255, 255), anchor="mm")
    d.rounded_rectangle((840, y, 1060, y + kh), 14, fill=(60, 60, 58))
    d.text((950, y + kh / 2), "/", font=font("sans", 50, 500), fill=(255, 255, 255), anchor="mm")
    keys["/"] = (900, y); keys[" "] = (480, y); keys["-"] = (900, y)
    if pressed and pressed in keys:
        x, y = keys[pressed]
        bw, bh = 140, 210
        bx, by = x + kw / 2 - bw / 2, y + kh - bh
        d.rounded_rectangle((bx, by, bx + bw, by + bh), 22, fill=(130, 130, 128))
        d.text((bx + bw / 2, by + 62), pressed, font=font("sans", 76, 500), fill=(255, 255, 255), anchor="mm")


def compose(text, thumb, popup=None, pressed=None, cursor=True):
    img, d = _base()
    # popup with slash command suggestions
    cy0 = 880
    if popup:
        h = 110 * len(popup) + 20
        d.rounded_rectangle((40, cy0 - h - 16, 1040, cy0 - 16), 28, fill=UI_PANEL)
        for i, (a, b) in enumerate(popup):
            y = cy0 - h - 16 + 22 + i * 110
            d.text((80, y + 8), a, font=font("sans", 40, 700), fill=UI_TEXT)
            d.text((80, y + 60), b, font=font("sans", 26, 500), fill=UI_DIM)
    d.rounded_rectangle((40, cy0, 1040, 1220), 34, fill=UI_PANEL)
    if thumb is not None:
        th = _thumb(thumb, (104, 184))
        img.paste(th, (76, cy0 + 26), th)
        d.ellipse((160, cy0 + 18, 196, cy0 + 54), fill=(240, 240, 238))
        d.line((170, cy0 + 28, 186, cy0 + 44), fill=(60, 60, 60), width=4)
        d.line((186, cy0 + 28, 170, cy0 + 44), fill=(60, 60, 60), width=4)
    ty = cy0 + 236
    col = CLAY if text.startswith("/") else UI_TEXT
    f = font("sans", 44, 500)
    d.text((80, ty), text, font=f, fill=col, anchor="ls")
    if cursor:
        x = 80 + tw(text, f) + 4
        d.line((x, ty - 42, x, ty + 6), fill=CLAY, width=4)
    # + and mic / send
    d.text((80, cy0 + 300), "+", font=font("sans", 52, 400), fill=UI_DIM, anchor="lm")
    d.ellipse((940, cy0 + 262, 1010, cy0 + 332), fill=CLAY)
    d.polygon([(975, cy0 + 278), (958, cy0 + 300), (992, cy0 + 300)], fill=(255, 255, 255))
    d.line((975, cy0 + 296, 975, cy0 + 318), fill=(255, 255, 255), width=6)
    word = text.split(" ")[-1].lstrip("/")
    keyboard(img, pressed, word)
    return img


def dot_matrix(img, p, seed=0, cell=12):
    """Dissolve: orange dot-matrix of `img` resolving into the picture as p goes 0→1."""
    w, h = img.size
    gw, gh = w // cell + 1, h // cell + 1
    small = np.asarray(img.resize((gw, gh), Image.BILINEAR).convert("L"), np.float32) / 255
    yy, xx = np.mgrid[0:h, 0:w]
    ci, cj = yy // cell, xx // cell
    dy = yy - (ci * cell + cell / 2); dx = xx - (cj * cell + cell / 2)
    dist = np.sqrt(dx * dx + dy * dy)
    lum = small[ci.clip(0, gh - 1), cj.clip(0, gw - 1)]
    rng = np.random.default_rng(seed)
    tw_ = rng.uniform(0.55, 1.0, (gh, gw))[ci, cj]
    r = 0.6 + lum * cell * 0.48
    a = np.clip(r - dist + 0.5, 0, 1) * tw_
    dots_col = np.array(CLAY, np.float32) * (0.45 + 0.75 * lum[..., None])
    bg = np.array((26, 26, 25), np.float32)
    dots = bg * (1 - a[..., None]) + dots_col * a[..., None]
    th = (0.55 * rng.uniform(0, 1, (gh, gw)) + 0.45 * np.linspace(0, 1, gh)[:, None])[ci, cj]
    reveal = np.clip((p * 1.25 - th) * 6, 0, 1)[..., None]
    out = dots * (1 - reveal) + np.asarray(img, np.float32) * reveal
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def chat(cmd, thumb, status, card_img, card_p, zoom=0.0, reply=None, show_card=True):
    """Chat view. card_p: dissolve progress. zoom: 0 → card in chat, 1 → fullscreen."""
    img, d = _base()
    y = 190
    if thumb is not None:
        th = _thumb(thumb, (110, 196))
        img.paste(th, (W - 60 - 110, y), th)
        y += 230
    f = font("sans", 40, 500)
    d.rounded_rectangle((W - 60 - tw(cmd, f) - 50, y - 6, W - 60, y + 66), 30, fill=UI_PANEL)
    d.text((W - 85, y + 30), cmd, font=f, fill=CLAY if cmd.startswith("/") else UI_TEXT, anchor="rm")
    y += 110
    if status:
        d.ellipse((60, y + 6, 82, y + 28), fill=CLAY)
        d.text((100, y + 17), status, font=font("sans", 32, 500), fill=UI_DIM, anchor="lm")
        d.text((W - 60, y + 17), "УСКОРЕНО", font=font("mono", 20, 600), fill=(110, 110, 104), anchor="rm")
    if reply:
        lines = reply
        for i, ln in enumerate(lines):
            d.text((60, y + 20 + i * 52), ln, font=font("sans", 38, 500), fill=UI_TEXT, anchor="lm")
    # bottom input
    d.rounded_rectangle((40, 1770, 1040, 1870), 50, fill=UI_PANEL)
    d.text((90, 1820), "+   Ответить Claude…", font=font("sans", 32, 500), fill=UI_DIM, anchor="lm")
    d.ellipse((960, 1790, 1020, 1850), fill=(78, 78, 74))
    if not show_card or card_img is None:
        return img
    x0, y0, x1, y1 = CARD
    z = ease_in_out(zoom)
    bx0, by0, bx1, by1 = lerp(x0, 0, z), lerp(y0, 0, z), lerp(x1, W, z), lerp(y1, H, z)
    bw, bh = int(bx1 - bx0), int(by1 - by0)
    if z <= 0:
        card = dot_matrix(card_img.resize((x1 - x0, y1 - y0), Image.LANCZOS), card_p)
        card = card.resize((bw, bh))
    else:
        card = card_img.resize((bw, bh), Image.LANCZOS)
    rad = int(28 * (1 - z))
    if z > 0:
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((bx0, by0 + 20, bx1, by1 + 20), rad + 8, fill=(0, 0, 0, 150))
        sh = sh.filter(ImageFilter.GaussianBlur(30))
        img = img.convert("RGBA"); img.alpha_composite(sh); img = img.convert("RGB")
    img.paste(card, (int(bx0), int(by0)), rrect_mask((bw, bh), rad) if rad else None)
    return img
