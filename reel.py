#!/usr/bin/env python3
"""Showcase reel: "one clip → 7 edits", each typed as /effects <name> in a Claude-style chat.

    python3 reel.py my_clip.mp4 -o reel.mp4 [--name "Имя Фамилия" --handle @me]

No voice: the clip's audio is dropped; a synthesized music bed + UI sounds are added.
"""
import argparse, os, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw
from lib.core import *
from lib.ctx import Ctx
from lib import ui, audio
from effects import ORDER, load

SEG = 3.5                    # one effect = 8 beats at 137 bpm
END = 4.0
BPM = 137.14
# segment timeline (seconds inside a segment)
T_TYPE0, T_TYPE1, T_SEND = 0.12, 0.70, 0.78
T_CHAT, T_DIS0, T_DIS1 = 0.80, 0.95, 1.45
T_Z0, T_Z1 = 1.50, 1.85
T_EFF = 0.95                 # effect clock starts here


def typed(cmd, t):
    n = int(len(cmd) * clamp((t - T_TYPE0) / (T_TYPE1 - T_TYPE0)))
    return cmd[:n], (cmd[n - 1] if 0 < n <= len(cmd) and t < T_TYPE1 + 0.05 else None)


def popup_for(s, mods):
    if not s.startswith("/"):
        return None
    if " " not in s:
        return [("/effects", f"{len(mods)} видеоэффектов для твоего клипа")]
    part = s.split(" ", 1)[1]
    hits = [m for m in mods if m.NAME.startswith(part)]
    if part and hits:
        return [(hits[0].NAME, hits[0].DESC)]
    return [("/effects", f"{len(mods)} видеоэффектов для твоего клипа")]


