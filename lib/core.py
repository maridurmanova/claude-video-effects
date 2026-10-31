"""Shared helpers: video IO, fonts, easing, glass panels, text."""
import os, subprocess, json, math
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H, FPS = 1080, 1920, 30

# ---------------------------------------------------------------- palette
CLAY = (217, 119, 87)        # Claude orange
CREAM = (245, 240, 230)
INK = (24, 24, 22)
UI_BG = (38, 38, 36)
UI_PANEL = (48, 48, 46)
UI_LINE = (70, 70, 66)
UI_TEXT = (236, 234, 228)
UI_DIM = (150, 148, 140)
PINK = (236, 64, 140)


# ---------------------------------------------------------------- fonts
_FONT_CACHE = {}
FONT_FILES = {
    "oswald": "Oswald.ttf",          # narrow bold caps (Cyrillic)
    "playfair": "PlayfairItalic.ttf",  # accent italic
    "sans": "Montserrat.ttf",        # UI / subtitles
    "mono": "JBMono.ttf",            # tech labels
}


def font(kind, size, weight=None):
    key = (kind, int(size), weight)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    f = ImageFont.truetype(os.path.join(ROOT, "fonts", FONT_FILES[kind]), int(size))
    if weight is not None:
        try:
            f.set_variation_by_axes([weight])
        except Exception:
            pass
    _FONT_CACHE[key] = f
    return f


# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out(x):
    x = clamp(x); return 1 - (1 - x) ** 3


def ease_in_out(x):
    x = clamp(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2


def ease_back(x, s=1.70158):
    x = clamp(x); c3 = s + 1
    return 1 + c3 * (x - 1) ** 3 + s * (x - 1) ** 2


def prog(t, start, dur):
    return clamp((t - start) / dur)


def lerp(a, b, x):
    return a + (b - a) * x


# ---------------------------------------------------------------- video IO
def probe(path):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                   "stream=width,height,r_frame_rate:format=duration", "-of", "json", path])
    d = json.loads(out)
    s = d["streams"][0]
    n, m = s["r_frame_rate"].split("/")
    return dict(w=s["width"], h=s["height"], fps=float(n) / float(m), duration=float(d["format"]["duration"]))


class Clip:
    """Random-access frames of the source clip, cover-fitted to 1080x1920.

    Frames are extracted once to JPEGs in a cache dir (cheap on disk, fast to seek)."""

    def __init__(self, path, cache=None):
        self.path = path
        self.info = probe(path)
        self.duration = self.info["duration"]
        self.dir = cache or path + ".frames"
        if not os.path.isdir(self.dir) or not os.listdir(self.dir):
            os.makedirs(self.dir, exist_ok=True)
            vf = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS}"
            subprocess.check_call(["ffmpeg", "-v", "error", "-i", path, "-vf", vf, "-q:v", "2",
                                   os.path.join(self.dir, "%05d.jpg")])
        self.n = len([f for f in os.listdir(self.dir) if f.endswith(".jpg")])
        self._cache = {}
        # skip leading black frames (camera start)
        self.offset = 0
        for i in range(1, min(self.n, 45)):
            im = Image.open(os.path.join(self.dir, f"{i:05d}.jpg")).reduce(8)
            if np.asarray(im).mean() > 8:
                self.offset = i - 1
                break
        self.duration = (self.n - self.offset) / FPS

    def frame(self, t):
        i = int(clamp(round(t * FPS) + self.offset, 0, self.n - 1)) + 1
        if i not in self._cache:
            if len(self._cache) > 40:
                self._cache.pop(next(iter(self._cache)))
            self._cache[i] = Image.open(os.path.join(self.dir, f"{i:05d}.jpg")).convert("RGB")
        return self._cache[i].copy()


class Writer:
    def __init__(self, out, crf=14):
        self.p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                                   "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
                                   "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p", out],
                                  stdin=subprocess.PIPE)

    def write(self, img):
        self.p.stdin.write(np.asarray(img.convert("RGB"), dtype=np.uint8).tobytes())

    def close(self):
        self.p.stdin.close(); self.p.wait()


# ---------------------------------------------------------------- drawing
def rrect_mask(size, r):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], r, fill=255)
    return m


