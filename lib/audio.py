"""Royalty-free music bed + UI sound effects, synthesized from scratch (no samples, no licences)."""
import subprocess, wave
import numpy as np
from scipy.signal import lfilter, butter

SR = 44100


def _t(d):
    return np.arange(int(d * SR)) / SR


def _lp(x, fc):
    b, a = butter(2, min(fc, SR / 2 - 100) / (SR / 2), "low")
    return lfilter(b, a, x)


def _hp(x, fc):
    b, a = butter(2, fc / (SR / 2), "high")
    return lfilter(b, a, x)


def _bp(x, lo, hi):
    b, a = butter(2, [lo / (SR / 2), hi / (SR / 2)], "band")
    return lfilter(b, a, x)


def note(n):          # midi -> Hz
    return 440.0 * 2 ** ((n - 69) / 12)


rng = np.random.default_rng(7)


# ------------------------------------------------------------------ SFX
def sfx_key():
    t = _t(0.035)
    n = rng.normal(0, 1, len(t)) * np.exp(-t * 260)
    n = _bp(n, 1800, 6500)
    thump = np.sin(2 * np.pi * rng.uniform(170, 230) * t) * np.exp(-t * 120) * 0.5
    return (n * 0.9 + thump) * 0.30


def sfx_pop():
    t = _t(0.12)
    f = 380 + 600 * np.exp(-t * 45)
    ph = np.cumsum(2 * np.pi * f / SR)
    return np.sin(ph) * np.exp(-t * 30) * 0.45


def sfx_tick():
    t = _t(0.06)
    return (np.sin(2 * np.pi * 2100 * t) * 0.6 + np.sin(2 * np.pi * 3150 * t) * 0.3) * np.exp(-t * 70) * 0.35


def sfx_click():
    t = _t(0.05)
    n = _bp(rng.normal(0, 1, len(t)), 2000, 8000) * np.exp(-t * 300)
    return (n + np.sin(2 * np.pi * 900 * t) * np.exp(-t * 200) * 0.6) * 0.5


def sfx_send():
    t = _t(0.25)
    f = 500 + 900 * (t / t[-1]) ** 0.6
    ph = np.cumsum(2 * np.pi * f / SR)
    return np.sin(ph) * np.exp(-t * 14) * 0.32 + sfx_pad(sfx_pop(), len(t)) * 0.6


def sfx_pad(x, n):
    y = np.zeros(n); y[:min(n, len(x))] = x[:n]; return y