def cta_poster(ctx, thumbs, t, mods, word="claude"):
    img = Image.new("RGB", (W, H), (30, 30, 28))
    d = ImageDraw.Draw(img)
    q = ease_back(prog(t, 0.0, 0.4))
    d.text((W // 2, 230 - 30 * (1 - q)), f"Напиши «{word}»", font=font("oswald", int(min(130, 130 * 960 / tw(f"Напиши «{word}»", font("oswald", 130, 700)))), 700), fill=(255, 255, 255), anchor="mm")
    f = font("sans", 38, 700)
    s = f"и получи все {len(mods)} эффектов"
    pw = tw(s, f) + 70
    d.rounded_rectangle((W / 2 - pw / 2, 330, W / 2 + pw / 2, 410), 18, fill=CLAY)
    d.text((W // 2, 370), s, font=f, fill=(255, 255, 255), anchor="mm")
    cols, gap, x0 = 4, 20, 50
    tw_ = (W - 2 * x0 - (cols - 1) * gap) // cols
    th_ = int(tw_ * 16 / 9)
    for i, (lab, im) in enumerate(thumbs):
        r, c = divmod(i, cols)
        x, y = x0 + c * (tw_ + gap), 470 + r * (th_ + 70)
        p = ease_back(prog(t, 0.1 + i * 0.07, 0.35), 2)
        if p <= 0:
            continue
        paste_scaled(img, im.resize((tw_, th_), Image.LANCZOS), (x + tw_ / 2, y + th_ / 2), p, radius=16)
        if p > 0.8:
            d.text((x + tw_ / 2, y + th_ + 30), lab, font=font("mono", 22, 600), fill=UI_DIM, anchor="mm")
    q = ease_out(prog(t, 1.0, 0.4))
    if q > 0:
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        od.text((W // 2, 1640), "/effects + твоё видео = готовый рилс", font=font("sans", 36, 600), fill=(255, 255, 255, int(255 * q)), anchor="mm")
        od.text((W // 2, 1710), ctx.cfg["handle"], font=font("sans", 34, 500), fill=CLAY + (int(255 * q),), anchor="mm")
        img = img.convert("RGBA"); img.alpha_composite(ov); img = img.convert("RGB")
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("-o", "--out", default="reel.mp4")
    ap.add_argument("--name"); ap.add_argument("--handle")
    ap.add_argument("--effects", default=",".join(ORDER))
    ap.add_argument("--preview", type=float, default=None, help="render one frame at time t to PNG")
    ap.add_argument("--word", default="claude", help="code word for the final call-to-action")
    ap.add_argument("--music-file", help="your own track instead of the synthesized bed")
    ap.add_argument("--music-start", type=float, default=0.0, help="start the track from this second")
    ap.add_argument("--sfx-gain", type=float, default=1.0, help="volume of UI sounds relative to music")
    ap.add_argument("--reuse", help="previous render: keep its picture before the final CTA, re-render only the end")
    a = ap.parse_args()
    cfg = {k: v for k, v in (("name", a.name), ("handle", a.handle)) if v}
    ctx = Ctx(a.video, cfg)
    mods = [load(n) for n in a.effects.split(",")]
    n = len(mods)
    total = n * SEG + END
    span = ctx.clip.duration - 0.1
    def src_t(t):                      # map reel time → clip time (whole clip spread over the effects)
        return clamp(t * span / (n * SEG), 0, span)

    # stills of every effect: orbit cards + end grid
    print("stills…")
    stills = []
    for i, m in enumerate(mods):
        stills.append((m.NAME, m.render(ctx, 1.9 + getattr(m, "REEL_DELAY", 0) * 0, src_t((i + 0.6) * SEG))))
    ctx.thumbs = [im for _, im in stills]
    grid = [("/" + lab, im) for lab, im in stills] + [("исходник", ctx.clip.frame(src_t(5)))]
    thumb_src = ctx.clip.frame(src_t(2))

    def frame_at(t):
        k = int(t // SEG)
        if k < n:
            m = mods[k]; ts_ = t - k * SEG; ts = src_t(t)
            cmd = "/effects " + m.NAME
            tl = ts_ - T_EFF - getattr(m, "REEL_DELAY", 0)
            if ts_ < T_CHAT:
                s, key = typed(cmd, ts_)
                return ui.compose(s, thumb_src, popup_for(s, mods), key)
            eff = m.render(ctx, tl, ts)
            if ts_ < T_Z0:
                return ui.chat(cmd, thumb_src, f"Монтирую: {m.NAME}…", eff, ease_in_out(prog(ts_, T_DIS0, T_DIS1 - T_DIS0)),
                               show_card=ts_ >= T_DIS0 - 0.05)
            if ts_ < T_Z1:
                return ui.chat(cmd, thumb_src, f"Монтирую: {m.NAME}…", eff, 1, zoom=prog(ts_, T_Z0, T_Z1 - T_Z0))
            return eff
        te = t - n * SEG
        word = a.word
        if te < 0.70:
            s = word[: int(len(word) * clamp((te - 0.1) / 0.45))]
            key = s[-1] if s and te < 0.6 else None
            return ui.compose(s, None, None, key, ru=any("а" <= ch.lower() <= "я" for ch in word))
        reply_full = [f"Напиши «{word}» в комментариях —", f"пришлю все {n} эффектов"]
        rp = clamp((te - 0.75) / 0.55)
        chars = int(sum(len(x) for x in reply_full) * rp)
        rep, c = [], chars
        for ln in reply_full:
            rep.append(ln[:max(0, c)]); c -= len(ln)
        poster = cta_poster(ctx, grid, te - 1.95, mods, word)
        if te < 1.65:
            return ui.chat(word, None, None, poster, ease_in_out(prog(te, 1.2, 0.45)), reply=rep,
                           show_card=te >= 1.2)
        if te < 1.95:
            return ui.chat(word, None, None, poster, 1, zoom=prog(te, 1.65, 0.3), reply=rep)
        return poster

    if a.preview is not None:
        frame_at(a.preview).save(a.out); return

    # ---------------- sound design
    ev = []
    for k, m in enumerate(mods):
        t0 = k * SEG
        cmd = "/effects " + m.NAME
        for i in range(len(cmd)):
            ev.append((t0 + T_TYPE0 + (T_TYPE1 - T_TYPE0) * (i + 1) / len(cmd), "key", 0.5))
        ev += [(t0 + T_SEND, "send", 0.8), (t0 + T_DIS0, "sparkle", 1.0), (t0 + T_Z0 - 0.05, "whoosh", 0.9)]
        d0 = t0 + T_EFF + getattr(m, "REEL_DELAY", 0)
        for st, name in m.SFX:
            if d0 + st < t0 + SEG - 0.05:
                ev.append((d0 + st, name, 0.8))
    te0 = n * SEG
    for i in range(len(a.word)):
        ev.append((te0 + 0.1 + 0.45 * (i + 1) / len(a.word), "key", 0.5))
    ev += [(te0 + 0.65, "send", 0.8), (te0 + 1.2, "sparkle", 1), (te0 + 0.75, "riser", 0.9),
           (te0 + 1.95, "impact", 1.0)]
    for i in range(len(grid)):
        ev.append((te0 + 1.95 + 0.1 + i * 0.07, "pop", 0.6))
    sections = [(0, n * SEG, 1.0), (n * SEG, n * SEG + 1.95, 0.35), (n * SEG + 1.95, total + 1, 1.0)]
    wav = a.out + ".wav"
    ev = [(t, nm, g * a.sfx_gain) for t, nm, g in ev]
    audio.build(total, ev, sections, wav, BPM, music_file=a.music_file, music_start=a.music_start)

    # ---------------- picture
    tmp = a.out + ".video.mp4"
    wr = Writer(tmp, crf=14)
    N = int(round(total * FPS))
    first = 0
    if a.reuse:
        first = int(round(n * SEG * FPS))
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", a.reuse, "-frames:v", str(first), "-f", "rawvideo",
                              "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        for _ in range(first):
            wr.p.stdin.write(p.stdout.read(W * H * 3))
        p.wait()
    for i in range(first, N):
        wr.write(frame_at(i / FPS))
        if i % 60 == 0:
            print(f"frame {i}/{N}", flush=True)
    wr.close()
    subprocess.check_call(["ffmpeg", "-y", "-v", "error", "-i", tmp, "-i", wav, "-map", "0:v", "-map", "1:a",
                           "-c:v", "copy", "-c:a", "aac", "-b:a", "320k", "-shortest", "-movflags", "+faststart", a.out])
    os.remove(tmp)
    print("done:", a.out)


if __name__ == "__main__":
    main()