def glass(base, box, r=36, blur=22, tint=(255, 255, 255), alpha=0.16, border=0.35, sat=1.45, opacity=1.0):
    """Frosted-glass panel on `base` (in place). box = (x0,y0,x1,y1)."""
    x0, y0, x1, y1 = [int(v) for v in box]
    x0, y0 = max(x0, -2000), max(y0, -2000)
    w, h = x1 - x0, y1 - y0
    if w <= 4 or h <= 4 or opacity <= 0.01:
        return
    pad = blur * 2
    cx0, cy0 = max(0, x0 - pad), max(0, y0 - pad)
    cx1, cy1 = min(base.width, x1 + pad), min(base.height, y1 + pad)
    if cx1 <= cx0 or cy1 <= cy0:
        return
    region = np.asarray(base.crop((cx0, cy0, cx1, cy1))).astype(np.float32)
    region = cv2.GaussianBlur(region, (0, 0), blur)
    g = region.mean(axis=2, keepdims=True)
    region = np.clip(g + (region - g) * sat, 0, 255)
    panel = Image.new("RGB", (w, h))
    panel.paste(Image.fromarray(region.astype(np.uint8)), (cx0 - x0, cy0 - y0))
    arr = np.asarray(panel).astype(np.float32)
    # tint + top-left sheen
    yy, xx = np.mgrid[0:h, 0:w]
    sheen = np.clip(1 - (xx / w * .6 + yy / h), 0, 1)[..., None] * 0.18
    arr = arr * (1 - alpha) + np.array(tint, np.float32) * alpha
    arr = arr + 255 * sheen
    panel = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    m = rrect_mask((w, h), r)
    if opacity < 1:
        m = m.point(lambda v: int(v * opacity))
    base.paste(panel, (x0, y0), m)
    if border > 0:
        ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(ov).rounded_rectangle([0, 0, w - 1, h - 1], r, outline=(255, 255, 255, int(255 * border * opacity)), width=2)
        base.paste(ov, (x0, y0), ov)


def text(draw, xy, s, f, fill=(255, 255, 255), anchor="la", shadow=None, **kw):
    if shadow:
        sx, sy, sc = shadow
        draw.text((xy[0] + sx, xy[1] + sy), s, font=f, fill=sc, anchor=anchor, **kw)
    draw.text(xy, s, font=f, fill=fill, anchor=anchor, **kw)


def paste_scaled(base, img, center, scale, radius=0, opacity=1.0, shadow=True):
    """Paste img scaled around center with rounded corners and soft shadow."""
    w, h = max(2, int(img.width * scale)), max(2, int(img.height * scale))
    im = img.resize((w, h), Image.LANCZOS)
    x, y = int(center[0] - w / 2), int(center[1] - h / 2)
    m = rrect_mask((w, h), int(radius * scale)) if radius else Image.new("L", (w, h), 255)
    if opacity < 1:
        m = m.point(lambda v: int(v * opacity))
    if shadow:
        sh = Image.new("RGBA", (w + 80, h + 80), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle([40, 50, w + 40, h + 50], int(radius * scale) + 4, fill=(0, 0, 0, int(110 * opacity)))
        sh = sh.filter(ImageFilter.GaussianBlur(22))
        base.paste(sh, (x - 40, y - 40), sh)
    base.paste(im, (x, y), m)


def grade(img, sat=1.0, contrast=1.0, bright=0.0, bw=False):
    a = np.asarray(img).astype(np.float32)
    if bw:
        g = a @ np.array([.299, .587, .114], np.float32)
        a = np.repeat(g[..., None], 3, axis=2)
    else:
        g = a.mean(axis=2, keepdims=True)
        a = g + (a - g) * sat
    a = (a - 128) * contrast + 128 + bright
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def composite_behind(fg_frame, layer_rgba, mask):
    """Put an RGBA layer between the background and the person (mask: HxW float 0..1)."""
    base = fg_frame.copy()
    base.paste(layer_rgba, (0, 0), layer_rgba)
    a = np.asarray(base).astype(np.float32)
    f = np.asarray(fg_frame).astype(np.float32)
    m = mask[..., None]
    return Image.fromarray((f * m + a * (1 - m)).astype(np.uint8))


def head_from_mask(mask):
    """(cx, top_y, head_w) of the person, read from the segmentation mask."""
    rows = np.where(mask.max(axis=1) > 0.5)[0]
    if len(rows) == 0:
        return (W // 2, int(H * .2), 260)
    top = int(rows[0])
    band = mask[top + 60: top + 260] > 0.5
    cols = np.where(band.any(axis=0))[0]
    if len(cols) == 0:
        return (W // 2, top, 260)
    return (int(cols.mean()), top, int(cols[-1] - cols[0]))


def spark(draw, cx, cy, r, fill=CLAY, rays=12):
    """Claude-style spark (asterisk of tapered rays) — no font glyph needed."""
    for i in range(rays):
        a = math.pi * 2 * i / rays
        rr = r * (1.0 if i % 2 == 0 else 0.78)
        ex, ey = cx + math.cos(a) * rr, cy + math.sin(a) * rr
        px, py = -math.sin(a) * r * 0.13, math.cos(a) * r * 0.13
        draw.polygon([(cx + px, cy + py), (ex, ey), (cx - px, cy - py)], fill=fill)
    draw.ellipse((cx - r * .22, cy - r * .22, cx + r * .22, cy + r * .22), fill=fill)


def tw(s, f):
    """Text width in px."""
    return f.getlength(s)