def sfx_whoosh(d=0.55, up=True):
    t = _t(d)
    n = rng.normal(0, 1, len(t))
    env = np.sin(np.pi * (t / d)) ** 2
    out = np.zeros_like(n)
    # sweep a band-pass in 8 slices
    k = 8
    for i in range(k):
        sl = slice(i * len(t) // k, (i + 1) * len(t) // k + 1)
        fc = (400 + 4200 * (i / k)) if up else (4600 - 4200 * (i / k))
        out[sl] = _bp(n, fc * 0.6, fc * 1.4)[sl]
    return out * env * 0.55


def sfx_swoosh():
    return sfx_whoosh(0.32)


def sfx_sparkle():
    d = 0.7
    out = np.zeros(int(d * SR))
    for i in range(14):
        st = rng.uniform(0, d - 0.12)
        f = rng.choice([note(n) for n in (88, 91, 93, 96, 98, 100)])
        t = _t(0.12)
        s = np.sin(2 * np.pi * f * t) * np.exp(-t * 40) * rng.uniform(.06, .14)
        i0 = int(st * SR); out[i0:i0 + len(s)] += s
    return out


def sfx_chime():
    t = _t(1.0)
    s = sum(np.sin(2 * np.pi * note(n) * t) * a for n, a in ((84, .5), (88, .35), (91, .3), (96, .15)))
    return s * np.exp(-t * 4.5) * 0.28


def sfx_buzz():
    t = _t(0.12)
    sq = np.sign(np.sin(2 * np.pi * 120 * t)) * 0.4 + rng.normal(0, .5, len(t))
    return _lp(sq, 3000) * np.exp(-t * 18) * 0.28


def sfx_neon():
    t = _t(1.2)
    h = np.sin(2 * np.pi * 120 * t) * 0.5 + np.sin(2 * np.pi * 240 * t) * 0.25
    return h * np.minimum(1, t * 20) * np.exp(-t * 1.8) * 0.12 + sfx_pad(sfx_chime(), len(t)) * 0.5


def sfx_riser(d=1.2):
    t = _t(d)
    n = _hp(rng.normal(0, 1, len(t)), 1500)
    f = 300 + 900 * (t / d) ** 2
    tone = np.sin(np.cumsum(2 * np.pi * f / SR)) * 0.25
    return (n * 0.25 + tone) * (t / d) ** 2 * 0.6


def sfx_impact():
    t = _t(1.4)
    f = 45 + 120 * np.exp(-t * 18)
    body = np.sin(np.cumsum(2 * np.pi * f / SR)) * np.exp(-t * 3.2)
    return body * 0.7 + sfx_pad(sfx_chime(), len(t)) * 0.8


SFX = {"key": sfx_key, "pop": sfx_pop, "tick": sfx_tick, "click": sfx_click, "send": sfx_send,
       "whoosh": sfx_whoosh, "swoosh": sfx_swoosh, "sparkle": sfx_sparkle, "chime": sfx_chime,
       "buzz": sfx_buzz, "neon": sfx_neon, "riser": sfx_riser, "impact": sfx_impact}


# ------------------------------------------------------------------ music
def music(duration, bpm=137.14, sections=None, seed=1):
    """Upbeat lo-fi/pop bed. `sections`: list of (start, end, intensity 0..1)."""
    r = np.random.default_rng(seed)
    beat = 60 / bpm
    n = int(duration * SR)
    L = np.zeros(n); R = np.zeros(n)

    def add(sig, st, pan=0.0, g=1.0):
        i0 = int(st * SR)
        if i0 >= n or i0 < 0:
            return
        s = sig[: n - i0] * g
        L[i0:i0 + len(s)] += s * (1 - pan) ** .5
        R[i0:i0 + len(s)] += s * (1 + pan) ** .5

    def inten(t):
        if not sections:
            return 1
        for a, b, v in sections:
            if a <= t < b:
                return v
        return 0

    t = _t(0.35)
    kick = np.sin(np.cumsum(2 * np.pi * (48 + 110 * np.exp(-t * 30)) / SR)) * np.exp(-t * 9)
    th = _t(0.05)
    hat = _hp(r.normal(0, 1, len(th)), 7000) * np.exp(-th * 90) * 0.18
    tc = _t(0.2)
    clap = _bp(r.normal(0, 1, len(tc)), 900, 3500) * (np.exp(-tc * 25) + 0.5 * np.exp(-((tc - .012) * 400) ** 2)) * 0.35

    prog = [(57, [69, 72, 76]), (53, [65, 69, 72]), (48, [64, 67, 72]), (55, [67, 71, 74])]  # Am F C G
    nb = int(duration / beat) + 1
    duck = np.ones(n)
    for b in range(nb):
        tb = b * beat
        I = inten(tb)
        if I <= 0:
            continue
        root, chord = prog[(b // 4) % 4]
        if I >= 0.6:
            add(kick, tb, g=0.95)
            i0 = int(tb * SR); dl = int(0.18 * SR)
            duck[i0:i0 + dl] = np.minimum(duck[i0:i0 + dl], 0.45 + 0.55 * np.linspace(0, 1, len(duck[i0:i0 + dl])))
            if b % 2 == 1:
                add(clap, tb, g=0.9)
        for h in range(2):
            add(hat, tb + h * beat / 2 + (beat / 2 if h == 0 else 0) * 0, pan=0.3 * (1 if h else -1), g=0.7 * max(I, .4))
        # bass on 8ths
        for h in range(2):
            tt = _t(beat / 2)
            bs = np.sin(2 * np.pi * note(root - 12) * tt) + 0.3 * np.sin(2 * np.pi * note(root) * tt)
            add(bs * np.minimum(1, tt * 200) * np.exp(-tt * 4) * 0.30 * I, tb + h * beat / 2)
        # pluck arp on 8ths
        for h in range(2):
            k = (b * 2 + h)
            nn = chord[k % 3] + (12 if (k // 3) % 2 else 0)
            tt = _t(0.45)
            pl = (np.sin(2 * np.pi * note(nn) * tt) + 0.35 * np.sin(2 * np.pi * 2 * note(nn) * tt)) * np.exp(-tt * 9)
            add(pl * 0.10 * max(I, .5), tb + h * beat / 2, pan=0.35 * (1 if k % 2 else -1))
        # pad, once per bar
        if b % 4 == 0:
            tt = _t(beat * 4 + 0.3)
            pad = np.zeros(len(tt))
            for nn in chord:
                for det in (-0.08, 0.08):
                    f = note(nn - 12) * 2 ** (det / 12)
                    pad += 2 * ((tt * f) % 1) - 1
            pad = _lp(pad, 1400) * np.minimum(1, tt * 6) * np.minimum(1, (tt[-1] - tt) * 6) * 0.035
            add(pad, tb)
    L *= duck; R *= duck
    return np.stack([L, R], 1)


def build(duration, events, sections, out_wav, bpm=137.14):
    """events: list of (time, name, gain). Writes a 44.1k stereo wav, loudness-normalised."""
    mix = music(duration, bpm, sections) * 0.55
    for t, name, g in events:
        s = SFX[name]()
        i0 = int(t * SR)
        if i0 >= len(mix):
            continue
        s = s[: len(mix) - i0] * g
        pan = rng.uniform(-.2, .2)
        mix[i0:i0 + len(s), 0] += s * (1 - pan)
        mix[i0:i0 + len(s), 1] += s * (1 + pan)
    # fade out tail
    fo = int(0.6 * SR)
    mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    mix /= max(1e-6, np.abs(mix).max()) / 0.9
    raw = out_wav + ".raw.wav"
    with wave.open(raw, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())
    subprocess.check_call(["ffmpeg", "-y", "-v", "error", "-i", raw, "-af", "loudnorm=I=-14:TP=-1.0:LRA=11",
                           "-ar", "44100", out_wav])
    return out_wav
