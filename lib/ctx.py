"""Render context passed to every effect."""
import json, os
import numpy as np
import cv2
from PIL import Image
from .core import Clip, W, H, ROOT
from .segment import MaskTrack

DEFAULT_CFG = {
    "name": "Мария Дурманова",
    "handle": "@maria.aiart",
    "series": "AI-СЕРИЯ ДЛЯ НЕТЕХНАРЕЙ · КАЖДЫЙ ДЕНЬ",
    "lang": "ru",
}


class Ctx:
    def __init__(self, video, cfg=None, need_mask=True):
        self.clip = Clip(video)
        self.cfg = dict(DEFAULT_CFG)
        p = os.path.join(ROOT, "config.json")
        if os.path.exists(p):
            self.cfg.update(json.load(open(p, encoding="utf-8")))
        if cfg:
            self.cfg.update(cfg)
        self.masks = MaskTrack(video) if need_mask else None
        self.thumbs = []          # stills of other effects (orbit cards, end grid)
        self.anchor = (W // 2, 600)

    def src(self, ts, zoom=1.0, anchor=None, with_mask=True):
        """Frame (and person mask) at source time ts, digitally zoomed around anchor."""
        ax, ay = anchor or self.anchor
        f = self.clip.frame(ts)
        m = self.masks.at(ts, (W, H)) if (with_mask and self.masks) else None
        if zoom != 1.0:
            cw, ch = W / zoom, H / zoom
            x0, y0 = ax - ax / zoom, ay - ay / zoom
            box = (x0, y0, x0 + cw, y0 + ch)
            f = f.resize((W, H), Image.LANCZOS, box=box)
            if m is not None:
                M = np.float32([[zoom, 0, -x0 * zoom], [0, zoom, -y0 * zoom]])
                m = cv2.warpAffine(m, M, (W, H), flags=cv2.INTER_LINEAR)
        return f, m

    def crop(self, ts, box, size):
        """Arbitrary crop of the source frame resized to `size` (+ mask)."""
        f = self.clip.frame(ts)
        img = f.resize(size, Image.LANCZOS, box=box)
        m = None
        if self.masks:
            mm = self.masks.at(ts, (W, H))
            x0, y0, x1, y1 = [int(v) for v in box]
            m = cv2.resize(mm[max(0, y0):y1, max(0, x0):x1], size)
        return img, m
