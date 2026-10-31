#!/usr/bin/env python3
"""Apply one effect to a whole clip.

    python3 run.py <effect> <video> [-o out.mp4] [--start 0] [--preview 1.5,3,6] [--no-voice] [--music]

  --preview   only render PNG stills at these times (approve them before the full render)
  --no-voice  drop the clip's own audio
  --music     add the synthesized music bed (+ the effect's UI sounds)
"""
import argparse, os, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.core import *
from lib.ctx import Ctx
from lib import audio
from effects import ORDER, load


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("effect", help="one of: " + ", ".join(ORDER) + " | list")
    ap.add_argument("video", nargs="?")
    ap.add_argument("-o", "--out")
    ap.add_argument("--start", type=float, default=0.0, help="effect starts at this second of the clip")
    ap.add_argument("--preview")
    ap.add_argument("--no-voice", action="store_true")
    ap.add_argument("--music", action="store_true")
    ap.add_argument("--name"); ap.add_argument("--handle")
    a = ap.parse_args()
    if a.effect == "list":
        for n in ORDER:
            print(f"{n:15s} {load(n).DESC}")
        return
    m = load(a.effect)
    cfg = {k: v for k, v in (("name", a.name), ("handle", a.handle)) if v}
    ctx = Ctx(a.video, cfg)
    base = os.path.splitext(a.out or a.video)[0]
    if a.preview:
        for t in [float(x) for x in a.preview.split(",")]:
            p = f"{base}.{m.NAME}.{t:.1f}s.png"
            m.render(ctx, t - a.start, t).save(p)
            print(p)
        return
    out = a.out or f"{base}.{m.NAME}.mp4"
    tmp = out + ".video.mp4"
    wr = Writer(tmp)
    N = int(ctx.clip.duration * FPS)
    for i in range(N):
        t = i / FPS
        wr.write(m.render(ctx, t - a.start, t) if t >= a.start else ctx.clip.frame(t))
        if i % 60 == 0:
            print(f"frame {i}/{N}", flush=True)
    wr.close()
    inputs, maps, filt = ["-i", tmp], ["-map", "0:v"], None
    if a.music:
        ev = [(a.start + t, s, 0.8) for t, s in m.SFX]
        wav = audio.build(N / FPS, ev, [(0, 999, 1.0)], out + ".wav")
        inputs += ["-i", wav]
    if not a.no_voice:
        inputs += ["-ss", str(ctx.clip.offset / FPS), "-i", a.video]
    if a.music and not a.no_voice:
        filt = "[1:a]volume=0.25[m];[2:a][m]amix=inputs=2:duration=first[a]"; maps += ["-map", "[a]"]
    elif a.music:
        maps += ["-map", "1:a"]
    elif not a.no_voice:
        maps += ["-map", "1:a?"]
    cmd = ["ffmpeg", "-y", "-v", "error", *inputs] + (["-filter_complex", filt] if filt else []) + \
          [*maps, "-c:v", "copy", "-c:a", "aac", "-b:a", "320k", "-shortest", "-movflags", "+faststart", out]
    subprocess.check_call(cmd)
    os.remove(tmp)
    print("done:", out)


if __name__ == "__main__":
    main()
